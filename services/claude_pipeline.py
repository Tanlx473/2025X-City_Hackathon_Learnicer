"""Claude 多模态一体化 Pipeline
统一处理：OCR（从图片提取题目文本） + 题目解析 + 动画指令生成

环境变量依赖：
- CLAUDE_API_KEY: Claude API 密钥（必需，claude 模式）
- CLAUDE_MODEL: Claude 模型名称（可选，默认 claude-3-5-sonnet-20241022）
- PIPELINE_MODE: claude/manual（可选，默认 claude）
"""

import base64
import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

from anthropic import Anthropic

logger = logging.getLogger(__name__)


# ==================== 配置 ====================

def get_pipeline_mode() -> str:
    """获取当前 Pipeline 模式

    Returns:
        'claude' 或 'manual'
    """
    return os.environ.get("PIPELINE_MODE", "claude").lower()


def get_claude_credentials() -> tuple[str, str]:
    """获取 Claude API 配置

    Returns:
        (api_key, model)

    Raises:
        RuntimeError: 环境变量未设置
    """
    api_key = os.environ.get("CLAUDE_API_KEY", "").strip()
    model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20240620").strip()

    if not api_key:
        raise RuntimeError(
            "Claude API Key 未配置！\n"
            "请设置环境变量：\n"
            "  export CLAUDE_API_KEY=your_api_key\n"
            "或使用 manual 模式：\n"
            "  export PIPELINE_MODE=manual"
        )

    logger.info(f"✅ Claude API 配置已加载（model: {model}）")
    return api_key, model


# ==================== Claude 多模态调用 ====================

CLAUDE_SYSTEM_PROMPT = """你是一个物理题 OCR + 解析专家。你的任务是：

1. **OCR**：从图片中提取完整的题目文字（包括中英文、数字、数学公式）
2. **题型识别**：判断运动类型（平抛、自由落体、竖直上抛、斜抛、匀速直线、斜面等）
3. **参数提取**：提取关键物理参数（初速度、角度、高度、重力加速度、摩擦系数等）
4. **解题步骤**：生成清晰的解题步骤（至少 3 步）
5. **动画指令**：输出符合前端动画引擎的 JSON 格式

**CRITICAL：你必须只返回纯 JSON，不要包含任何 Markdown 代码块标记（如 ```json），不要有任何解释性文字。**
"""

CLAUDE_USER_PROMPT = """请从图片中识别物理题目，并按以下 JSON 格式返回（不要包含 ```json 等标记）：

{
  "problem_text": "OCR 提取的完整题目文字",
  "problem_type": "运动类型（可选值见下方）",
  "parameters": {
    "initial_speed": 初速度（m/s，可为 null），
    "angle": 角度（度，可为 null），
    "initial_height": 初始高度（m，可为 null），
    "gravity": 重力加速度（m/s²，默认 9.8），
    "friction": 摩擦系数（可为 null）
  },
  "solution_steps": [
    "步骤1：识别题干和运动类型",
    "步骤2：列出已知条件和待求量",
    "步骤3：应用物理公式求解",
    "步骤4：（可选）验证结果的合理性"
  ],
  "animation_instructions": {
    "type": "动画类型（projectile/uniform/free_fall/inclined_plane）",
    "initial_speed": 初速度（同上），
    "angle": 角度（同上），
    "gravity": 重力加速度（同上），
    "initial_x": 0,
    "initial_y": 初始高度（同上），
    "duration": 持续时间（秒，自动计算或估算），
    "scale": 缩放比例（10-30 之间，确保动画可见）
  }
}

**运动类型判别规则：**
- projectile: 一般抛体运动（任意角度，有初速度）
- horizontal_projectile: 平抛运动（角度=0 或水平抛出）
- free_fall: 自由落体（初速度=0，垂直下落）
- vertical_throw: 竖直上抛（角度=90，竖直向上）
- uniform: 匀速直线运动
- inclined_plane: 斜面运动

**动画类型映射：**
- projectile → type="projectile"
- horizontal_projectile → type="projectile"（angle=0）
- free_fall → type="free_fall"
- vertical_throw → type="projectile"（angle=90）
- uniform → type="uniform"
- inclined_plane → type="inclined_plane"

**参数提取要求：**
- 如果题目中没有明确给出某个参数，设为 null
- 角度用度数表示（0-360）
- 平抛运动的角度为 0
- 自由落体的初速度为 0
- 持续时间 duration：根据运动学公式估算，确保物体完成完整运动（落地或到达终点）
- 缩放比例 scale：10-30 之间，确保动画在画布中可见

现在请开始识别图片中的物理题目，只返回 JSON："""


