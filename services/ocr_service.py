"""
OCR 服务模块 - Mathpix API 版本

提供统一接口：extract_text(image_path: str, manual_text: Optional[str] = None) -> str

支持的 provider（通过环境变量 OCR_MODE 控制）：
- mathpix: 使用 Mathpix API（默认）
- manual: 手动输入模式（用于测试/无 Key 场景）

安全要求：
- Mathpix API Key 必须从环境变量读取（MATHPIX_APP_ID, MATHPIX_APP_KEY）
- 绝对禁止在代码中硬编码 Key
"""

import os
import base64
import hashlib
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Mathpix API 配置
MATHPIX_API_URL = "https://api.mathpix.com/v3/text"


def get_ocr_mode() -> str:
    """
    获取当前 OCR 模式配置

    可选值：
    - mathpix: 使用 Mathpix API（默认）
    - manual: 手动输入模式
    """
    return os.environ.get("OCR_MODE", "mathpix").lower()


def _get_mathpix_credentials() -> tuple[str, str]:
    """
    从环境变量读取 Mathpix 认证信息

    Returns:
        (app_id, app_key)

    Raises:
        RuntimeError: 环境变量未设置
    """
    app_id = os.environ.get("MATHPIX_APP_ID", "").strip()
    app_key = os.environ.get("MATHPIX_APP_KEY", "").strip()

    if not app_id or not app_key:
        raise RuntimeError(
            "Mathpix API 凭证未配置！\n"
            "请设置环境变量：\n"
            "  export MATHPIX_APP_ID=your_app_id\n"
            "  export MATHPIX_APP_KEY=your_app_key\n"
            "或使用 manual 模式：\n"
            "  export OCR_MODE=manual"
        )

    logger.info(f"✅ Mathpix 凭证已加载（app_id: {app_id[:8]}...）")
    return app_id, app_key


def _encode_image_to_base64(image_path: str) -> str:
    """
    将图片编码为 base64（data URI 格式）

    Args:
        image_path: 图片文件路径

    Returns:
        data URI 格式的 base64 字符串
    """
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        # 检测图片格式
        if image_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif image_path.lower().endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        else:
            mime_type = "image/jpeg"  # 默认

        base64_data = base64.b64encode(image_data).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{base64_data}"

        logger.info(f"✅ 图片已编码为 base64（{len(base64_data)} 字符）")
        return data_uri

    except Exception as e:
        logger.error(f"❌ 图片编码失败: {e}")
        raise


def _mathpix_ocr_extract(image_path: str) -> str:
    """
    使用 Mathpix API 提取文本

    Args:
        image_path: 图片文件路径

    Returns:
        提取的文本（优先返回 Markdown，其次 LaTeX，最后纯文本）

    Raises:
        RuntimeError: API 调用失败
    """
    app_id, app_key = _get_mathpix_credentials()

    # 1. 编码图片为 base64
    logger.info(f"开始 Mathpix OCR 识别: {image_path}")
    image_data_uri = _encode_image_to_base64(image_path)

    # 2. 构建请求
    headers = {
        "app_id": app_id,
        "app_key": app_key,
        "Content-Type": "application/json"
    }

    payload = {
        "src": image_data_uri,
        "formats": ["text", "latex_styled", "html"],  # 支持多种格式
        "ocr": ["math", "text"]  # 同时识别数学公式和文本
    }

    # 3. 调用 Mathpix API
    try:
        logger.info("正在调用 Mathpix API...")
        response = requests.post(
            MATHPIX_API_URL,
            json=payload,
            headers=headers,
            timeout=30  # 30 秒超时
        )

        # 检查 HTTP 状态码
        if response.status_code != 200:
            error_msg = f"Mathpix API 返回错误状态码: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f"\n详情: {error_detail}"
            except:
                error_msg += f"\n响应: {response.text[:200]}"

            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        result = response.json()
        logger.info(f"✅ Mathpix API 调用成功")

    except requests.exceptions.Timeout:
        logger.error("❌ Mathpix API 请求超时（30秒）")
        raise RuntimeError("Mathpix API 请求超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Mathpix API 请求失败: {e}")
        raise RuntimeError(f"Mathpix API 请求失败: {e}")
    except Exception as e:
        logger.error(f"❌ 未知错误: {e}")
        raise RuntimeError(f"Mathpix OCR 失败: {e}")

    # 4. 提取文本（优先级：html/markdown > latex > text）
    extracted_text = ""

    # 优先使用 HTML/Markdown（包含结构化信息）
    if "html" in result:
        extracted_text = result["html"]
        logger.info("使用 HTML 格式")
    elif "text" in result:
        extracted_text = result["text"]
        logger.info("使用纯文本格式")
    elif "latex_styled" in result:
        extracted_text = result["latex_styled"]
        logger.info("使用 LaTeX 格式")

    # 如果还是空，尝试其他字段
    if not extracted_text and "data" in result:
        extracted_text = result.get("data", "")

    if not extracted_text:
        logger.warning(f"⚠️  Mathpix 未识别到文本，原始响应: {result}")
        return ""

    extracted_text = extracted_text.strip()
    logger.info(f"✅ Mathpix 识别完成（{len(extracted_text)} 字符）")
    logger.debug(f"识别结果: {extracted_text[:200]}...")

    return extracted_text


