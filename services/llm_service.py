"""物理题解析与动画指令生成服务

集成 Claude API 进行智能解析，同时保留规则引擎作为降级方案。
支持的运动类型：
- projectile: 一般抛体运动（任意角度）
- horizontal_projectile: 平抛运动（角度=0）
- free_fall: 自由落体（v0=0, angle=90）
- vertical_throw: 竖直上抛（angle=90）
- uniform: 匀速直线运动
"""

from __future__ import annotations

import json
import logging
import math
import re
from typing import Any, Dict, Optional

from anthropic import Anthropic
from flask import current_app

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Claude API 集成 ====================

# Claude Prompt 模板（强制返回纯 JSON）
CLAUDE_SYSTEM_PROMPT = """你是一个物理题解析专家，专门将物理运动学问题转化为可视化动画指令。

你的任务是：
1. 识别运动类型（平抛、自由落体、竖直上抛、斜抛、匀速直线等）
2. 提取关键参数（初速度、角度、高度、重力加速度等）
3. 生成解题步骤
4. 输出符合前端动画引擎的 JSON 格式

**CRITICAL: 你必须只返回纯 JSON，不要包含任何 Markdown 代码块标记（如 ```json），不要有任何解释性文字。**
"""

CLAUDE_USER_PROMPT_TEMPLATE = """请解析以下物理题目文本，提取运动类型和参数，并生成动画指令。

题目文本：
{ocr_text}

请严格按照以下 JSON 格式返回（不要包含 ```json 等 Markdown 标记）：

{{
  "motion_type": "运动类型（可选值: horizontal_projectile, free_fall, vertical_throw, projectile, uniform）",
  "parameters": {{
    "initial_speed": 初速度数值（m/s，可为 null），
    "angle": 角度数值（度，可为 null），
    "initial_height": 初始高度（m，可为 null），
    "gravity": 重力加速度（m/s²，默认 9.8）
  }},
  "solution_steps": [
    "步骤1描述",
    "步骤2描述",
    "步骤3描述"
  ]
}}

运动类型判别规则：
- horizontal_projectile: 平抛运动（水平抛出，初速度水平）
- free_fall: 自由落体（初速度为0，垂直下落）
- vertical_throw: 竖直上抛（初速度竖直向上）
- projectile: 一般斜抛运动（有初速度和抛射角）
- uniform: 匀速直线运动

参数提取注意事项：
- 如果题目中没有明确给出某个参数，设为 null
- 角度用度数表示（0-360）
- 平抛运动的角度为 0
- 自由落体的初速度为 0，角度为 90
- 竖直上抛的角度为 90

现在请开始解析，只返回 JSON："""


def _clean_json_response(text: str) -> str:
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


def _validate_and_fix_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """校验 JSON 格式，尝试修复常见问题"""
    try:
        # 先尝试直接解析
        data = json.loads(raw_text)

        # 校验必需字段
        if not isinstance(data, dict):
            logger.error("Claude返回的不是JSON对象")
            return None

        # 确保有 motion_type
        if "motion_type" not in data:
            logger.warning("缺少 motion_type 字段，使用默认值")
            data["motion_type"] = "projectile"

        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"原始文本: {raw_text[:200]}")
        return None


