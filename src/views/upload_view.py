from flask import Blueprint, jsonify, request
import uuid
import os
from src.config import IMAGE_FOLDER, VIDEO_FOLDER

upload_dp = Blueprint("upload", __name__, url_prefix="/upload")



@upload_dp.route("/image", methods=["POST"])
def upload_image():
    """
    上传图片接口
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 生成唯一的文件名
        file_extension = os.path.splitext(file.filename)[1]
        image_id = str(uuid.uuid4())
        filename = f"{image_id}{file_extension}"
        file_path = os.path.join(IMAGE_FOLDER, filename)

        file.save(file_path)

        return jsonify({"message": "Image upload success", "image_id": image_id})


@upload_dp.route("/video", methods=["POST"])
def upload_video():
    """
    上传视频接口
    """
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 生成唯一的文件名
        file_extension = os.path.splitext(file.filename)[1]
        video_id = str(uuid.uuid4())
        filename = f"{video_id}{file_extension}"
        file_path = os.path.join(VIDEO_FOLDER, filename)

        file.save(file_path)

        return jsonify({"message": "Video upload success", "video_id": video_id})
