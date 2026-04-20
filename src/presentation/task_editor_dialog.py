from PySide6.QtCore import QDate, QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class TaskEditorDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "Add New Task")
        self.setMinimumWidth(400)
        self.task = task

        layout = QVBoxLayout(self)

        # Initialize floating toast (does not get added to layout)
        self.toast = ToastNotification(self)

        # Title
        layout.addWidget(QLabel("Title (Required):"))
        self.title_input = QLineEdit()
        if task:
            self.title_input.setText(task.title)
        layout.addWidget(self.title_input)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        if task:
            self.desc_input.setText(task.description or "")
        layout.addWidget(self.desc_input)

        # Due Date
        layout.addWidget(QLabel("Due Date:"))
        self.date_input = QDateEdit()
        if task and task.due_date:
            due_str = str(task.due_date).strip()
            if due_str:
                parsed = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                if parsed.isValid():
                    self.date_input.setDate(parsed)
                else:
                    self.date_input.setDate(QDate.currentDate())
            else:
                self.date_input.setDate(QDate.currentDate())
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
            if index >= 0:
                self.priority_input.setCurrentIndex(index)
        layout.addWidget(self.priority_input)

        # Color
        layout.addWidget(QLabel("Task Color:"))
        self.color_combo = QComboBox()
        # Original Soft Themes
        self.color_combo.addItem("🌊 Ocean Peach", "#6579BE")
        self.color_combo.addItem("🏜️ Warm Sand", "#E9DFD8")
        self.color_combo.addItem("🔥 Vibrant Orange", "#F54800")
        self.color_combo.addItem("🍦 Soft Cream", "#FDF1F5")
        self.color_combo.addItem("🪵 Earthy Brown", "#8A6729")
        self.color_combo.addItem("🪨 Muted Stone", "#ECE7E2")
        self.color_combo.addItem("🐋 Deep Ocean", "#19485F")
        self.color_combo.addItem("🌲 Forest Pink", "#285B23")
        self.color_combo.addItem("🥀 Dusty Rose", "#92736C")

        # New High-Contrast & Solid Themes
        self.color_combo.addItem("🌑 Pitch Black (White Text)", "#000000")
        self.color_combo.addItem("🌕 Pure White (Black Text)", "#FFFFFF")

        # We use slight micro-shades of White/Black to keep Python Dictionaries happy
        self.color_combo.addItem("🌫️ Frost White (Gray Text)", "#FFFFFE")
        self.color_combo.addItem("☁️ Light Gray (White Text)", "#DDDDDD")
        self.color_combo.addItem("🥶 Ice White (Blue Text)", "#FFFFFD")
        self.color_combo.addItem("🚨 Hacker Black (Red Text)", "#000001")
        self.color_combo.addItem("📟 Matrix Black (Green Text)", "#000002")

        if task and hasattr(task, "color") and task.color:
            index = self.color_combo.findData(task.color)
            if index >= 0:
                self.color_combo.setCurrentIndex(index)
        layout.addWidget(self.color_combo)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        title = self.title_input.text().strip()

        if not title:
            self.toast.show_toast("Title is required!")
            return

        # --- PAST DUE DATE VALIDATION ---
        selected_date = self.date_input.date()
        current_date = QDate.currentDate()

        # Check if the currently selected date is in the past
        if selected_date < current_date:
            original_date = None

            # Identify if we are editing an existing task, and if so, capture its original date
            if self.task and self.task.due_date:
                due_str = str(self.task.due_date).strip()
                if due_str:
                    parsed = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                    if parsed.isValid():
                        original_date = parsed

            # If it's a NEW task, OR they changed the date to a NEW past date, block the save
            if not original_date or selected_date != original_date:
                self.toast.show_toast("Due Date cannot be in the past!")
                return
        # --------------------------------

        self.accept()

    def get_data(self):
        """Returns a dictionary of the task data"""
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self.date_input.date().toString(Qt.DateFormat.ISODate),
            "priority": self.priority_input.currentText(),
            "status": self.task.status if self.task else "Pending",
            "color": self.color_combo.currentData(),  # Extract the hidden Hex Code
        }


class ToastNotification(QLabel):
    """A floating, animated notification overlay."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                background-color: #2F3239;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

        # Premium Shadow Hook
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def show_toast(self, message, duration_ms=3000):
        self.setText(message)
        self.adjustSize()

        # Mathematical absolute positioning (Top-Center)
        parent_rect = self.parent().rect()
        target_x = (parent_rect.width() - self.width()) // 2
        target_y = 20  # Hovering 20px down from the roof
        start_y = -self.height() - 20  # Offscreen

        self.setGeometry(target_x, start_y, self.width(), self.height())
        self.show()
        self.raise_()

        # Slide Down Animation Engine
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(400)
        self.anim.setStartValue(QPoint(target_x, start_y))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.setEasingCurve(QEasingCurve.OutBack)  # Bouncy effect!
        self.anim.start()

        # Start timer to auto-hide
        QTimer.singleShot(duration_ms, self.hide_toast)

    def hide_toast(self):
        # Slide Up Animation
        target_x = self.x()
        end_y = -self.height() - 20

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(target_x, end_y))
        self.anim.setEasingCurve(QEasingCurve.InBack)
        self.anim.finished.connect(self.hide)
        self.anim.start()