def _call_claude_api(ocr_text: str) -> Optional[Dict[str, Any]]:
    """调用 Claude API 解析物理题"""
    cfg = current_app.config
    api_key = cfg.get("CLAUDE_API_KEY")

    if not api_key:
        logger.info("未配置 CLAUDE_API_KEY，跳过 LLM 调用")
        return None

    try:
        client = Anthropic(api_key=api_key)

        # 构建用户提示词
        user_prompt = CLAUDE_USER_PROMPT_TEMPLATE.format(ocr_text=ocr_text)

        # 调用 Claude API
        logger.info(f"调用 Claude API: model={cfg.get('CLAUDE_MODEL')}")
        response = client.messages.create(
            model=cfg.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=cfg.get("CLAUDE_MAX_TOKENS", 2048),
            system=CLAUDE_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # 提取文本内容
        raw_text = response.content[0].text
        logger.debug(f"Claude 原始返回: {raw_text[:200]}")

        # 清理并解析 JSON
        cleaned_text = _clean_json_response(raw_text)
        parsed = _validate_and_fix_json(cleaned_text)

        if parsed:
            logger.info(f"Claude 成功解析，运动类型: {parsed.get('motion_type')}")
            return parsed

        # 第一次失败，尝试重试（添加更强的提示）
        logger.warning("首次解析失败，尝试重试...")
        retry_response = client.messages.create(
            model=cfg.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=cfg.get("CLAUDE_MAX_TOKENS", 2048),
            system=CLAUDE_SYSTEM_PROMPT + "\n\n**再次强调：只返回纯 JSON 对象，不要有任何其他内容！**",
            messages=[
                {"role": "user", "content": user_prompt + "\n\n只返回 JSON，不要解释："}
            ]
        )

        retry_text = retry_response.content[0].text
        retry_cleaned = _clean_json_response(retry_text)
        retry_parsed = _validate_and_fix_json(retry_cleaned)

        if retry_parsed:
            logger.info("重试成功")
            return retry_parsed

        logger.error("重试仍然失败，返回 None")
        return None

    except Exception as e:
        logger.error(f"Claude API 调用失败: {e}")
        return None


# ==================== 规则引擎降级方案 ====================

def _match_number(patterns, text: str) -> Optional[float]:
    """使用正则表达式匹配数字"""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def _extract_parameters_fallback(ocr_text: str) -> Dict[str, Any]:
    """规则引擎：使用正则抓取参数"""
    speed = _match_number([
        r"初速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"v0\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m/s|米/秒|米每秒)?",
        r"以\s*([0-9]+(?:\.[0-9]+)?)\s*m/s",
        r"([0-9]+(?:\.[0-9]+)?)\s*m/s\s*的.*速度",
    ], ocr_text)

    angle = _match_number([
        r"角度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*[°度]\s*角",
        r"以\s*([0-9]+(?:\.[0-9]+)?)\s*[°度]",
    ], ocr_text)

    height = _match_number([
        r"高度\s*(?:为|是|[:：])\s*([0-9]+(?:\.[0-9]+)?)",
        r"从\s*([0-9]+(?:\.[0-9]+)?)\s*[米m]",
        r"高\s*([0-9]+(?:\.[0-9]+)?)\s*[米m]",
        r"([0-9]+(?:\.[0-9]+)?)\s*米高",
        r"([0-9]+(?:\.[0-9]+)?)\s*m高",
    ], ocr_text)

    gravity = _match_number([
        r"g\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"重力加速度\s*(?:为|是|[:：])\s*([0-9]+(?:\.[0-9]+)?)",
    ], ocr_text) or 9.8

    return {
        "initial_speed": speed,
        "angle": angle,
        "initial_height": height,
        "gravity": gravity,
    }


