"""抽取物理题目信息，生成动画参数。

设计思路：
- 优先尝试调用外部 LLM（如果配置了 LLM_API_URL / LLM_API_KEY）。
- 若未配置或调用失败，则使用简易规则从 OCR 文本中提取运动类型与关键参数，返回
  前端可直接渲染的 animation_instructions 对象。
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Optional

import requests
from flask import current_app


def _match_number(patterns, text: str) -> Optional[float]:
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue
    return None


def _extract_parameters(ocr_text: str) -> Dict[str, Any]:
    """使用正则抓取常见的物理题参数，避免 LLM 不可用时完全无输出。"""

    speed = _match_number([
        r"初速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"v0\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"速度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m/s|米/秒|米每秒)?",
    ], ocr_text)

    angle = _match_number([
        r"角度\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*度",
    ], ocr_text)

    height = _match_number([
        r"高度\s*(?:为|是|:)\s*([0-9]+(?:\.[0-9]+)?)",
        r"从\s*([0-9]+(?:\.[0-9]+)?)\s*米",
        r"高\s*([0-9]+(?:\.[0-9]+)?)\s*m",
    ], ocr_text)

    gravity = _match_number([
        r"g\s*[:：=]?\s*([0-9]+(?:\.[0-9]+)?)",
        r"重力加速度\s*(?:为|是|:)\s*([0-9]+(?:\.[0-9]+)?)",
    ], ocr_text) or 9.8

    return {
        "initial_speed": speed,
        "angle": angle,
        "initial_height": height,
        "gravity": gravity,
    }


def _detect_motion_type(ocr_text: str) -> str:
    lowered = ocr_text.lower()
    if any(keyword in ocr_text for keyword in ["平抛", "水平抛", "水平抛射"]):
        return "horizontal_projectile"
    if any(keyword in ocr_text for keyword in ["自由落体", "下落", "坠落"]):
        return "free_fall"
    if any(keyword in ocr_text for keyword in ["竖直上抛", "竖直上抛运动", "上抛"]):
        return "vertical_throw"
    if "匀速" in ocr_text or "匀速直线" in ocr_text:
        return "uniform"
    if "抛" in ocr_text or "弹道" in ocr_text or "抛体" in ocr_text:
        return "projectile"
    if "parabola" in lowered or "projectile" in lowered:
        return "projectile"
    return "projectile"


def _compute_duration(motion_type: str, v0: float, angle_deg: float, g: float, h0: float) -> float:
    """估计飞行时长，便于动画循环。"""
    if g <= 0:
        return 0

    angle_rad = math.radians(angle_deg)
    vy0 = v0 * math.sin(angle_rad)

    # 匀速或点集合由前端自行控制时长
    if motion_type == "uniform":
        return 5.0

    # y(t) = h0 + vy0*t - 0.5*g*t^2 = 0
    disc = vy0 * vy0 + 2 * g * h0
    if disc < 0:
        return 0
    return max((vy0 + math.sqrt(disc)) / g, 0)


def _build_animation_payload(motion_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    g = params.get("gravity") or 9.8
    v0 = params.get("initial_speed") or 0
    angle = params.get("angle")
    h0 = params.get("initial_height") or 0

    # 针对不同类型设置默认角度 / 高度
    if motion_type == "horizontal_projectile":
        angle = angle if angle is not None else 0
        h0 = h0 or 6
    elif motion_type == "free_fall":
        v0 = v0 or 0
        angle = angle if angle is not None else 90
        h0 = h0 or 8
    elif motion_type == "vertical_throw":
        angle = angle if angle is not None else 90
        v0 = v0 or 10
    else:  # general projectile
        angle = angle if angle is not None else 45
        v0 = v0 or 18

    duration = params.get("duration") or _compute_duration(motion_type, v0, angle, g, h0)

    return {
        "type": "uniform" if motion_type == "uniform" else "projectile",
        "initial_speed": v0,
        "angle": angle,
        "gravity": g,
        "initial_x": 0,
        "initial_y": h0,
        "duration": duration,
        "scale": params.get("scale") or 24,
        "analysis_motion_type": motion_type,
    }


def _build_solution_steps(motion_type: str, params: Dict[str, Any], ocr_preview: str) -> list:
    readable = {
        "horizontal_projectile": "识别到平抛/水平抛运动",
        "free_fall": "识别到自由落体运动",
        "vertical_throw": "识别到竖直上抛运动",
        "uniform": "识别到匀速直线运动",
        "projectile": "识别到斜抛/一般抛体运动",
    }
    return [
        f"解析题干：{ocr_preview or '无有效文本'}",
        readable.get(motion_type, "识别到抛体运动模型"),
        f"提取参数：v0={params.get('initial_speed') or '默认'}, 角度={params.get('angle') or '默认'}°, 高度={params.get('initial_height') or 0} m, g={params.get('gravity') or 9.8} m/s²",
        "生成动画指令，前端 Canvas 可直接播放运动轨迹。",
    ]


def _normalize_llm_payload(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None

    animation = raw.get("animation") or raw.get("animation_instructions")
    if not animation:
        return None

    return {
        "problem_type": raw.get("problem_type", "physics_motion"),
        "parameters": raw.get("parameters", {}),
        "solution_steps": raw.get("solution_steps", []),
        "animation_instructions": animation,
    }


def _maybe_call_external_llm(ocr_text: str) -> Optional[Dict[str, Any]]:
    cfg = current_app.config
    url = cfg.get("LLM_API_URL")
    api_key = cfg.get("LLM_API_KEY")

    if not url or not api_key:
        return None

    try:
        resp = requests.post(
            url,
            json={"task": "physics_motion_extraction", "text": ocr_text},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        return _normalize_llm_payload(data)
    except Exception:
        # 外部接口失败则返回 None，后续使用本地规则兜底
        return None


def analyze_physics_text(ocr_text: str) -> dict:
    """主入口：返回包含 problem_type、parameters、solution_steps、animation_instructions 的字典。"""

    llm_first = _maybe_call_external_llm(ocr_text)
    if llm_first:
        return llm_first

    params = _extract_parameters(ocr_text)
    motion_type = _detect_motion_type(ocr_text)
    animation_payload = _build_animation_payload(motion_type, params)

    preview = ocr_text[:80] + ("..." if len(ocr_text) > 80 else "")
    params_summary = {
        "preview_text": preview or "未识别到文字",
        **{k: v for k, v in params.items() if v is not None},
        "motion_type": motion_type,
    }

    return {
        "problem_type": f"physics_{motion_type}",
        "parameters": params_summary,
        "solution_steps": _build_solution_steps(motion_type, params, preview),
        "animation_instructions": animation_payload,
    }
