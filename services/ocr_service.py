from paddleocr import PaddleOCR

# 建议全局单例，避免每次请求都重新加载模型
_ocr = None

def get_ocr():
    global _ocr
    if _ocr is None:
        # lang='ch' 支持中英混合题目；如只英文可改 'en'
        _ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    return _ocr

def ocr_extract_text(image_path: str) -> str:
    """
    返回 OCR 识别出的多行文本，用换行拼接。
    """
    ocr = get_ocr()
    result = ocr.ocr(image_path, cls=True)

    if not result:
        return ""

    lines = []
    for line in result:
        # line: [ [box], (text, score) ]
        try:
            lines.append(line[1][0])
        except Exception:
            continue

    return "\n".join(lines).strip()
