from flask import Blueprint, jsonify
from src.task_manager import task_manager

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
            "progress": 0-100  # 处理进度(百分比)
        }
    """
    status = task_manager.get_task_status(task_id)
    if status is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(status)


@task_bp.route("/list", methods=["GET"])
def list_tasks():
    """
    获取所有任务列表

    Returns:
        JSON Response:
        {
            "tasks": [
                {
                    "task_id": "xxx",
                    "status": "pending|processing|completed|failed",
                    "progress": 0-100
                },
                ...
            ]
        }
    """
    tasks = []
    for task_id, task_info in task_manager.tasks.items():
        tasks.append(
            {
                "task_id": task_id,
                "status": task_info["status"].value,
                "progress": task_info.get("progress", 0),
            }
        )

    return jsonify({"tasks": tasks})


@task_bp.route("/result/<task_id>", methods=["GET"])
def get_task_result(task_id):
    """
    获取任务结果

    Args:
        task_id (str): 任务ID

    Returns:
        JSON Response:
        {
            "status": "pending|processing|completed|failed",
            "result": {...} | null,  # 当任务完成时返回结果
            "error": "错误信息" | null,  # 当任务失败时返回错误信息
            "progress": 0-100  # 处理进度(百分比)
        }
    """
    status = task_manager.get_task_status(task_id)
    if status is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(status)
