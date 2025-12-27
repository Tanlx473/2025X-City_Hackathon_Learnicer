import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from services.ocr_service import ocr_extract_text
from services.llm_service import analyze_physics_text
from utils.json_builder import build_response

upload_bp = Blueprint("upload", __name__)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@upload_bp.post("/upload")
def upload():
    """
    接收题目图片 -> OCR ->（占位LLM）-> 返回统一JSON
    """
    if "file" not in request.files:
        return jsonify({"error": "missing file field 'file'"}), 400

    f = request.files["file"]
    if not f or f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    if not allowed_file(f.filename):
        return jsonify({"error": "unsupported file type"}), 400

    filename = secure_filename(f.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    try:
        f.save(save_path)
    except Exception as e:
        return jsonify({"error": "failed to save file", "details": str(e)}), 500

    # OCR
    try:
        text = ocr_extract_text(save_path)
    except Exception as e:
        return jsonify({"error": "ocr failed", "details": str(e)}), 500

    # LLM/规则引擎：抽取题目类型 + 动画参数
    llm_result = analyze_physics_text(text)

    # 统一响应结构
    resp = build_response(
        problem_type=llm_result.get("problem_type", "unknown"),
        ocr_text=text,
        solution_steps=llm_result.get("solution_steps", []),
        animation_instructions=llm_result.get("animation_instructions", []),
    )
    # 兼容额外字段（如参数等），方便前端调试
    if "parameters" in llm_result:
        resp["parameters"] = llm_result["parameters"]
    return jsonify(resp), 200
