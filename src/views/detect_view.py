import os
import uuid
from threading import Thread
from flask import Blueprint, jsonify, request
from os.path import join, exists
from src.config import IMAGE_FOLDER, DETECT_FOLDER, VIDEO_FOLDER, MERGE_FOLDER
from src.image_detect import detect_and_draw
from src.video_detect import detect_video
from src.MultiModalVideoDetector import MultiModalVideoDetector
from src.task_manager import task_manager, TaskStatus
from src.config import get_logger
from src.cache import video_cache

logger = get_logger()

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
        image_type = os.path.basename(os.path.normpath(DETECT_FOLDER))
        if exists(image_path):
            try:
                # 执行目标检测
                res = detect_and_draw(image_path)

                return jsonify(
                    {
                        "code": 200,
                        "message": "Detection success",
                        "save_path": res[0],
                        "process_time": res[1],
                        "file_path": f"/upload/{image_type}/{image_name}",
                    }
                )
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({"error": "Image not found"}), 404


def process_single_video_in_background(task_id: str, video_path: str, video_id: str):
    """后台处理单个视频的函数"""
    try:
        task_manager.update_task(task_id, TaskStatus.PROCESSING, progress=0)
        output_path, process_time = detect_video(video_path)
        # 文件名
        video_name = os.path.basename(os.path.normpath(output_path))
        result = {
            "message": "Detection success",
            "save_path": output_path,
            "process_time": process_time,
            "file_path": f"/upload/video/detected/{video_name}",
        }

        # 更新缓存
        video_cache.set(video_id, result)

        # 更新任务状态
        task_manager.update_task(
            task_id,
            TaskStatus.COMPLETED,
            result=result,
            progress=100,
        )
        logger.info(f"Video processing completed: {output_path}")
    except Exception as e:
        logger.error(f"Video processing failed: {str(e)}")
        task_manager.update_task(task_id, TaskStatus.FAILED, error=str(e), progress=0)


@detect_bp.route("/videos", methods=["POST"])
def detect_videos_route():
    """视频检测 - 异步处理版本"""
    video_id = request.json.get("video_id")
    if not video_id:
        return jsonify({"error": "No video ID provided"}), 400

    # 检查缓存
    cached_result = video_cache.get(video_id)
    if cached_result:
        return jsonify({"message": "Retrieved from cache", "result": cached_result})

    # 在上传目录中查找视频
    for ext in [".mp4", ".avi", ".mov"]:
        video_name = f"{video_id}{ext}"
        video_path = join(VIDEO_FOLDER, video_name)
        if exists(video_path):
            task_id = str(uuid.uuid4())
            task_manager.create_task(task_id)

            # 启动后台处理线程
            thread = Thread(
                target=process_single_video_in_background,
                args=(task_id, video_path, video_id),  # 添加video_id参数
                daemon=True,
            )
            thread.start()

            return jsonify({"message": "Processing started", "task_id": task_id})

    return jsonify({"error": "Video not found"}), 404


def process_video_in_background(task_id: str, detector: MultiModalVideoDetector):
    try:
        task_manager.update_task(task_id, TaskStatus.PROCESSING)
        detector.run()
        task_manager.update_task(
            task_id,
            TaskStatus.COMPLETED,
            result={"message": "Detection success", "save_path": detector.output_path},
        )
    except Exception as e:
        task_manager.update_task(task_id, TaskStatus.FAILED, error=str(e))


@detect_bp.route("/merge", methods=["POST"])
def merge_and_detect():
    ir_path = request.args.get("ir_path")
    tr_path = request.args.get("tr_path")
    model_path = request.args.get("model_path")
    conf_thres = float(request.args.get("conf_thres", 0.5))

    output_path = join(MERGE_FOLDER, "output_detection.mp4")

    # 创建任务ID
    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id)

    # 初始化视频检测器
    detector = MultiModalVideoDetector(
        ir_params={"video_path": ir_path},
        tr_params={"video_path": tr_path},
        model_path=model_path,
        output_path=output_path,
        conf_thres=conf_thres,
        show_preview=False,
    )

    # 启动后台处理线程
    thread = Thread(
        target=process_video_in_background, args=(task_id, detector), daemon=True
    )
    thread.start()

    # 立即返回任务ID
    return jsonify({"message": "Processing started", "task_id": task_id})


@detect_bp.route("/task_status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """获取任务处理状态"""
    status = task_manager.get_task_status(task_id)
    if status is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(status)