def encode_image_to_base64(image_source: Union[str, bytes, Path]) -> tuple[str, str]:
    """将图片编码为 base64

    Args:
        image_source: 图片路径（str/Path）或图片字节（bytes）

    Returns:
        (base64_string, mime_type)

    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 不支持的图片格式
    """
    # 读取图片字节
    if isinstance(image_source, bytes):
        image_data = image_source
        # 根据文件头判断格式
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            mime_type = "image/gif"
        elif image_data[:4] == b'WEBP':
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"  # 默认
    else:
        # 路径方式
        image_path = Path(image_source)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as f:
            image_data = f.read()

        # 根据扩展名判断格式
        suffix = image_path.suffix.lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        mime_type = mime_map.get(suffix, 'image/jpeg')

    # 编码为 base64
    base64_string = base64.standard_b64encode(image_data).decode('utf-8')

    logger.info(f"✅ 图片已编码为 base64（{len(base64_string)} 字符，类型: {mime_type}）")
    return base64_string, mime_type


def clean_json_response(text: str) -> str:
    """清理 Claude 返回的文本，移除 Markdown 代码块标记"""
    text = text.strip()

    # 移除开头的 ```json 或 ```
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    # 移除结尾的 ```
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def validate_and_normalize_response(data: dict) -> dict:
    """校验并规范化 Claude 返回的 JSON

    Args:
        data: Claude 返回的原始 dict

    Returns:
        规范化后的 dict

    Raises:
        ValueError: 数据格式不符合要求
    """
    # 必需字段
    if "problem_text" not in data or not data["problem_text"]:
        raise ValueError("缺少 problem_text 字段或为空")

    # 默认值
    if "problem_type" not in data or not data["problem_type"]:
        logger.warning("缺少 problem_type，使用默认值 projectile")
        data["problem_type"] = "projectile"

    if "parameters" not in data or not isinstance(data["parameters"], dict):
        logger.warning("缺少 parameters，使用空字典")
        data["parameters"] = {}

    if "solution_steps" not in data or not isinstance(data["solution_steps"], list):
        logger.warning("缺少 solution_steps，使用默认值")
        data["solution_steps"] = [
            "步骤1：识别题干和运动类型",
            "步骤2：列出已知条件",
            "步骤3：应用物理公式求解"
        ]

    if "animation_instructions" not in data or not isinstance(data["animation_instructions"], dict):
        logger.warning("缺少 animation_instructions，将自动生成")
        data["animation_instructions"] = {}

    # 规范化 animation_instructions
    anim = data["animation_instructions"]
    if "type" not in anim:
        # 根据 problem_type 推断 type
        problem_type = data["problem_type"]
        if "uniform" in problem_type:
            anim["type"] = "uniform"
        elif "inclined" in problem_type or "slope" in problem_type:
            anim["type"] = "inclined_plane"
        elif "free_fall" in problem_type:
            anim["type"] = "free_fall"
        else:
            anim["type"] = "projectile"

    # 确保必要的动画参数
    params = data["parameters"]
    if "initial_speed" not in anim:
        anim["initial_speed"] = params.get("initial_speed", 10.0)
    if "angle" not in anim:
        anim["angle"] = params.get("angle", 45)
    if "gravity" not in anim:
        anim["gravity"] = params.get("gravity", 9.8)
    if "initial_x" not in anim:
        anim["initial_x"] = 0
    if "initial_y" not in anim:
        anim["initial_y"] = params.get("initial_height", 0)

    # 计算持续时间（如果缺失）
    if "duration" not in anim or not anim["duration"]:
        anim["duration"] = estimate_duration(
            anim["type"],
            anim["initial_speed"],
            anim["angle"],
            anim["gravity"],
            anim["initial_y"]
        )

    # 计算缩放比例（如果缺失）
    if "scale" not in anim or not anim["scale"]:
        anim["scale"] = estimate_scale(
            anim["type"],
            anim["initial_speed"],
            anim["angle"],
            anim["gravity"],
            anim["initial_y"]
        )

    logger.info("✅ 响应数据校验通过")
    return data