def _detect_motion_type_fallback(ocr_text: str) -> str:
    """规则引擎：运动类型判别

    优先级：具体类型 > 一般类型
    """
    # 检查匀速直线运动（优先，避免误判）
    if "匀速" in ocr_text or "匀速直线" in ocr_text:
        return "uniform"

    # 检查自由落体（优先，很明确）
    if any(keyword in ocr_text for keyword in ["自由落体", "自由下落"]):
        return "free_fall"

    # 检查平抛运动（优先，很明确）
    if any(keyword in ocr_text for keyword in ["平抛", "水平抛", "水平抛射"]):
        return "horizontal_projectile"

    # 检查竖直上抛（需要更具体的关键词，避免误判斜抛）
    # 只有明确说"竖直"才判定为竖直上抛
    if "竖直上抛" in ocr_text or "竖直抛" in ocr_text:
        return "vertical_throw"

    # 检查角度信息：如果有角度且不是0或90，则为一般抛体
    angle_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[°度]", ocr_text)
    if angle_match:
        angle = float(angle_match.group(1))
        if 0 < angle < 90 and angle != 0:
            return "projectile"
        elif angle == 90:
            return "vertical_throw"
        elif angle == 0:
            return "horizontal_projectile"

    # 检查是否有"斜"、"角"等关键词，表明是斜抛
    if any(keyword in ocr_text for keyword in ["斜抛", "斜向", "角度"]):
        return "projectile"

    # 最后才检查一般的"抛"
    if "抛" in ocr_text or "弹道" in ocr_text or "抛体" in ocr_text:
        return "projectile"

    # 英文关键词
    lowered = ocr_text.lower()
    if "parabola" in lowered or "projectile" in lowered:
        return "projectile"

    # 如果检查到"下落"但不是自由落体，可能是有初速度的抛体
    if "下落" in ocr_text or "坠落" in ocr_text:
        return "projectile"

    # 默认返回一般抛体运动
    return "projectile"


def _compute_duration(motion_type: str, v0: float, angle_deg: float, g: float, h0: float) -> float:
    """计算运动持续时间"""
    if g <= 0:
        g = 9.8

    if motion_type == "uniform":
        return 5.0

    # 对于抛体运动，计算落地时间
    angle_rad = math.radians(angle_deg)
    vy0 = v0 * math.sin(angle_rad)

    # 求解 y(t) = h0 + vy0*t - 0.5*g*t^2 = 0
    # 使用求根公式: t = (vy0 + sqrt(vy0^2 + 2*g*h0)) / g
    discriminant = vy0 * vy0 + 2 * g * h0
    if discriminant < 0:
        return 2.0  # 默认值

    t = (vy0 + math.sqrt(discriminant)) / g
    return max(t, 0.5)  # 至少0.5秒


# ==================== 动画指令生成 ====================

