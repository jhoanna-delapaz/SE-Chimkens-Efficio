"""
Business logic for tasks. Delegates all DB access to DataHandler.
Keeps core logic DB-agnostic for easier testing and future upgrades.
"""
from data.models import Task
from data.DataBaseHandler import DataHandler


class TaskManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._data_handler = DataHandler(db_file)

    def close(self) -> None:
        """Close DB connection. Call on shutdown to avoid file locks."""
        self._data_handler.close()

    def add_task(self, task: Task) -> int:
        return self._data_handler.add_task(task)

    def get_all_tasks(self) -> list:
        return self._data_handler.get_all_tasks()

    def get_task_by_id(self, task_id: int):
        return self._data_handler.get_task_by_id(task_id)

    def delete_task(self, task_id: int) -> None:
        self._data_handler.delete_task(task_id)

    def update_task_status(self, task_id: int, status: str) -> None:
        self._data_handler.update_task_status(task_id, status)

    def update_task(self, task: Task) -> None:
        self._data_handler.update_task(task)