def _generate_deterministic_text(image_path: str, manual_text: Optional[str] = None) -> str:
    """
    生成确定性的测试文本（manual 模式）

    基于图片路径/manual_text 生成 hash，确保：
    1. 不同输入产生不同输出
    2. 相同输入产生相同输出
    3. 输出包含物理题特征（便于下游解析）

    Args:
        image_path: 图片路径
        manual_text: 手动输入文本（优先使用）

    Returns:
        确定性的测试文本
    """
    # 1. 如果提供了 manual_text，优先使用
    if manual_text and manual_text.strip():
        logger.info(f"✅ [Manual Mode] 使用手动输入的文本（{len(manual_text)} 字符）")
        return manual_text.strip()

    # 2. 根据图片路径生成 hash 值（确保不同图片产生不同文本）
    hash_input = f"{image_path}_{os.path.getmtime(image_path)}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()

    # 3. 使用 hash 生成确定性参数
    # 取 hash 的不同位置作为参数种子
    height_seed = int(hash_value[0:2], 16) % 20 + 5    # 5-24 米
    speed_seed = int(hash_value[2:4], 16) % 20 + 10   # 10-29 m/s
    angle_seed = int(hash_value[4:6], 16) % 90        # 0-89 度
    gravity_seed = int(hash_value[6:8], 16) % 2       # 0 或 1 (决定用 9.8 还是 10)

    height = height_seed
    speed = speed_seed
    angle = angle_seed
    gravity = 9.8 if gravity_seed == 0 else 10

    # 4. 根据角度决定运动类型
    if angle < 10:
        # 平抛运动
        motion_type = "平抛运动"
        text = f"""
一物体从 {height} 米高处以 {speed} m/s 的初速度水平抛出，
不计空气阻力，重力加速度 g = {gravity} m/s²。
求：
(1) 物体落地时的水平位移
(2) 物体落地时的速度大小
(3) 物体的运动轨迹方程
        """.strip()
    elif angle > 80:
        # 竖直上抛
        motion_type = "竖直上抛运动"
        text = f"""
一物体以 {speed} m/s 的初速度竖直向上抛出，
不计空气阻力，重力加速度 g = {gravity} m/s²。
求：
(1) 物体能达到的最大高度
(2) 物体回到抛出点的时间
(3) 物体落地时的速度
        """.strip()
    else:
        # 斜抛运动
        motion_type = "斜抛运动"
        text = f"""
一物体以 {speed} m/s 的初速度与水平方向成 {angle}° 角斜向上抛出，
抛出点距地面 {height} 米，不计空气阻力，重力加速度 g = {gravity} m/s²。
求：
(1) 物体的最大高度
(2) 物体的水平射程
(3) 物体落地时的速度大小和方向
        """.strip()

    logger.info(f"✅ [Manual Mode] 生成确定性文本: {motion_type}")
    logger.info(f"   参数: h={height}m, v={speed}m/s, θ={angle}°, g={gravity}m/s²")
    logger.debug(f"   文本: {text[:100]}...")

    return text


def extract_text(image_path: str, manual_text: Optional[str] = None) -> str:
    """
    统一 OCR 接口：从图片中提取文本

    Args:
        image_path: 图片文件路径
        manual_text: 手动输入的文本（manual 模式专用）

    Returns:
        提取的文本字符串

    环境变量：
        OCR_MODE: mathpix/manual（默认 mathpix）
        MATHPIX_APP_ID: Mathpix 应用 ID（mathpix 模式必需）
        MATHPIX_APP_KEY: Mathpix 应用密钥（mathpix 模式必需）

    Raises:
        RuntimeError: OCR 初始化或识别失败
        FileNotFoundError: 图片文件不存在（mathpix 模式）
    """
    mode = get_ocr_mode()

    logger.info(f"OCR 模式: {mode}")

    if mode == "mathpix":
        # Mathpix 模式：调用 Mathpix API
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        return _mathpix_ocr_extract(image_path)

    elif mode == "manual":
        # Manual 模式：生成确定性测试文本
        return _generate_deterministic_text(image_path, manual_text)

    else:
        raise ValueError(
            f"不支持的 OCR_MODE: {mode}\n"
            f"可选值: mathpix, manual"
        )


def get_ocr_status() -> dict:
    """
    获取 OCR 状态信息（健康检查）

    Returns:
        {
            "mode": "mathpix/manual",
            "mathpix_configured": bool,
            "error": Optional[str]
        }
    """
    mode = get_ocr_mode()

    status = {
        "mode": mode,
        "mathpix_configured": False,
        "error": None
    }

    # 检查 Mathpix 配置
    if mode == "mathpix":
        try:
            _get_mathpix_credentials()
            status["mathpix_configured"] = True
        except Exception as e:
            status["error"] = str(e)
            status["mathpix_configured"] = False

    return status


# 向后兼容的别名
def ocr_extract_text(image_path: str) -> str:
    """向后兼容接口（不推荐使用）"""
    return extract_text(image_path)