def estimate_duration(motion_type: str, v0: float, angle: float, g: float, h0: float) -> float:
    """估算运动持续时间（秒）"""
    if g <= 0:
        g = 9.8
    if v0 is None:
        v0 = 10.0
    if angle is None:
        angle = 45
    if h0 is None:
        h0 = 0

    if motion_type == "uniform":
        return 5.0

    if motion_type == "free_fall":
        # t = sqrt(2h/g)
        if h0 > 0:
            return math.sqrt(2 * h0 / g)
        return 2.0

    # 抛体运动：求解 y(t) = h0 + vy0*t - 0.5*g*t^2 = 0
    angle_rad = math.radians(angle)
    vy0 = v0 * math.sin(angle_rad)

    discriminant = vy0 * vy0 + 2 * g * h0
    if discriminant < 0:
        return 2.0

    t = (vy0 + math.sqrt(discriminant)) / g
    return max(t, 0.5)


def estimate_scale(motion_type: str, v0: float, angle: float, g: float, h0: float) -> float:
    """估算缩放比例（10-30）"""
    if g <= 0:
        g = 9.8
    if v0 is None:
        v0 = 10.0
    if angle is None:
        angle = 45
    if h0 is None:
        h0 = 0

    if motion_type == "uniform":
        return 20.0

    # 计算最大范围和高度
    angle_rad = math.radians(angle)
    max_range = v0 * v0 * abs(math.sin(2 * angle_rad)) / g if v0 > 0 else 10
    max_height = h0 + (v0 * math.sin(angle_rad)) ** 2 / (2 * g) if v0 > 0 else h0

    # Canvas 默认大小约 800x600，留边距
    scale_x = 700 / max(max_range, 1)
    scale_y = 500 / max(max_height, 1)
    scale = min(scale_x, scale_y, 30)
    scale = max(scale, 10)

    return scale


def call_claude_pipeline(image_source: Union[str, bytes, Path]) -> dict:
    """调用 Claude 多模态 API 完成 OCR + 解析 + 动画指令生成

    Args:
        image_source: 图片路径或图片字节

    Returns:
        {
            "problem_text": str,
            "problem_type": str,
            "parameters": dict,
            "solution_steps": list[str],
            "animation_instructions": dict
        }

    Raises:
        RuntimeError: API 调用失败
        ValueError: 响应格式错误
    """
    # 1. 获取 API 配置
    api_key, model = get_claude_credentials()

    # 2. 编码图片
    logger.info("开始 Claude 多模态 Pipeline...")
    base64_image, mime_type = encode_image_to_base64(image_source)

    # 3. 构建消息
    client = Anthropic(api_key=api_key)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64_image,
                    },
                },
                {
                    "type": "text",
                    "text": CLAUDE_USER_PROMPT
                }
            ],
        }
    ]

    # 4. 调用 Claude API
    try:
        logger.info(f"正在调用 Claude API（model: {model}）...")
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=CLAUDE_SYSTEM_PROMPT,
            messages=messages,
            temperature=0  # 使用确定性输出
        )

        # 5. 提取并解析响应
        raw_text = response.content[0].text
        logger.debug(f"Claude 原始返回: {raw_text[:300]}...")

        # 清理并解析 JSON
        cleaned_text = clean_json_response(raw_text)

        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"原始文本: {cleaned_text[:500]}")
            raise ValueError(f"Claude 返回的不是有效 JSON: {e}")

        # 6. 校验并规范化
        normalized = validate_and_normalize_response(data)

        logger.info(f"✅ Claude Pipeline 成功完成（problem_type: {normalized['problem_type']}）")
        return normalized

    except Exception as e:
        logger.error(f"❌ Claude API 调用失败: {e}")
        raise RuntimeError(f"Claude Pipeline 失败: {e}")


# ==================== Manual 模式（降级方案） ====================

