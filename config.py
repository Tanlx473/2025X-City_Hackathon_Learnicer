"""
集中式配置管理模块

所有配置项通过环境变量加载，确保：
1. 不在代码中硬编码任何敏感信息（API Key、密钥等）
2. 支持多种配置来源：系统环境变量、.env 文件
3. 提供清晰的错误提示和配置指引
4. 允许开发者 clone 后无需修改代码即可开始开发
"""

import os
import logging
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
# 优先级：系统环境变量 > .env 文件
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """统一配置类 - 所有配置项的单一来源"""

    # ==================== 应用基础配置 ====================
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")

    # 上传目录
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # 允许的图片后缀
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # 限制上传体积（可按需调整）
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    # ==================== OCR 配置 ====================
    # OCR Provider（paddle/mock/manual）
    OCR_PROVIDER = os.environ.get("OCR_PROVIDER", "paddle").lower()

    # PaddleOCR 语言设置（'ch' 支持中英混合，'en' 仅英文）
    OCR_LANG = os.environ.get("OCR_LANG", "ch")

    # ==================== Claude API 配置 ====================
    # Claude API Key（从环境变量读取，不设默认值）
    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

    # Claude 模型名称
    CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

    # Claude 最大 tokens
    CLAUDE_MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "2048"))

    # 是否启用 LLM（如果未配置 API key，将使用规则引擎降级）
    ENABLE_LLM = bool(CLAUDE_API_KEY)

    # ==================== 兼容性配置 ====================
    # Python 3.13 + PaddleOCR modelscope 兼容性 workaround
    HUB_DATASET_ENDPOINT = os.environ.get(
        "HUB_DATASET_ENDPOINT",
        "https://modelscope.cn/api/v1/datasets"
    )

    @classmethod
    def validate(cls):
        """
        验证配置完整性，提供友好的错误提示

        注意：不会因为缺少 API Key 而崩溃，而是给出清晰提示
        """
        warnings = []

        # 检查 Claude API Key
        if not cls.CLAUDE_API_KEY:
            warnings.append(
                "⚠️  未配置 CLAUDE_API_KEY\n"
                "   系统将使用规则引擎降级方案（准确率较低）\n"
                "   配置方法：\n"
                "   1. 创建 .env 文件：cp .env.example .env\n"
                "   2. 编辑 .env，填入你的 API Key\n"
                "   3. 或设置环境变量：export CLAUDE_API_KEY=your_key_here"
            )

        # 检查上传目录
        if not os.path.exists(cls.UPLOAD_FOLDER):
            try:
                os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
                logger.info(f"创建上传目录: {cls.UPLOAD_FOLDER}")
            except Exception as e:
                warnings.append(f"⚠️  无法创建上传目录: {e}")

        # 输出警告信息
        if warnings:
            logger.warning("\n" + "\n".join(warnings))

        return len(warnings) == 0

    @classmethod
    def get_claude_api_key(cls) -> str:
        """
        获取 Claude API Key

        如果未配置，抛出友好的异常提示
        """
        if not cls.CLAUDE_API_KEY:
            raise RuntimeError(
                "Claude API Key 未配置\n\n"
                "请按以下步骤配置：\n"
                "1. 访问 https://console.anthropic.com/ 获取 API Key\n"
                "2. 创建 .env 文件：cp .env.example .env\n"
                "3. 编辑 .env，填入：CLAUDE_API_KEY=your_actual_key_here\n"
                "4. 或设置环境变量：export CLAUDE_API_KEY=your_key_here\n\n"
                "如果只是测试，系统会自动使用规则引擎降级方案（无需 API Key）"
            )
        return cls.CLAUDE_API_KEY

    @classmethod
    def print_config_summary(cls):
        """打印配置摘要（用于调试和启动日志）"""
        print("\n" + "=" * 60)
        print(" 配置摘要")
        print("=" * 60)
        print(f"  OCR Provider: {cls.OCR_PROVIDER}")
        print(f"  OCR Language: {cls.OCR_LANG}")
        print(f"  Claude API: {'✅ 已配置' if cls.CLAUDE_API_KEY else '❌ 未配置（将使用规则引擎降级）'}")
        print(f"  Claude Model: {cls.CLAUDE_MODEL}")
        print(f"  Upload Folder: {cls.UPLOAD_FOLDER}")
        print("=" * 60 + "\n")
