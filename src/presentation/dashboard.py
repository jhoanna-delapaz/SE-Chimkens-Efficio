
import os
from datetime import datetime
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QPushButton, QListWidget,
                               QListWidgetItem, QHBoxLayout, QLabel, QMenu, QMessageBox
                               )
from PySide6.QtCore import Qt

from business.task_manager import TaskManager
from data.models import Task
from presentation.add_task_dialog import AddTaskDialog
try:
    from config import get_default_db_path
except ImportError:
    get_default_db_path = None


class DashboardInterface(QWidget):
    def __init__(self, parent=None, db_file=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")

        # 1. First, check if a direct path was passed or parent has it
        if db_file is None and parent is not None:
            db_file = getattr(parent, "db_file", None)

        # 2. If STILL None, calculate the absolute path robustly
        if db_file is None:
            # Get the path to the 'src' directory
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(src_dir, "data")

            # CRITICAL FIX: Ensure the 'data' directory actually exists
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            db_file = os.path.join(data_dir, "efficio.db")

        self.db_file = db_file
        self.task_manager = TaskManager(self.db_file)

        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Region
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        # Add Task Button
        self.add_btn = QPushButton("+ New Task")
        self.add_btn.setStyleSheet("background-color: #007bff; color: white;"
                                   "padding: 8px 16px; border-radius: 4px;")
        self.add_btn.clicked.connect(self.show_add_task_dialog)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        # Task List
        layout.addWidget(QLabel("Your Tasks:"))
        self.task_list = QListWidget()
        self.task_list.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.task_list)

        # Enable Right-Click Context Menu
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)

    def load_tasks(self):
        # Disconnect momentarily to avoid triggering the signal while loading
        try:
            self.task_list.itemChanged.disconnect(self.on_item_changed)
        except TypeError:
            pass  # Signal not connected yet (first load)

        self.task_list.clear()
        tasks = self.task_manager.get_all_tasks()

        for task in tasks:
            due_display = task.due_date if task.due_date else ""
            item_text = f"[{task.priority}] {task.title} - {task.status} (Due: {due_display})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, task.id)

            # Add Checkbox
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            if task.status == "Completed":
                item.setCheckState(Qt.CheckState.Checked)
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self.task_list.addItem(item)

        # Reconnect signal
        self.task_list.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if not task_id:
            return

        if item.checkState() == Qt.CheckState.Checked:
            new_status = "Completed"
            font = item.font()
            font.setStrikeOut(True)
            item.setFont(font)
        else:
            new_status = "Pending"
            font = item.font()
            font.setStrikeOut(False)
            item.setFont(font)

        # Update DB
        self.task_manager.update_task_status(task_id, new_status)

    def show_add_task_dialog(self):
        """
        Opens the dialog to create a new task. Provides a success notification
        upon successfully saving the task to the database.
        """
        dialog = AddTaskDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # Create Task Object
            new_task = Task(
                id=None,
                title=data['title'],
                description=data['description'],
                status=data['status'],
                created_at=datetime.now(),
                due_date=data['due_date'],
                priority=data['priority']
            )

            # Save to DB safely
            result_id = self.task_manager.add_task(new_task)

            if result_id != -1:
                # ISO 25010 Usability: Visual confirmation of success
                QMessageBox.information(
                    self, "Success", f"Task '{new_task.title}' was successfully created!"
                )
                self.load_tasks()
            else:
                QMessageBox.critical(
                    self, "Error", "A database error occurred while saving the task."
                )

    def show_context_menu(self, pos):
        item = self.task_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            edit_action = menu.addAction("Edit Task")
            delete_action = menu.addAction("Delete Task")

            action = menu.exec(self.task_list.mapToGlobal(pos))

            if action == delete_action:
                self.delete_current_task(item)
            elif action == edit_action:
                self.edit_current_task(item)

    def delete_current_task(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            confirm = QMessageBox.question(self, "Confirm Delete",
                                           "Are you sure you want to delete this task?",
                                           QMessageBox.StandardButton.Yes
                                           | QMessageBox.StandardButton.No)

            if confirm == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task_id)
                self.load_tasks()

    def edit_current_task(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            # Fetch existing task data
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                dialog = AddTaskDialog(self, task=task)
                if dialog.exec():
                    data = dialog.get_data()

                    # Update Task Object
                    updated_task = Task(
                        id=task_id,
                        title=data['title'],
                        description=data['description'],
                        status=data['status'],
                        created_at=task.created_at,
                        due_date=data['due_date'],
                        priority=data['priority']
                    )

                    self.task_manager.update_task(updated_task)
                    self.load_tasks()
