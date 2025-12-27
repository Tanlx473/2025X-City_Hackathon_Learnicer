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

    # Python 3.13 + PaddleOCR 某些环境下的 modelscope 兼容性 workaround
    #（不一定每台机器都需要，但加上很安全）
    HUB_DATASET_ENDPOINT = os.environ.get("HUB_DATASET_ENDPOINT", "https://modelscope.cn/api/v1/datasets")
