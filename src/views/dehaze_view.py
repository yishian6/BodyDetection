from flask import Blueprint, jsonify, request, send_file
from os.path import join
from src.dehaze import dehaze_algorithm

dehaze_bp = Blueprint("dehaze", __name__, url_prefix="/dehaze")


@dehaze_bp.route("/dehaze", methods=["POST"])
def dehaze():
    """
    去烟
    """
    if "image" not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        file_path = join("/upload", filename)
        file.save(file_path)

        dehazed_image_path = dehaze_algorithm(file_path)

        return send_file(dehazed_image_path, mimetype="image/jpeg")
