def llm_analyze_placeholder(ocr_text: str) -> dict:
    """
    先用固定输出让前端/可视化联调。
    后续替换为真实 Claude API 调用，并把输出严格映射到统一JSON格式。
    """
    return {
        "problem_type": "physics_projectile",
        "solution_steps": [
            "Step 1: Extract known parameters from OCR text.",
            "Step 2: Assume projectile motion model and compute trajectory.",
            "Step 3: Provide animation instructions for Canvas rendering."
        ],
        "animation_instructions": {
            "type": "projectile",
            "initial_speed": 20,
            "angle": 45,
            "gravity": 9.8,
            "duration": 3.0,
            "scale": 20
        }
    }