def manual_pipeline(manual_text: str) -> dict:
    """Manual 模式：直接解析文本（无 OCR）

    Args:
        manual_text: 用户提供的题目文本

    Returns:
        同 call_claude_pipeline 的返回格式
    """
    if not manual_text or not manual_text.strip():
        raise ValueError("manual_text 不能为空")

    logger.info(f"✅ [Manual Mode] 使用手动输入文本（{len(manual_text)} 字符）")

    # 使用规则引擎解析
    problem_type = detect_motion_type(manual_text)
    params = extract_parameters(manual_text)

    # 生成解题步骤
    solution_steps = generate_solution_steps(problem_type, params, manual_text)

    # 生成动画指令
    animation_instructions = generate_animation_instructions(problem_type, params)

    return {
        "problem_text": manual_text.strip(),
        "problem_type": problem_type,
        "parameters": params,
        "solution_steps": solution_steps,
        "animation_instructions": animation_instructions,
    }


def detect_motion_type(text: str) -> str:
    """规则引擎：检测运动类型"""
    # 检查匀速直线运动
    if "匀速" in text or "匀速直线" in text:
        return "uniform"

    # 检查自由落体
    if any(kw in text for kw in ["自由落体", "自由下落"]):
        return "free_fall"

    # 检查平抛运动
    if any(kw in text for kw in ["平抛", "水平抛", "水平抛射"]):
        return "horizontal_projectile"

    # 检查竖直上抛
    if "竖直上抛" in text or "竖直抛" in text:
        return "vertical_throw"

    # 检查斜面
    if any(kw in text for kw in ["斜面", "斜坡", "inclined plane"]):
        return "inclined_plane"

    # 检查角度：如果有角度且不是 0 或 90，则为一般抛体
    angle_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[°度]", text)
    if angle_match:
        angle = float(angle_match.group(1))
        if 0 < angle < 90:
            return "projectile"
        elif angle == 90:
            return "vertical_throw"
        elif angle == 0:
            return "horizontal_projectile"

    # 检查斜抛
    if any(kw in text for kw in ["斜抛", "斜向", "角度"]):
        return "projectile"

    # 最后检查一般的"抛"
    if "抛" in text or "弹道" in text or "抛体" in text:
        return "projectile"

    # 默认
    return "projectile"


def extract_parameters(text: str) -> dict:
    """规则引擎：提取参数"""
    def match_number(patterns):
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    continue
        return None

    speed = match_number([
        r"初速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"v0?\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m/s|米/秒)?",
        r"以\s*([0-9]+(?:\.[0-9]+)?)\s*m/s",
        r"([0-9]+(?:\.[0-9]+)?)\s*m/s\s*的.*速度",
    ])

    angle = match_number([
        r"角度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*[°度]\s*角",
        r"以\s*([0-9]+(?:\.[0-9]+)?)\s*[°度]",
    ])

    height = match_number([
        r"高度\s*(?:为|是|[:：])\s*([0-9]+(?:\.[0-9]+)?)",
        r"从\s*([0-9]+(?:\.[0-9]+)?)\s*[米m]",
        r"高\s*([0-9]+(?:\.[0-9]+)?)\s*[米m]",
        r"([0-9]+(?:\.[0-9]+)?)\s*米高",
        r"([0-9]+(?:\.[0-9]+)?)\s*m高",
    ])

    gravity = match_number([
        r"g\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"重力加速度\s*(?:为|是|[:：])\s*([0-9]+(?:\.[0-9]+)?)",
    ]) or 9.8

    friction = match_number([
        r"摩擦系数\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"μ\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
    ])

    return {
        "initial_speed": speed,
        "angle": angle,
        "initial_height": height,
        "gravity": gravity,
        "friction": friction,
    }


def generate_solution_steps(motion_type: str, params: dict, text_preview: str) -> list:
    """生成解题步骤"""
    type_names = {
        "horizontal_projectile": "平抛运动",
        "free_fall": "自由落体运动",
        "vertical_throw": "竖直上抛运动",
        "uniform": "匀速直线运动",
        "projectile": "抛体运动",
        "inclined_plane": "斜面运动",
    }

    type_name = type_names.get(motion_type, "运动")
    preview = text_preview[:60] + ('...' if len(text_preview) > 60 else '')

    steps = [
        f"解析题干：{preview}",
        f"识别运动类型：{type_name}",
    ]

    # 参数说明
    v0 = params.get("initial_speed")
    angle = params.get("angle")
    h0 = params.get("initial_height") or 0
    g = params.get("gravity") or 9.8

    param_parts = []
    if v0 is not None:
        param_parts.append(f"初速度={v0} m/s")
    if angle is not None:
        param_parts.append(f"角度={angle}°")
    if h0:
        param_parts.append(f"高度={h0} m")
    param_parts.append(f"g={g} m/s²")

    steps.append(f"提取参数：{', '.join(param_parts)}")
    steps.append("应用运动学公式求解各物理量")
    steps.append("生成动画指令，可视化物体运动轨迹")

    return steps


