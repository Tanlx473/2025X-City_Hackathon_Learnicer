from flask import current_app
from paddleocr import PaddleOCR

# 全局单例 OCR 引擎，避免重复加载模型开销
_ocr = None


def get_ocr():
    """
    按配置的语言加载 PaddleOCR。
    放在函数里懒加载，确保应用启动即能复用同一实例。
    """
    global _ocr
    if _ocr is None:
        lang = current_app.config.get("OCR_LANG", "ch")
        _ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    return _ocr


def _safe_extract_line_text(line) -> str:
    """
    从 PaddleOCR 单行结果中提取文字，失败返回空字符串。
    """
    try:
        return line[1][0]
    except Exception:
        return ""


def ocr_extract_text(image_path: str) -> str:
    """
    返回 OCR 识别出的多行文本，用换行拼接。
    """
    ocr = get_ocr()
    # result = ocr.ocr(image_path, cls=True)
    result = ocr.ocr(image_path)

    if not result:
        return ""

    lines = [_safe_extract_line_text(line) for line in result]
    # 过滤空行，保持顺序
    lines = [line for line in lines if line]

    return "\n".join(lines).strip()
