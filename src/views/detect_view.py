from flask import Blueprint, jsonify, request
from os.path import join, exists
from src.config import IMAGE_FOLDER, VIDEO_FOLDER, MERGE_FOLDER
from src.image_detect import detect_and_draw
from src.video_detect import detect_video
from src.MultiModalVideoDetector import MultiModalVideoDetector

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

    return:
    {
        "message": "Detection success",
        "save_path": output_path,
        "process_time": process_time,
        "detections": detections,
    }
    """
    # 获取视频ID
    video_id = request.json.get("video_id")
    if not video_id:
        return jsonify({"error": "No video ID provided"}), 400

    # 在上传目录中查找视频
    for ext in [".mp4", ".avi", ".mov"]:
        video_name = f"{video_id}{ext}"
        video_path = join(VIDEO_FOLDER, video_name)
        if exists(video_path):
            try:
                # 执行视频目标检测
                # TODO: 避免阻塞，直接返回结果后台处理后的结果，前端轮询获取结果
                output_path, process_time, detections = detect_video(video_path)
                return jsonify(
                    {
                        "message": "Detection success",
                        "save_path": output_path,
                        "process_time": process_time,
                        "detections": detections,
                    }
                )
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({"error": "Video not found"}), 404


@detect_bp.route("/merge_and_detect", methods=["POST"])
def merge_and_detect():  #
    ir_path = request.args.get("ir_path")
    tr_path = request.args.get("tr_path")
    model_path = request.args.get("model_path")
    conf_thres = float(request.args.get("conf_thres", 0.25))

    output_path = join(MERGE_FOLDER, "output_detection.mp4")

    # 初始化视频流
    detector = MultiModalVideoDetector(
        ir_params={"video_path": ir_path},
        tr_params={"video_path": tr_path},
        model_path=model_path,
        output_path=output_path,
        conf_thres=conf_thres,
        show_preview=False,
    )
    detector.run()
    return jsonify({"message": "Detection success", "save_path": output_path})
