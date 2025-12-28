"""
OCR 服务模块 - 支持多种 provider（paddle/mock/manual）

提供统一接口：extract_text(image_path: str) -> str
支持通过环境变量切换 provider，确保在 PaddleOCR 不可用时也能运行演示
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局单例 OCR 引擎，避免重复加载模型开销
_ocr = None
_ocr_provider = None


def get_ocr_provider() -> str:
    """
    获取当前 OCR provider 配置

    优先级：
    1. 环境变量 OCR_PROVIDER
    2. 默认使用 paddle

    可选值：
    - paddle: 使用 PaddleOCR（需要安装 paddleocr）
    - mock: 返回模拟文本（用于快速测试）
    - manual: 手动输入模式（由调用方通过 manual_text 参数提供文本）
    """
    return os.environ.get("OCR_PROVIDER", "paddle").lower()


def get_ocr():
    """
    按配置的语言加载 PaddleOCR

    使用懒加载 + 全局单例，确保应用启动即能复用同一实例
    如果 PaddleOCR 初始化失败，会抛出异常并建议使用 mock/manual 模式
    """
    global _ocr, _ocr_provider

    provider = get_ocr_provider()

    # 如果 provider 变更，需要重新初始化
    if _ocr_provider != provider:
        _ocr = None
        _ocr_provider = provider

    if _ocr is None:
        if provider == "paddle":
            try:
                from paddleocr import PaddleOCR
                lang = os.environ.get("OCR_LANG", "ch")

                logger.info(f"正在初始化 PaddleOCR（语言: {lang}）...")
                # 使用最基础的配置以兼容不同版本的 PaddleOCR
                _ocr = PaddleOCR(
                    use_angle_cls=True,  # 启用方向分类器（提高倾斜文字识别）
                    lang=lang            # 语言：ch=中英文混合，en=英文
                )
                logger.info("PaddleOCR 初始化成功")
                logger.info(f"PaddleOCR 配置: use_angle_cls=True, lang={lang}")

            except ImportError as e:
                logger.error(f"PaddleOCR 导入失败: {e}")
                raise RuntimeError(
                    "PaddleOCR 未安装或导入失败。\n"
                    "解决方案：\n"
                    "1. 安装 PaddleOCR: pip install paddleocr\n"
                    "2. 或使用 mock 模式: export OCR_PROVIDER=mock\n"
                    "3. 或使用 manual 模式并通过 manual_text 参数提供文本"
                ) from e

            except Exception as e:
                logger.error(f"PaddleOCR 初始化失败: {e}")
                raise RuntimeError(
                    f"PaddleOCR 初始化失败: {e}\n"
                    "解决方案：\n"
                    "1. 检查 PaddlePaddle 是否正确安装\n"
                    "2. 或使用 mock 模式: export OCR_PROVIDER=mock\n"
                    "3. 或使用 manual 模式并通过 manual_text 参数提供文本"
                ) from e

        elif provider == "mock":
            logger.info("使用 Mock OCR（返回模拟文本）")
            _ocr = "mock"  # 标记为 mock 模式

        elif provider == "manual":
            logger.info("使用 Manual OCR（需要通过 manual_text 参数提供文本）")
            _ocr = "manual"  # 标记为 manual 模式

        else:
            raise ValueError(
                f"不支持的 OCR_PROVIDER: {provider}\n"
                f"可选值: paddle, mock, manual"
            )

    return _ocr


def _safe_extract_line_text(line) -> str:
    """
    从 PaddleOCR 单行结果中提取文字，失败返回空字符串

    PaddleOCR 结果格式：
    [
      [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], ('识别文本', 置信度)],
      ...
    ]
    """
    try:
        return line[1][0]
    except (IndexError, TypeError):
        return ""


def _paddle_ocr_extract(image_path: str) -> str:
    """使用 PaddleOCR 提取文本"""
    ocr = get_ocr()

    if ocr == "mock" or ocr == "manual":
        raise ValueError("当前 OCR provider 不是 paddle")

    logger.info(f"开始 OCR 识别: {image_path}")
    result = ocr.ocr(image_path)

    if not result or not result[0]:
        logger.warning(f"PaddleOCR 未识别到文本: {image_path}")
        return ""

    # 修复 bug：PaddleOCR 返回 result[0] 才是行列表
    logger.info(f"OCR 识别到 {len(result[0])} 行文本")

    # 输出每行的识别结果和置信度（用于调试）
    for i, line in enumerate(result[0]):
        try:
            text = line[1][0]
            confidence = line[1][1]
            logger.debug(f"第 {i+1} 行: {text} (置信度: {confidence:.2f})")
        except (IndexError, TypeError):
            logger.warning(f"第 {i+1} 行解析失败")

    lines = [_safe_extract_line_text(line) for line in result[0]]

    # 过滤空行，保持顺序
    lines = [line for line in lines if line.strip()]

    extracted_text = "\n".join(lines).strip()
    logger.info(f"OCR 识别完成，提取了 {len(lines)} 行有效文本")

    return extracted_text


def _mock_ocr_extract(image_path: str) -> str:
    """
    Mock OCR（返回模拟文本）

    用于快速测试，无需真实 OCR 引擎
    """
    logger.info(f"[Mock OCR] 处理图片: {image_path}")

    # 返回一个典型的物理题文本（平抛运动）
    mock_text = """
