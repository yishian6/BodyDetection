from flask import Blueprint, jsonify, request
from os.path import join
from src.ImageDetector import ImageDetector

detect_bp = Blueprint("detect", __name__, url_prefix="/detect")


@detect_bp.route("/detect/images", methods=["POST"])
def detect_images_route():
    """
    图像检测
    """
    if "image1" not in request.files or "image2" not in request.files:
        return jsonify({"error": "No image part"}), 400

    file1 = request.files["image1"]
    file2 = request.files["image2"]

    if file1.filename == "" or file2.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file1 and file2:
        filename1 = file1.filename
        filename2 = file2.filename
        file_path1 = join("/path/to/upload", filename1)
        file_path2 = join("/path/to/upload", filename2)
        file1.save(file_path1)
        file2.save(file_path2)


@detect_bp.route("/detect/videos", methods=["POST"])
def detect_videos_route():
    """
    视频检测
    """
    if "video1" not in request.files or "video2" not in request.files:
        return jsonify({"error": "No video part"}), 400

    file1 = request.files["video1"]
    file2 = request.files["video2"]

    if file1.filename == "" or file2.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file1 and file2:
        filename1 = file1.filename
        filename2 = file2.filename
        file_path1 = join("/path/to/upload", filename1)
        file_path2 = join("/path/to/upload", filename2)
        file1.save(file_path1)
        file2.save(file_path2)
