def build_response(problem_type: str, ocr_text: str, solution_steps: list, animation_instructions) -> dict:
    """
    按约定字段组装统一返回结构。
    animation_instructions 允许传入 list 或 dict，保持灵活。
    """
    return {
        "problem_type": problem_type,
        "ocr_text": ocr_text,
        "solution_steps": solution_steps or [],
        "animation_instructions": animation_instructions or [],
    }
