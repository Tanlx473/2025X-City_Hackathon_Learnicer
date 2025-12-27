import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from services.ocr_service import extract_text, get_ocr_status
from services.llm_service import analyze_physics_text
from utils.json_builder import build_response

upload_bp = Blueprint("upload", __name__)
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@upload_bp.post("/upload")
def upload():
    """
    接收题目图片 -> OCR -> LLM/规则引擎 -> 返回统一JSON

    支持 manual_text 参数，允许直接传入文本跳过 OCR（用于调试和降级）
    """
    # 1. 检查是否有手动输入的文本（降级方案）
    manual_text = request.form.get("manual_text", "").strip()

    if manual_text:
        logger.info("使用手动输入的文本，跳过 OCR")
        ocr_text = manual_text
    else:
        # 2. 正常流程：图片上传 + OCR
        if "file" not in request.files:
            return jsonify({
                "error": "missing_file",
                "message": "请上传图片文件，或使用 manual_text 参数直接输入文本"
            }), 400

        f = request.files["file"]
        if not f or f.filename == "":
            return jsonify({
                "error": "empty_filename",
                "message": "文件名为空"
            }), 400

        if not allowed_file(f.filename):
            return jsonify({
                "error": "unsupported_file_type",
                "message": f"不支持的文件类型，仅支持: {', '.join(current_app.config['ALLOWED_EXTENSIONS'])}"
            }), 400

        filename = secure_filename(f.filename)
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

        # 保存文件
        try:
            f.save(save_path)
            logger.info(f"文件已保存: {save_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return jsonify({
                "error": "file_save_failed",
                "message": "保存文件失败",
                "details": str(e)
            }), 500

        # OCR 提取文本（使用新接口，支持 manual_text fallback）
        try:
            ocr_text = extract_text(save_path, manual_text=None)
            logger.info(f"OCR 识别成功，文本长度: {len(ocr_text)}")

            if not ocr_text or not ocr_text.strip():
                logger.warning("OCR 未识别到文本")
                return jsonify({
                    "error": "ocr_no_text",
                    "message": "未能从图片中识别到文本，请确保图片清晰且包含文字",
                    "suggestion": "您也可以使用 manual_text 参数直接输入题目文本"
                }), 400

        except Exception as e:
            logger.error(f"OCR 失败: {e}")
            return jsonify({
                "error": "ocr_failed",
                "message": "OCR 识别失败",
                "details": str(e),
                "suggestion": "您可以使用 manual_text 参数直接输入题目文本"
            }), 500

    # 3. LLM/规则引擎：解析物理题
    try:
        llm_result = analyze_physics_text(ocr_text)
        logger.info(f"解析成功: {llm_result.get('problem_type')}")
    except Exception as e:
        logger.error(f"LLM 解析失败: {e}")
        return jsonify({
            "error": "llm_analysis_failed",
            "message": "题目解析失败",
            "details": str(e),
            "ocr_text": ocr_text[:200]  # 返回部分 OCR 文本供调试
        }), 500

    # 4. 构建响应
    try:
        resp = build_response(
            problem_type=llm_result.get("problem_type", "unknown"),
            ocr_text=ocr_text,
            solution_steps=llm_result.get("solution_steps", []),
            animation_instructions=llm_result.get("animation_instructions", {}),
        )

        # 附加参数信息（方便前端调试）
        if "parameters" in llm_result:
            resp["parameters"] = llm_result["parameters"]

        logger.info("响应构建成功")
        return jsonify(resp), 200

    except Exception as e:
        logger.error(f"构建响应失败: {e}")
        return jsonify({
            "error": "response_build_failed",
            "message": "构建响应失败",
            "details": str(e)
        }), 500


@upload_bp.get("/ocr/status")
def ocr_status():
    """
    OCR 状态检查接口（用于调试和健康检查）

    返回：
    {
        "provider": "paddle/mock/manual",
        "initialized": bool,
        "lang": "ch/en",
        "error": Optional[str]
    }
    """
    try:
        status = get_ocr_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"获取 OCR 状态失败: {e}")
        return jsonify({
            "error": "status_check_failed",
            "message": "获取 OCR 状态失败",
            "details": str(e)
        }), 500
