
import os
from datetime import datetime
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QPushButton, QListWidget, 
                             QListWidgetItem, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt

from business.task_manager import TaskManager
from data.models import Task
from presentation.add_task_dialog import AddTaskDialog

class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        # Initialize Task Manager
        db_path = os.path.join(os.getcwd(), "src", "data", "efficio.db")
        self.task_manager = TaskManager(db_path)

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
        self.add_btn.setStyleSheet("background-color: #007bff; color: white; padding: 8px 16px; border-radius: 4px;")
        self.add_btn.clicked.connect(self.show_add_task_dialog)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)

        # Task List
        layout.addWidget(QLabel("Your Tasks:"))
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        # Enable Right-Click Context Menu
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)

    def load_tasks(self):
        self.task_list.clear()
        tasks = self.task_manager.get_all_tasks()
        for task in tasks:
            item_text = f"[{task.priority}] {task.title} - {task.status} (Due: {task.due_date})"
            item = QListWidgetItem(item_text)
            # Store the ID in the item so we can retrieve it later
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.task_list.addItem(item)

    def show_add_task_dialog(self):
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
            
            # Save to DB
            self.task_manager.add_task(new_task)
            
            # Refresh List
            self.load_tasks()
            
    def show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        
        item = self.task_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            delete_action = menu.addAction("Delete Task")
            action = menu.exec(self.task_list.mapToGlobal(pos))
            
            if action == delete_action:
                self.delete_current_task(item)

    def delete_current_task(self, item):
        # Retrieve the ID we stored earlier
        task_id = item.data(Qt.ItemDataRole.UserRole)
        
        if task_id:
            from PySide6.QtWidgets import QMessageBox
            confirm = QMessageBox.question(self, "Confirm Delete", 
                                         "Are you sure you want to delete this task?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task_id)
                self.load_tasks() # Refresh list