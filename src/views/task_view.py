from flask import Blueprint, jsonify
from src.task_manager import task_manager, TaskStatus
from src.config import get_logger


logger = get_logger()

task_bp = Blueprint("task", __name__, url_prefix="/task")


@task_bp.route("/status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """
    获取任务状态

    Args:
        task_id (str): 任务ID

    Returns:
        JSON Response:
        {
            "status": "pending|processing|completed|failed",
            "result": {...} | null,  # 当任务完成时返回结果
            "error": "错误信息" | null,  # 当任务失败时返回错误信息
        }
    """
    status = task_manager.get_task_status(task_id)
    if status is None:
        return jsonify({"error": "Task not found"}), 404

    # 创建可序列化的响应数据
    response_data = {
        "status": status["status"].value,  # 将枚举转换为字符串
        "result": status.get("result"),
        "error": status.get("error"),
    }

    return jsonify(response_data)


@task_bp.route("/list", methods=["GET"])
def list_tasks():
    """获取所有任务列表"""
    tasks = []
    for task_id, task_info in task_manager.tasks.items():
        task_data = {
            "task_id": task_id,
            "status": task_info["status"].value,
            "start_time": task_info.get("start_time"),
            "has_result": task_info.get("result") is not None,
            "has_error": task_info.get("error") is not None,
        }
        tasks.append(task_data)

    logger.info(f"Current tasks: {len(tasks)}")
    return jsonify({"tasks": tasks})


@task_bp.route("/result/<task_id>", methods=["GET"])
def get_task_result(task_id):
    """
    获取任务的处理结果

    Args:
        task_id (str): 任务ID

    Returns:
        JSON Response:
        成功时:
        {
            "result": {
                "message": "Detection success",
                "save_path": "path/to/result",
                "process_time": 1.23,
                "detections": [...]
            }
        }

        失败时:
        {
            "error": "错误信息"
        }, 404/400
    """
    # 获取任务状态
    task_info = task_manager.get_task_status(task_id)

    # 检查任务是否存在
    if task_info is None:
        return jsonify({"error": "Task not found"}), 404

    # 检查任务状态
    if task_info["status"] == TaskStatus.FAILED:
        return jsonify({"error": task_info["error"]}), 400

    if task_info["status"] != TaskStatus.COMPLETED:
        return jsonify(
            {
                "error": "Task is not completed yet",
                "status": task_info["status"].value,
            }
        ), 400

    # 返回处理结果
    return jsonify({"result": task_info["result"]})