def _build_animation_instructions(motion_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据运动类型和参数生成动画指令

    前端 animation.js 支持的类型：
    - type="projectile": 抛体运动（支持任意角度）
    - type="uniform": 匀速直线运动
    - type="points": 点集动画

    我们将 horizontal_projectile, free_fall, vertical_throw 都映射为 projectile
    """
    g = params.get("gravity") or 9.8
    v0 = params.get("initial_speed")
    angle = params.get("angle")
    h0 = params.get("initial_height") or 0

    # 根据运动类型设置默认值
    if motion_type == "horizontal_projectile":
        # 平抛：角度=0，需要有初速度和高度
        if v0 is None:
            v0 = 10.0  # 默认10 m/s
        if angle is None:
            angle = 0
        if h0 == 0:
            h0 = 8.0  # 默认8m高度

    elif motion_type == "free_fall":
        # 自由落体：v0=0，angle=90（但实际上angle对v0=0无影响）
        v0 = 0
        if angle is None:
            angle = 90
        if h0 == 0:
            h0 = 10.0  # 默认10m高度

    elif motion_type == "vertical_throw":
        # 竖直上抛：angle=90，需要初速度
        if v0 is None:
            v0 = 15.0  # 默认15 m/s
        if angle is None:
            angle = 90

    elif motion_type == "uniform":
        # 匀速直线
        if v0 is None:
            v0 = 5.0
        angle = 0

    else:  # general projectile
        # 一般抛体运动
        if v0 is None:
            v0 = 20.0
        if angle is None:
            angle = 45.0

    # 计算持续时间
    duration = _compute_duration(motion_type, v0, angle, g, h0)

    # 计算合适的 scale（保证物体不出画面）
    # Canvas 默认大小约 800x600，留50px边距
    max_range = v0 * v0 * abs(math.sin(2 * math.radians(angle))) / g if v0 > 0 else 10
    max_height = h0 + (v0 * math.sin(math.radians(angle))) ** 2 / (2 * g) if v0 > 0 else h0

    # scale 使得最大范围在画面内
    scale_x = 700 / max(max_range, 1)
    scale_y = 500 / max(max_height, 1)
    scale = min(scale_x, scale_y, 30)  # 不超过30，确保可见
    scale = max(scale, 10)  # 不小于10，确保不太小

    return {
        "type": "uniform" if motion_type == "uniform" else "projectile",
        "initial_speed": v0,
        "angle": angle,
        "gravity": g,
        "initial_x": 0,
        "initial_y": h0,
        "duration": duration,
        "scale": scale,
        # 额外字段，方便调试
        "motion_type_original": motion_type,
    }


def _build_solution_steps(motion_type: str, params: Dict[str, Any], ocr_preview: str) -> list:
    """生成解题步骤"""
    motion_type_names = {
        "horizontal_projectile": "平抛运动",
        "free_fall": "自由落体运动",
        "vertical_throw": "竖直上抛运动",
        "uniform": "匀速直线运动",
        "projectile": "抛体运动",
    }

    type_name = motion_type_names.get(motion_type, "运动")

    steps = [
        f"解析题干：{ocr_preview[:60]}{'...' if len(ocr_preview) > 60 else ''}",
        f"识别运动类型：{type_name}",
    ]

    # 参数说明
    v0 = params.get("initial_speed")
    angle = params.get("angle")
    h0 = params.get("initial_height") or 0
    g = params.get("gravity") or 9.8

    param_desc = f"提取参数：初速度={v0 or '默认'} m/s, 角度={angle or '默认'}°, 初始高度={h0} m, g={g} m/s²"
    steps.append(param_desc)

    steps.append("生成动画指令，前端 Canvas 将播放物体运动轨迹")

    return steps


# ==================== 主入口 ====================

def analyze_physics_text(ocr_text: str) -> dict:
    """
    主入口：解析物理题文本，返回结构化结果

    返回格式：
    {
        "problem_type": str,
        "parameters": dict,
        "solution_steps": list,
        "animation_instructions": dict
    }
    """
    if not ocr_text or not ocr_text.strip():
        logger.warning("OCR文本为空，使用默认示例")
        ocr_text = "平抛运动示例"

    preview = ocr_text[:100] + ("..." if len(ocr_text) > 100 else "")

    # 1. 优先尝试 Claude API
    claude_result = None
    if current_app.config.get("ENABLE_LLM"):
        claude_result = _call_claude_api(ocr_text)

    if claude_result:
        # 使用 Claude 解析结果
        motion_type = claude_result.get("motion_type", "projectile")
        params = claude_result.get("parameters", {})

        # 确保参数格式正确
        normalized_params = {
            "initial_speed": params.get("initial_speed"),
            "angle": params.get("angle"),
            "initial_height": params.get("initial_height"),
            "gravity": params.get("gravity") or 9.8,
        }

        # 生成动画指令
        animation_instructions = _build_animation_instructions(motion_type, normalized_params)

        # 解题步骤
        solution_steps = claude_result.get("solution_steps") or _build_solution_steps(
            motion_type, normalized_params, preview
        )

        logger.info(f"使用 Claude 解析结果: motion_type={motion_type}")

    else:
        # 2. 降级使用规则引擎
        logger.info("使用规则引擎降级方案")
        motion_type = _detect_motion_type_fallback(ocr_text)
        params = _extract_parameters_fallback(ocr_text)

        animation_instructions = _build_animation_instructions(motion_type, params)
        solution_steps = _build_solution_steps(motion_type, params, preview)

    # 3. 组装返回结果
    return {
        "problem_type": f"physics_{motion_type}",
        "parameters": {
            "motion_type": motion_type,
            "preview_text": preview,
            **{k: v for k, v in (params if claude_result else params).items() if v is not None}
        },
        "solution_steps": solution_steps,
        "animation_instructions": animation_instructions,
    }