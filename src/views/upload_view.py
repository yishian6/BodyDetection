from flask import Blueprint, jsonify, request
from os.path import join

upload_dp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_dp.route("/upload", methods=["POST"])
def upload():
    """
    上传文件
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        file_path = join("/path/to/upload", filename)
        file.save(file_path)

        return jsonify({"message": "Upload success"})
