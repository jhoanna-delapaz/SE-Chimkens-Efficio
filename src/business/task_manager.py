"""
Business logic for tasks. Delegates all DB access to DataHandler.
Keeps core logic DB-agnostic for easier testing and future upgrades.
"""

import logging
import sqlite3

from typing import List, Optional, Dict
from data.DataBaseHandler import DataHandler
from data.models import Task, Tag

# ISO 25010 Security: Centralized logging prevents internal exception details from leaking
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Avoid duplicating handlers if module is reloaded
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)


class TaskManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._data_handler = DataHandler(db_file)

    def _validate_task(self, task: Task) -> bool:
        """Validates task integrity to prevent malicious or malformed injections."""
        if not task.title or not task.title.strip():
            logger.warning(
                "Security/Validation Alert: Blocked attempt to save task with empty title."
            )
            return False
        if len(task.title) > 255:
            logger.warning(
                "Security/Validation Alert: Task title exceeds maximum allowed length."
            )
            return False

        # Basic anti-XSS heuristic
        malicious_patterns = ["<script>", "javascript:", "onload="]
        title_lower = task.title.lower()
        desc_lower = (task.description or "").lower()
        if any(p in title_lower or p in desc_lower for p in malicious_patterns):
            logger.warning(
                "Security/Validation Alert: Blocked potential script injection attempt."
            )
            return False

        return True

    def close(self) -> None:
        """Close DB connection. Call on shutdown to avoid file locks."""
        self._data_handler.close()

    def get_all_tags(self) -> List[Tag]:
        """Fetches all tags securely."""
        try:
            return self._data_handler.get_all_tags()
        except sqlite3.Error:
            logger.error("Database Query Error on Get All Tags")
            return []

    def add_tag(self, tag: Tag) -> int:
        """Saves a new tag to the database securely."""
        try:
            return self._data_handler.add_tag(tag)
        except sqlite3.Error:
            logger.error("Database Integrity Error on Add Tag")
            return -1

    def update_tag(self, tag: Tag) -> None:
        """Updates a tag securely."""
        try:
            self._data_handler.update_tag(tag)
        except sqlite3.Error:
            logger.error(f"Database Integrity Error on Update for Tag {tag.id}")

    def delete_tag(self, tag_id: int) -> None:
        """Deletes a tag securely."""
        try:
            self._data_handler.delete_tag(tag_id)
        except sqlite3.Error:
            logger.error(f"Database Integrity Error on Delete for Tag {tag_id}")

    def add_task(self, task: Task) -> int:
        """Saves a new task to the database safely after validation."""
        if not self._validate_task(task):
            return -1
        try:
            return self._data_handler.add_task(task)
        except sqlite3.Error:
            logger.error(
                "Database Integrity Error on Add (details masked for security)"
            )
            return -1

    def get_all_tasks(self, search_query: str = "") -> List[Task]:
        """Fetches all active tasks, optionally applying a keyword search."""
        try:
            return self._data_handler.get_all_tasks(search_query)
        except sqlite3.Error:
            logger.error(
                "Database Query Error on Get All (details masked for security)"
            )
            return []

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Fetches a specific task by ID securely."""
        try:
            return self._data_handler.get_task_by_id(task_id)
        except sqlite3.Error:
            logger.error(
                f"Database Query Error on Get ID for Task {task_id} (details masked)"
            )
            return None

    def delete_task(self, task_id: int) -> None:
        """Deletes a task safely."""
        try:
            self._data_handler.delete_task(task_id)
        except sqlite3.Error:
            logger.error(f"Database Integrity Error on Delete for Task {task_id}")

    def update_task_status(self, task_id: int, status: str) -> None:
        """Updates just the string status of a specific task."""
        try:
            self._data_handler.update_task_status(task_id, status)
        except sqlite3.Error:
            logger.error(
                f"Database Integrity Error on Update Status for Task {task_id}"
            )

    def update_task(self, task: Task) -> None:
        """Updates an entire task object securely after validation."""
        if not self._validate_task(task):
            return
        try:
            self._data_handler.update_task(task)
        except sqlite3.Error:
            logger.error(f"Database Integrity Error on Update for Task {task.id}")

    def get_deleted_tasks(self, search_query: str = "") -> List[Task]:
        """Fetches all tasks from the Trash securely, optionally applying a keyword search."""
        try:
            return self._data_handler.get_deleted_tasks(search_query)
        except sqlite3.Error:
            logger.error(
                "Database Query Error on Get Deleted (details masked for security)"
            )
            return []

    def restore_task(self, task_id: int) -> None:
        """Restores a task from the Trash securely."""
        try:
            self._data_handler.restore_task(task_id)
        except sqlite3.Error:
            logger.error(f"Database Integrity Error on Restore for Task {task_id}")

    def permanently_delete_task(self, task_id: int) -> None:
        """Permanently obliterates a task from storage."""
        try:
            self._data_handler.permanently_delete_task(task_id)
        except sqlite3.Error:
            logger.error(
                f"Database Integrity Error on Permanent Delete for Task {task_id}"
            )

    def get_task_stats(self, tasks_list: List[Task] = None) -> Dict:
        """Aggregates task counts for the analytics dashboard.

        If a list of tasks is provided, computes stats for that exact list
        (respecting UI filters). Otherwise, queries all active tasks.

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
        if tasks_list is None:
            try:
                tasks = self._data_handler.get_all_tasks()
            except sqlite3.Error:
                logger.error(
                    "Database Query Error on Get Stats (details masked for security)"
                )
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
        else:
            tasks = tasks_list

        from datetime import datetime

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

        now = datetime.now()

        for task in tasks:
            # Status aggregation
            if task.status in stats:
                stats[task.status] += 1

            # Priority aggregation
            if task.priority in stats:
                stats[task.priority] += 1

            # Overdue detection: non-completed tasks with a past due datetime
            if task.status != "Completed" and task.due_date:
                due_str = str(task.due_date).strip()
                try:
                    due = datetime.fromisoformat(due_str)
                    if due < now:
                        stats["overdue"] += 1
                except ValueError:
                    try:
                        # Legacy task with no time, just date
                        # We assume end of day for deadline
                        legacy_date = datetime.strptime(due_str, "%Y-%m-%d")
                        legacy_due = legacy_date.replace(hour=23, minute=59, second=59)
                        if legacy_due < now:
                            stats["overdue"] += 1
                    except ValueError:
                        pass  # Malformed string - silently skip

        return stats
