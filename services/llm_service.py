def llm_analyze_placeholder(ocr_text: str) -> dict:
    """
    先用固定输出让前端/可视化联调。
    后续替换为真实 Claude API 调用，并把输出严格映射到统一JSON格式。
    """
    # 根据识别文本生成一个简单的占位分析结果
    problem_preview = ocr_text[:50] + ("..." if len(ocr_text) > 50 else "")
    return {
        "problem_type": "physics_projectile",
        "parameters": {
            "preview_text": problem_preview or "未识别到文字"
        },
        "solution_steps": [
            "步骤1：解析题目文本并提取已知量（占位）。",
            "步骤2：假设为抛体运动模型，建立方程（占位）。",
            "步骤3：计算弹道关键参数并准备动画指令（占位）。"
        ],
        "animation_instructions": [
            "动画指令1：展示物体以初速度 v0、角度 θ 发射（占位）。",
            "动画指令2：在重力 g 作用下的抛物线轨迹演示（占位）。",
            "动画指令3：标注关键时刻与速度矢量（占位）。"
        ]
    }
