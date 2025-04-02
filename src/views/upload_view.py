from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory, Response
import uuid
import os
from src.config import IMAGE_FOLDER, VIDEO_FOLDER, UPLOAD_FOLDER

upload_dp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_dp.route("/image", methods=["POST"])
def upload_image():
    """
    上传图片接口
    """
    if "file" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 生成唯一的文件名
        file_extension = os.path.splitext(file.filename)[1]
        image_id = str(uuid.uuid4())
        filename = f"{image_id}{file_extension}"
        file_path = os.path.join(IMAGE_FOLDER, filename)
        image_type = os.path.basename(os.path.normpath(IMAGE_FOLDER))
        file.save(file_path)

        return jsonify(
            {"message": "Image upload success", "image_id": image_id, "file_path": f"/upload/{image_type}/{filename}"})


@upload_dp.route('/<param1>/<param2>')
def uploaded_file(param1, param2):
    #  param1 是目录，param2 是文件名
    if param2.split('.')[-1] in ['png', 'jpg', 'jpeg', 'gif']:
        return send_from_directory(Path(UPLOAD_FOLDER) / param1, param2)
    else:
        return send_from_directory(Path(UPLOAD_FOLDER) / param1, param2, mimetype='video/mp4', as_attachment=True)


@upload_dp.route("/video", methods=["POST"])
def upload_video():
    """
    上传视频接口
    """
    if "file" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 生成唯一的文件名
        file_extension = os.path.splitext(file.filename)[1]
        video_id = str(uuid.uuid4())
        filename = f"{video_id}{file_extension}"
        file_path = os.path.join(VIDEO_FOLDER, filename)
        image_type = os.path.basename(os.path.normpath(VIDEO_FOLDER))
        file.save(file_path)

        return jsonify(
            {"message": "Video upload success", "video_id": video_id,
             "file_path": f"/upload/video/{image_type}/{filename}"})


@upload_dp.route('/video/<param1>/<param2>')
def stream_video(param1, param2):
    video_path = Path(UPLOAD_FOLDER) / param1 / param2
    try:
        file_size = video_path.stat().st_size
    except FileNotFoundError:
        return "File not found", 404
    except Exception as e:
        return f"Error accessing file: {e}", 500

    range_header = request.headers.get('Range')
    if range_header:
        start, end = range_header.replace('bytes=', '').split('-')
        start = int(start)
        end = int(end) if end else file_size - 1
        # 确保 end 不超过文件大小
        end = min(end, file_size - 1)
    else:
        start = 0
        end = file_size - 1

    content_length = end - start + 1
    # 确保 content_length 不会超过文件的实际剩余长度
    content_length = min(content_length, file_size - start)

    def generate():
        try:
            with open(video_path, 'rb') as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(2048 * 1024, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    remaining -= len(chunk)
        except Exception as e:
            print(f"Error reading file: {e}")
            yield b''  # 确保生成器能够正确结束

    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Content-Length': str(content_length),
        'Content-Type': 'video/mp4'
    }

    return Response(generate(), status=206, headers=headers)
