from datetime import datetime
from typing import List

from data.models import Task
from utils.constants import PRIORITY_MAP


class TaskSorter:
    """
    Utility class for sorting tasks based on different criteria.
    ISO 25010: Improves Reusability and Testability.
    """

    @staticmethod
    def get_date_key(task: Task):
        if not task.due_date:
            return datetime.max
        due_str = str(task.due_date).strip()
        try:
            return datetime.fromisoformat(due_str)
        except ValueError:
            try:
                # Legacy date-only: assume end of day
                return datetime.strptime(due_str, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
            except ValueError:
                return datetime.max

    @classmethod
    def sort(
        cls, tasks: List[Task], criteria: str, reverse: bool = False
    ) -> List[Task]:
        """
        Sorts tasks based on the provided criteria.
        """
        if criteria == "Due Date":
            return sorted(tasks, key=cls.get_date_key, reverse=reverse)
        elif criteria == "Priority":
            return sorted(
                tasks, key=lambda t: PRIORITY_MAP.get(t.priority, 99), reverse=reverse
            )

        return tasks

    @staticmethod
    def format_due_countdown(due_date_str, status: str = "") -> str | None:
        """
        Returns a short human-readable countdown tooltip for a task's due date.
        """
        if not due_date_str or status == "Completed":
            return None

        due_str = str(due_date_str).strip()
        try:
            due_dt = datetime.fromisoformat(due_str)
        except ValueError:
            try:
                # Handle legacy date strings
                due_dt = datetime.strptime(due_str, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
            except ValueError:
                return None

        total_seconds = (due_dt - datetime.now()).total_seconds()

        if total_seconds < 0:
            abs_s = abs(total_seconds)
            if abs_s < 3600:
                return f"⚠️ Overdue by {int(abs_s // 60)}m"
            elif abs_s < 86400:
                return f"⚠️ Overdue by {int(abs_s // 3600)}h"
            else:
                return f"⚠️ Overdue by {int(abs_s // 86400)}d"
        elif total_seconds < 3600:
            return f"⏰ Due in {max(1, int(total_seconds // 60))}m"
        elif total_seconds < 86400:
            return f"⏰ Due in {int(total_seconds // 3600)}h"
        else:
            days = int(total_seconds // 86400)
            if days <= 3:
                return f"⏰ Due in {days}d"
            return f"📅 Due in {days}d"