一小球以 20 m/s 的初速度从地面以 45° 角斜向上抛出，
不计空气阻力，重力加速度 g = 9.8 m/s²。
求：
(1) 小球能达到的最大高度
(2) 小球的水平射程
(3) 小球落地时的速度大小
    """.strip()

    logger.info(f"[Mock OCR] 返回模拟文本（{len(mock_text)} 字符）")
    return mock_text


def extract_text(image_path: str, manual_text: Optional[str] = None) -> str:
    """
    统一 OCR 接口：从图片中提取文本

    Args:
        image_path: 图片文件路径
        manual_text: 手动输入的文本（优先级最高，用于降级）

    Returns:
        提取的文本字符串

    Raises:
        RuntimeError: OCR 初始化或识别失败
        FileNotFoundError: 图片文件不存在

    支持的 provider（通过环境变量 OCR_PROVIDER 控制）：
    - paddle: 使用 PaddleOCR（默认）
    - mock: 返回模拟文本
    - manual: 使用 manual_text 参数（如果未提供则抛出异常）
    """
    provider = get_ocr_provider()

    # 优先使用 manual_text（降级方案）
    if manual_text and manual_text.strip():
        logger.info(f"使用手动输入的文本，跳过 OCR（{len(manual_text)} 字符）")
        return manual_text.strip()

    # 根据 provider 选择 OCR 方法
    if provider == "paddle":
        # PaddleOCR 需要检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        return _paddle_ocr_extract(image_path)

    elif provider == "mock":
        # Mock 模式不需要真实文件
        return _mock_ocr_extract(image_path)

    elif provider == "manual":
        if not manual_text:
            raise ValueError(
                "OCR_PROVIDER=manual 需要通过 manual_text 参数提供文本\n"
                "使用方法：\n"
                "  curl -X POST /upload -F 'file=@test.jpg' -F 'manual_text=题目文本'"
            )
        return manual_text.strip()

    else:
        raise ValueError(f"不支持的 OCR_PROVIDER: {provider}")


# 向后兼容的别名（保持旧代码可用）
def ocr_extract_text(image_path: str) -> str:
    """
    向后兼容接口（不推荐使用，建议使用 extract_text）

    注意：此接口不支持 manual_text 参数
    """
    return extract_text(image_path)


def get_ocr_status() -> dict:
    """
    获取 OCR 状态信息（用于调试和健康检查）

    Returns:
        {
            "provider": "paddle/mock/manual",
            "initialized": bool,
            "lang": "ch/en",
            "error": Optional[str]
        }
    """
    provider = get_ocr_provider()

    status = {
        "provider": provider,
        "initialized": _ocr is not None,
        "lang": os.environ.get("OCR_LANG", "ch"),
        "error": None
    }

    # 尝试初始化以检测潜在错误
    if provider == "paddle" and not _ocr:
        try:
            get_ocr()
            status["initialized"] = True
        except Exception as e:
            status["error"] = str(e)
            status["initialized"] = False

    return status