import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

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

    # Claude API 配置（用于物理题解析与动画指令生成）
    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
    CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    CLAUDE_MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "2048"))

    # 是否启用 LLM（如果未配置 API key，将使用规则引擎降级）
    ENABLE_LLM = bool(CLAUDE_API_KEY)

    # Python 3.13 + PaddleOCR 某些环境下的 modelscope 兼容性 workaround
    #（不一定每台机器都需要，但加上很安全）
    HUB_DATASET_ENDPOINT = os.environ.get("HUB_DATASET_ENDPOINT", "https://modelscope.cn/api/v1/datasets")
