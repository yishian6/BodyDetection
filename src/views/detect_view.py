from flask import Blueprint, jsonify, request
from os.path import join, exists
from src.config import IMAGE_FOLDER
from src.ImageDetector import detect_and_draw

detect_bp = Blueprint("detect", __name__, url_prefix="/detect")


@detect_bp.route("/images", methods=["POST"])
def detect_images_route():
    """
    图像检测
    """
    # 获取图片ID
    image_id = request.json.get("image_id")
    if not image_id:
        return jsonify({"error": "No image ID provided"}), 400
    # 在上传目录中查找图片
    for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        image_name = f"{image_id}{ext}"
        image_path = join(IMAGE_FOLDER, image_name)
        if exists(image_path):
            try:
                # 执行目标检测
                res = detect_and_draw(image_path)
                return jsonify(
                    {
                        "message": "Detection success",
                        "save_path": res[0],
                        "process_time": res[1],
                    }
                )
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({"error": "Image not found"}), 404


@detect_bp.route("/videos", methods=["POST"])
def detect_videos_route():
    """
    视频检测
    """
    if "video_id" not in request.json:
        return jsonify({"error": "No video ID provided"}), 400
    