def generate_animation_instructions(motion_type: str, params: dict) -> dict:
    """生成动画指令"""
    g = params.get("gravity") or 9.8
    v0 = params.get("initial_speed")
    angle = params.get("angle")
    h0 = params.get("initial_height") or 0
    friction = params.get("friction")

    # 根据运动类型设置默认值
    if motion_type == "horizontal_projectile":
        if v0 is None:
            v0 = 10.0
        if angle is None:
            angle = 0
        if h0 == 0:
            h0 = 8.0
        anim_type = "projectile"

    elif motion_type == "free_fall":
        v0 = 0
        if angle is None:
            angle = 90
        if h0 == 0:
            h0 = 10.0
        anim_type = "free_fall"

    elif motion_type == "vertical_throw":
        if v0 is None:
            v0 = 15.0
        if angle is None:
            angle = 90
        anim_type = "projectile"

    elif motion_type == "uniform":
        if v0 is None:
            v0 = 5.0
        angle = 0
        anim_type = "uniform"

    elif motion_type == "inclined_plane":
        if v0 is None:
            v0 = 0
        if angle is None:
            angle = 30
        anim_type = "inclined_plane"

    else:  # general projectile
        if v0 is None:
            v0 = 20.0
        if angle is None:
            angle = 45.0
        anim_type = "projectile"

    # 计算持续时间和缩放
    duration = estimate_duration(anim_type, v0, angle, g, h0)
    scale = estimate_scale(anim_type, v0, angle, g, h0)

    instructions = {
        "type": anim_type,
        "initial_speed": v0,
        "angle": angle,
        "gravity": g,
        "initial_x": 0,
        "initial_y": h0,
        "duration": duration,
        "scale": scale,
    }

    # 斜面特有参数
    if motion_type == "inclined_plane" and friction is not None:
        instructions["friction"] = friction

    return instructions


# ==================== 主入口 ====================

def process_image(
    image_source: Optional[Union[str, bytes, Path]] = None,
    manual_text: Optional[str] = None
) -> dict:
    """主入口：处理图片或文本，返回统一的结构化结果

    Args:
        image_source: 图片路径/字节（claude 模式必需）
        manual_text: 手动输入的题目文本（manual 模式必需）

    Returns:
        {
            "problem_text": str,
            "problem_type": str,
            "parameters": dict,
            "solution_steps": list[str],
            "animation_instructions": dict
        }

    Raises:
        ValueError: 参数错误
        RuntimeError: 处理失败
    """
    mode = get_pipeline_mode()
    logger.info(f"Pipeline 模式: {mode}")

    if mode == "claude":
        # Claude 模式：必须提供图片
        if not image_source:
            raise ValueError("claude 模式需要提供 image_source（图片路径或字节）")

        return call_claude_pipeline(image_source)

    elif mode == "manual":
        # Manual 模式：必须提供文本
        if not manual_text:
            raise ValueError(
                "manual 模式需要提供 manual_text\n"
                "请在上传请求中添加 manual_text 参数"
            )

        return manual_pipeline(manual_text)

    else:
        raise ValueError(
            f"不支持的 PIPELINE_MODE: {mode}\n"
            f"可选值: claude, manual"
        )


def get_pipeline_status() -> dict:
    """获取 Pipeline 状态（健康检查）

    Returns:
        {
            "mode": "claude/manual",
            "claude_configured": bool,
            "error": Optional[str]
        }
    """
    mode = get_pipeline_mode()

    status = {
        "mode": mode,
        "claude_configured": False,
        "error": None
    }

    if mode == "claude":
        try:
            get_claude_credentials()
            status["claude_configured"] = True
        except Exception as e:
            status["error"] = str(e)
            status["claude_configured"] = False

    return status