
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QComboBox, QDialogButtonBox, QDateEdit, QMessageBox)
from PySide6.QtCore import QDate, Qt

class AddTaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "Add New Task")
        self.setMinimumWidth(400)
        self.task = task 

        layout = QVBoxLayout(self)

        # Title
        layout.addWidget(QLabel("Title (Required):"))
        self.title_input = QLineEdit()
        if task: self.title_input.setText(task.title)
        layout.addWidget(self.title_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        if task: self.desc_input.setText(task.description)
        layout.addWidget(self.desc_input)

        # Due Date
        layout.addWidget(QLabel("Due Date:"))
        self.date_input = QDateEdit()
        if task and task.due_date:
            self.date_input.setDate(QDate.fromString(task.due_date, Qt.DateFormat.ISODate))
        else:
            self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        layout.addWidget(self.date_input)

        # Priority
        layout.addWidget(QLabel("Priority:"))
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High", "Critical"])
        if task and task.priority:
            index = self.priority_input.findText(task.priority)
            if index >= 0: self.priority_input.setCurrentIndex(index)
        layout.addWidget(self.priority_input)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required!")
            return
        self.accept()

    def get_data(self):
        """Returns a dictionary of the task data"""
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self.date_input.date().toString(Qt.DateFormat.ISODate),
            "priority": self.priority_input.currentText(),
            "status": self.task.status if self.task else "Pending" 
        }
