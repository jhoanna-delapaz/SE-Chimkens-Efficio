"""
Business logic for tasks. Delegates all DB access to DataHandler.
Keeps core logic DB-agnostic for easier testing and future upgrades.
"""

import sqlite3
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
        """Saves a new task to the database safely."""
        try:
            return self._data_handler.add_task(task)
        except sqlite3.Error as e:
            print(f"Database Error on Add: {e}")
            return -1

    def get_all_tasks(self, search_query: str = "") -> list:
        """Fetches all active tasks, optionally applying a keyword search."""
        try:
            return self._data_handler.get_all_tasks(search_query)
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return []

    def get_task_by_id(self, task_id: int):
        """Fetches a specific task by ID securely."""
        try:
            return self._data_handler.get_task_by_id(task_id)
        except sqlite3.Error as e:
            print(f"Database Error on Get ID: {e}")
            return None

    def delete_task(self, task_id: int) -> None:
        """Deletes a task safely."""
        try:
            self._data_handler.delete_task(task_id)
        except sqlite3.Error as e:
            print(f"Database Error on Delete: {e}")

    def update_task_status(self, task_id: int, status: str) -> None:
        """Updates just the string status of a specific task."""
        try:
            self._data_handler.update_task_status(task_id, status)
        except sqlite3.Error as e:
            print(f"Database Error on Update Status: {e}")

    def update_task(self, task: Task) -> None:
        """Updates an entire task object securely."""
        try:
            self._data_handler.update_task(task)
        except sqlite3.Error as e:
            print(f"Database Error on Update: {e}")

    def get_deleted_tasks(self, search_query: str = "") -> list:
        """Fetches all tasks from the Trash securely, optionally applying a keyword search."""
        try:
            return self._data_handler.get_deleted_tasks(search_query)
        except sqlite3.Error as e:
            print(f"Database Error on Get Deleted: {e}")
            return []

    def restore_task(self, task_id: int) -> None:
        """Restores a task from the Trash securely."""
        try:
            self._data_handler.restore_task(task_id)
        except sqlite3.Error as e:
            print(f"Database Error on Restore: {e}")

    def permanently_delete_task(self, task_id: int) -> None:
        """Permanently obliterates a task from storage."""
        try:
            self._data_handler.permanently_delete_task(task_id)
        except sqlite3.Error as e:
            print(f"Database Error on Permanent Delete: {e}")

    def get_task_stats(self) -> dict:
        """Aggregates task counts for the analytics dashboard.

        Queries all active (non-deleted) tasks and computes counts grouped
        by status and priority, plus the number of tasks whose due date has
        already passed. Keeps the analytics widget completely DB-agnostic —
        it only ever consumes this plain dictionary.

        Returns:
            dict: A flat mapping of metric names to integer counts, e.g.::

                {
                    "Pending": 3,
                    "In Progress": 1,
                    "Completed": 5,
                    "Low": 2,
                    "Medium": 3,
                    "High": 3,
                    "Critical": 1,
                    "overdue": 2,
                    "total": 9,
                }
        """
        try:
            tasks = self._data_handler.get_all_tasks()
        except sqlite3.Error as e:
            print(f"Database Error on Get Stats: {e}")
            return {
                "Pending": 0,
                "In Progress": 0,
                "Completed": 0,
                "Low": 0,
                "Medium": 0,
                "High": 0,
                "Critical": 0,
                "overdue": 0,
                "total": 0,
            }

        from datetime import date

        stats: dict = {
            "Pending": 0,
            "In Progress": 0,
            "Completed": 0,
            "Low": 0,
            "Medium": 0,
            "High": 0,
            "Critical": 0,
            "overdue": 0,
            "total": len(tasks),
        }

        today = date.today()

        for task in tasks:
            # Status aggregation
            if task.status in stats:
                stats[task.status] += 1

            # Priority aggregation
            if task.priority in stats:
                stats[task.priority] += 1

            # Overdue detection: non-completed tasks with a past due date
            if task.status != "Completed" and task.due_date:
                try:
                    due = date.fromisoformat(str(task.due_date).strip())
                    if due < today:
                        stats["overdue"] += 1
                except ValueError:
                    pass  # Malformed date — silently skip

        return stats
