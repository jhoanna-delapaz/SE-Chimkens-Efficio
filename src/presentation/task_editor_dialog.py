import os
from PySide6.QtCore import (
    QDate,
    QDateTime,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTime,
    QTimer,
)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QScrollArea,
    QFrame,
    QFileDialog,
)
from data.models import TaskAttachment
from presentation.components.tag_select_menu import TagSelectMenu

_DIALOG_STYLE = """
    QDialog {
        background-color: #1E2328;
    }
    QLabel {
        color: #FFFFFF;
        font-weight: bold;
        font-size: 13px;
    }
    QLineEdit, QTextEdit, QDateEdit, QComboBox {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
    }
    QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus {
        border: 1px solid #6579BE;
        background-color: rgba(255, 255, 255, 0.08);
    }
    QLineEdit:hover, QTextEdit:hover, QDateEdit:hover, QComboBox:hover {
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    /* Disable calendar popup weird styling */
    QCalendarWidget QWidget {
        alternate-background-color: #2F3239;
    }
"""


class TaskEditorDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Task" if task else "Create New Task")
        self.setMinimumWidth(500)
        self.setStyleSheet(_DIALOG_STYLE)
        self.task = task

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Initialize floating toast (does not get added to layout)
        self.toast = ToastNotification(self)

        # 1. Header
        header_lbl = QLabel("✏️ Edit Task" if task else "✨ Create New Task")
        header_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        layout.addWidget(header_lbl)

        # 2. Main Inputs (Title & Description)
        layout.addWidget(QLabel("Task Title (Required)"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Prepare Q3 Marketing Report")
        if task:
            self.title_input.setText(task.title)
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Task Description"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Add any relevant context or notes here...")
        self.desc_input.setMaximumHeight(80)
        if task:
            self.desc_input.setText(task.description or "")
        layout.addWidget(self.desc_input)

        # 3. Metadata Grid (2x2)
        grid = QGridLayout()
        grid.setSpacing(15)

        # Row 0, Col 0: Due Date & Time
        grid.addWidget(QLabel("Due Date & Time"), 0, 0)

        datetime_layout = QHBoxLayout()
        datetime_layout.setSpacing(5)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)

        self.time_input = QComboBox()
        # Generate 30-minute intervals
        times = []
        for h in range(24):
            for m in (0, 30):
                qtime = QTime(h, m)
                times.append(qtime.toString("hh:mm AP"))
        self.time_input.addItems(times)

        if task and task.due_date:
            due_str = str(task.due_date).strip()
            if due_str:
                parsed_dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
                if parsed_dt.isValid():
                    self.date_input.setDate(parsed_dt.date())
                    # Snap to nearest 30 mins or just match exact if exists
                    time_str = parsed_dt.time().toString("hh:mm AP")
                    idx = self.time_input.findText(time_str)
                    if idx >= 0:
                        self.time_input.setCurrentIndex(idx)
                    else:
                        # If weird time, just append it
                        self.time_input.addItem(time_str)
                        self.time_input.setCurrentIndex(self.time_input.count() - 1)
                else:
                    parsed_d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                    if parsed_d.isValid():
                        self.date_input.setDate(parsed_d)
                        self.time_input.setCurrentText("11:30 PM")
                    else:
                        self.date_input.setDate(QDate.currentDate())
                        self.time_input.setCurrentText("11:30 PM")
            else:
                self.date_input.setDate(QDate.currentDate())
                self.time_input.setCurrentText("11:30 PM")
        else:
            self.date_input.setDate(QDate.currentDate())
            self.time_input.setCurrentText("11:30 PM")

        datetime_layout.addWidget(self.date_input, stretch=2)
        datetime_layout.addWidget(self.time_input, stretch=1)
        grid.addLayout(datetime_layout, 1, 0)

        # Row 0, Col 1: Priority
        grid.addWidget(QLabel("Priority"), 0, 1)
        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High", "Critical"])
        if task and task.priority:
            index = self.priority_input.findText(task.priority)
            if index >= 0:
                self.priority_input.setCurrentIndex(index)
        grid.addWidget(self.priority_input, 1, 1)

        # Row 2, Col 0: Status
        grid.addWidget(QLabel("Status"), 2, 0)
        self.status_input = QComboBox()
        self.status_input.addItems(["Pending", "In Progress", "Completed"])
        if task and hasattr(task, "status"):
            index = self.status_input.findText(task.status)
            if index >= 0:
                self.status_input.setCurrentIndex(index)
        grid.addWidget(self.status_input, 3, 0)

        # Row 2, Col 1: Color Theme
        grid.addWidget(QLabel("Theme Color"), 2, 1)
        self.color_combo = QComboBox()
        self.color_combo.addItem("🌊 Ocean Peach", "#6579BE")
        self.color_combo.addItem("🏜️ Warm Sand", "#E9DFD8")
        self.color_combo.addItem("🔥 Vibrant Orange", "#F54800")
        self.color_combo.addItem("🍦 Soft Cream", "#FDF1F5")
        self.color_combo.addItem("🪵 Earthy Brown", "#8A6729")
        self.color_combo.addItem("🪨 Muted Stone", "#ECE7E2")
        self.color_combo.addItem("🐋 Deep Ocean", "#19485F")
        self.color_combo.addItem("🌲 Forest Pink", "#285B23")
        self.color_combo.addItem("🥀 Dusty Rose", "#92736C")
        self.color_combo.addItem("🌑 Pitch Black (White Text)", "#000000")
        self.color_combo.addItem("🌕 Pure White (Black Text)", "#FFFFFF")
        self.color_combo.addItem("🌫️ Frost White (Gray Text)", "#FFFFFE")
        self.color_combo.addItem("☁️ Light Gray (White Text)", "#DDDDDD")
        self.color_combo.addItem("🥶 Ice White (Blue Text)", "#FFFFFD")
        self.color_combo.addItem("🚨 Hacker Black (Red Text)", "#000001")
        self.color_combo.addItem("📟 Matrix Black (Green Text)", "#000002")

        if task and hasattr(task, "color") and task.color:
            index = self.color_combo.findData(task.color)
            if index >= 0:
                self.color_combo.setCurrentIndex(index)
        grid.addWidget(self.color_combo, 3, 1)

        layout.addLayout(grid)
        layout.addSpacing(10)

        # 3.5 Tags Section
        layout.addWidget(QLabel("Tags (Select up to 5)"))

        # Tags control row (Button)
        self.tags_control_layout = QHBoxLayout()
        self.tags_select_btn = QPushButton("🏷️ Select Tags")
        self.tags_select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tags_select_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1); color: white; border-radius: 6px; padding: 6px 12px; border: 1px solid rgba(255,255,255,0.2); font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); border: 1px solid #6579BE; }
        """)
        self.tags_select_btn.clicked.connect(self._show_tag_menu)
        self.tags_control_layout.addWidget(self.tags_select_btn)
        self.tags_control_layout.addStretch()
        layout.addLayout(self.tags_control_layout)

        # Tags display container
        self.tags_container = QWidget()
        self.tags_container.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.tags_container.setMinimumHeight(40)
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(8)
        self.tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.tags_container)

        self.selected_tags = []
        if task and hasattr(task, "tags") and task.tags:
            self.selected_tags = list(task.tags)

        self._render_selected_tags()

        layout.addSpacing(10)

        # 3.6 Attachments Section
        layout.addWidget(QLabel("Attachments (Optional, max 5)"))

        self.attach_control_layout = QHBoxLayout()
        self.attach_btn = QPushButton("📎 Add Images")
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1); color: white; border-radius: 6px; padding: 6px 12px; border: 1px solid rgba(255,255,255,0.2); font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); border: 1px solid #6579BE; }
        """)
        self.attach_btn.clicked.connect(self._select_attachments)
        self.attach_control_layout.addWidget(self.attach_btn)
        self.attach_control_layout.addStretch()
        layout.addLayout(self.attach_control_layout)

        # Horizontal Scroll Area for thumbnails
        self.attach_scroll = QScrollArea()
        self.attach_scroll.setWidgetResizable(True)
        self.attach_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.attach_scroll.setStyleSheet("background-color: transparent;")
        self.attach_scroll.setFixedHeight(100)

        self.attach_container = QWidget()
        self.attach_layout = QHBoxLayout(self.attach_container)
        self.attach_layout.setContentsMargins(0, 5, 0, 5)
        self.attach_layout.setSpacing(10)
        self.attach_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.attach_scroll.setWidget(self.attach_container)
        layout.addWidget(self.attach_scroll)

        self.attachments = []
        if task and hasattr(task, "attachments") and task.attachments:
            self.attachments = list(task.attachments)

        self._render_attachments()

        # Enable Drag & Drop
        self.setAcceptDrops(True)

        layout.addSpacing(10)

        # 4. Action Footer (Save / Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #A0A0A0; font-weight: bold; padding: 10px 20px; border-radius: 6px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.05); color: white; }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save Task")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(40, 91, 35, 0.85);
                color: white; font-weight: bold; padding: 10px 24px; border-radius: 6px;
            }
            QPushButton:hover { background-color: rgba(40, 91, 35, 1.0); }
        """)
        self.save_btn.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _show_tag_menu(self):
        parent_dash = self.parent()
        all_tags = []
        if hasattr(parent_dash, "task_manager"):
            all_tags = parent_dash.task_manager.get_all_tags()

        menu = TagSelectMenu(all_tags, self.selected_tags, self)
        menu.tags_changed.connect(self._on_tags_changed)

        # Show menu below the button
        pos = self.tags_select_btn.mapToGlobal(QPoint(0, self.tags_select_btn.height()))
        menu.exec(pos)

    def _on_tags_changed(self, new_tags):
        if len(new_tags) > 5:
            self.toast.show_toast("Maximum 5 tags allowed! Only saving first 5.")
            self.selected_tags = new_tags[:5]
        else:
            self.selected_tags = new_tags
        self._render_selected_tags()

    def _render_selected_tags(self):
        # Clear existing
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tag in self.selected_tags:
            btn = QPushButton(tag.name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Smart Contrast for text
            text_color = "#FFFFFF"
            try:
                hex_c = tag.color.lstrip("#")
                r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
                luma = 0.299 * r + 0.587 * g + 0.114 * b
                text_color = "#000000" if luma > 160 else "#FFFFFF"
            except Exception:
                pass

            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {tag.color}; color: {text_color}; border-radius: 4px; padding: 4px 10px; border: none; font-weight: bold; font-size: 11px; }}
                QPushButton:hover {{ opacity: 0.8; }}
            """)
            btn.clicked.connect(lambda checked, t=tag: self._remove_tag(t))
            self.tags_layout.addWidget(btn)

        self.tags_layout.addStretch()

    def _remove_tag(self, tag):
        self.selected_tags = [t for t in self.selected_tags if t.id != tag.id]
        self._render_selected_tags()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls]
        self._add_files(files)

    def _select_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files", "", "Files (*.png *.jpg *.jpeg *.bmp *.gif *.pdf)"
        )
        if files:
            self._add_files(files)

    def _add_files(self, file_paths):
        parent_dash = self.parent()
        if not hasattr(parent_dash, "task_manager"):
            return

        SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".pdf"}
        for path in file_paths:
            if len(self.attachments) >= 5:
                self.toast.show_toast("Maximum 5 attachments allowed!")
                break

            ext = os.path.splitext(path)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                self.toast.show_toast(f"Unsupported type: {ext}")
                continue

            # Save file via task manager
            result = parent_dash.task_manager.save_attachment(path)
            if result:
                new_path, original_name = result
                self.attachments.append(
                    TaskAttachment(
                        id=None,
                        task_id=self.task.id if self.task else -1,
                        file_path=new_path,
                        file_name=original_name,
                    )
                )
            else:
                self.toast.show_toast(f"Failed to add image: {os.path.basename(path)}")

        self._render_attachments()

    def _render_attachments(self):
        # Clear existing
        while self.attach_layout.count():
            item = self.attach_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for att in self.attachments:
            thumb_widget = QWidget()
            thumb_widget.setFixedSize(80, 80)
            thumb_widget.setStyleSheet("""
                QWidget { background-color: rgba(255,255,255,0.05); border-radius: 6px; }
            """)
            thumb_layout = QVBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(0, 0, 0, 0)

            img_label = QLabel()
            img_label.setFixedSize(80, 80)
            img_label.setScaledContents(True)
            if att.file_path.lower().endswith(".pdf"):
                img_label.setText("PDF")
                img_label.setStyleSheet("""
                    QLabel {
                        background-color: #EE2222; color: white; border-radius: 6px;
                        font-weight: bold; font-size: 16px; border: 1px solid rgba(255,255,255,0.2);
                    }
                """)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                pixmap = QPixmap(att.file_path)
                if not pixmap.isNull():
                    img_label.setPixmap(
                        pixmap.scaled(
                            80, 80, Qt.AspectRatioMode.KeepAspectRatioByExpanding
                        )
                    )
                else:
                    img_label.setText("🖼️")
                    img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_layout.addWidget(img_label)

            # Close button overlay
            del_btn = QPushButton("✕", thumb_widget)
            del_btn.setFixedSize(20, 20)
            del_btn.move(60, 0)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0,0,0,0.6); color: white; border-radius: 10px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #F54800; }
            """)
            del_btn.clicked.connect(lambda checked, a=att: self._remove_attachment(a))

            self.attach_layout.addWidget(thumb_widget)

        self.attach_layout.addStretch()

    def _remove_attachment(self, attachment):
        self.attachments.remove(attachment)
        # Note: We don't delete the physical file yet,
        # in case the user cancels the dialog.
        # Or we could, but then we'd have to manage undo.
        # Requirement says "remove or replace", so this is fine for now.
        self._render_attachments()

    def _get_selected_datetime(self):
        """Helper to combine the DateEdit and TimeComboBox into a single QDateTime"""
        d = self.date_input.date()
        t = QTime.fromString(self.time_input.currentText(), "hh:mm AP")
        if not t.isValid():
            t = QTime(23, 59, 59)
        return QDateTime(d, t)

    def validate_and_accept(self):
        title = self.title_input.text().strip()

        if not title:
            self.toast.show_toast("Title is required!")
            return

        # --- PAST DUE DATETIME VALIDATION ---
        selected_dt = self._get_selected_datetime()
        current_dt = QDateTime.currentDateTime()

        # Check if the currently selected datetime is in the past
        if selected_dt < current_dt:
            original_dt = None

            # Identify if we are editing an existing task, and if so, capture its original datetime
            if self.task and self.task.due_date:
                due_str = str(self.task.due_date).strip()
                if due_str:
                    parsed_dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
                    if parsed_dt.isValid():
                        original_dt = parsed_dt
                    else:
                        # Legacy fallback parsing for comparison
                        parsed_d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                        if parsed_d.isValid():
                            original_dt = QDateTime(parsed_d, QTime(23, 59, 59))

            # If it's a NEW task, OR they changed the datetime to a NEW past datetime, block the save
            if not original_dt or selected_dt != original_dt:
                self.toast.show_toast("Due Date/Time cannot be in the past!")
                return
        # --------------------------------

        self.accept()

    def get_data(self):
        """Returns a dictionary of the task data"""
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "due_date": self._get_selected_datetime().toString(Qt.DateFormat.ISODate),
            "priority": self.priority_input.currentText(),
            "status": self.status_input.currentText(),
            "color": self.color_combo.currentData(),
            "tags": self.selected_tags,
            "attachments": self.attachments,
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
