from enum import Enum
from typing import Dict, Any
import time


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

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return self.tasks.get(task_id)


task_manager = TaskManager()
