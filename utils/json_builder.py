def build_response(problem_type: str, ocr_text: str, solution_steps: list, animation_instructions: dict) -> dict:
    return {
        "problem_type": problem_type,
        "ocr_text": ocr_text,
        "solution_steps": solution_steps,
        "animation_instructions": animation_instructions
    }
