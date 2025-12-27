import os

class Config:
    DEBUG = True

    # 上传目录
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # 允许的图片后缀
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # 限制上传体积（可按需调整）
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    # PaddleOCR 语言设置（'ch' 支持中英混合，'en' 仅英文）
    OCR_LANG = "ch"

    # LLM 占位配置（未来接入真实接口时使用）
    LLM_API_URL = os.environ.get("LLM_API_URL", "")
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

    # Python 3.13 + PaddleOCR 某些环境下的 modelscope 兼容性 workaround
    #（不一定每台机器都需要，但加上很安全）
    HUB_DATASET_ENDPOINT = os.environ.get("HUB_DATASET_ENDPOINT", "https://modelscope.cn/api/v1/datasets")
