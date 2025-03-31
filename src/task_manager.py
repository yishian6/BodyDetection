from enum import Enum
from typing import Dict, Any
import time
from src.config import get_logger


logger = get_logger()


class TaskStatus(Enum):
    PENDING = "pending"  # 任务等待中
    PROCESSING = "processing"  # 任务处理中
    COMPLETED = "completed"  # 任务完成
    FAILED = "failed"  # 任务失败


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def create_task(self, task_id: str) -> None:
        self.tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None,
            "progress": 0,
            "start_time": time.time(),
        }
        logger.info(f"Task created: {task_id}")

    def update_task(
        self, task_id: str, status: TaskStatus, result=None, error=None, progress=None
    ) -> None:
        if task_id in self.tasks:
            if status:
                self.tasks[task_id]["status"] = status
            if result is not None:
                self.tasks[task_id]["result"] = result
            if error is not None:
                self.tasks[task_id]["error"] = error
            if progress is not None:
                self.tasks[task_id]["progress"] = progress
            logger.info(f"Task updated: {task_id}, status: {status.value}")
        else:
            logger.error(f"Task not found: {task_id}")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if task:
            logger.info(
                f"Getting task status: {task_id}, status: {task['status'].value}"
            )
        else:
            logger.warning(f"Task not found when getting status: {task_id}")
        return task


task_manager = TaskManager()
