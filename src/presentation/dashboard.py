import logging
import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QFrame,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from business.task_manager import TaskManager
from data.models import Task
from presentation.analytics_widget import AnalyticsWidget
from presentation.components.kanban_board_view import KanbanBoardView

# ISO 25010: Modular components and centralized constants
from presentation.components.task_list_view import TaskListView
from presentation.task_editor_dialog import TaskEditorDialog
from presentation.trash_widget import TrashWidget
from presentation.tags_management_widget import TagsManagementWidget
from utils.constants import UIConstants
from utils.paths import get_asset_path
from utils.strings import UIStrings

logger = logging.getLogger(__name__)


class DashboardInterface(QWidget):
    """
    Main controller and user interface for the Efficio Dashboard.

    This class manages the primary application routing loop, handling switching
    between the standard dashboard view, the Kanban board, and the Trash bin.
    It maintains direct synchronization with the SQLite TaskManager backend.
    """

    def __init__(self, parent=None, db_file=None):
        """
        Initializes the DashboardInterface with the given parent and database file path.

        Args:
            parent (QWidget): The parent widget of this widget.
            db_file (str): The path to the SQLite database file.
        """
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")

        self.db_file = db_file
        self.task_manager = TaskManager(self.db_file)
        self.current_mode = "active"
        self.current_sort = "Due Date"

        # Sidebar UI State tracking
        self.sidebar_expanded = False

        # Safely calculate absolute path to the teammate's image using centralized utility
        self.preset_image_path = get_asset_path(
            os.path.join("..", "ref", "Efficio_UI", "images", "pastel-bg.jpg")
        )

        # Setup the Glassmorphism Background Blur
        self.bg_label = QLabel(self)
        self.bg_label.setStyleSheet("border: none;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(30)
        self.bg_label.setGraphicsEffect(blur)

        self.setup_ui()
        self.update_background()
        self.load_tasks()

    def resizeEvent(self, event):
        """
        Overrides the default resize event to handle window resizing.

        Args:
            event (QResizeEvent): The resize event.
        """
        self.update_background()
        super().resizeEvent(event)

    def update_background(self):
        """
        Dynamically adjusts the application background based on current window geometry.

        Attempts to load a standard graphic asset (QPixmap). If the asset is missing
        or a file IO exception occurs, it safely resolves to a high-contrast dark solid color.
        """
        try:
            # Check if your teammate actually pushed the image file
            if os.path.exists(self.preset_image_path):
                pixmap = QPixmap(self.preset_image_path).scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.bg_label.setPixmap(pixmap)
            else:
                # Safe fallback color if image doesn't exist so tasks are visible
                self.bg_label.setStyleSheet("background-color: #4A5568;")

            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            self.bg_label.setStyleSheet("background-color: #4A5568;")

    def setup_ui(self):
        """
        Architects and renders the primary application grid using modular components.
        ISO 25010: Improves Modifiability and Analyzability.
        """
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # ---------------- Sidebar ----------------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(UIConstants.SIDEBAR_COLLAPSED_WIDTH)
        self.sidebar.setStyleSheet(
            f"QFrame {{ background-color: rgba(0,0,0,0.4); border-radius: {UIConstants.ROUND_RADIUS_LARGE}px; }}"
        )

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(15)

        toggle_container = QHBoxLayout()
        self.toggle_btn = QPushButton("≡")
        self.toggle_btn.setFixedSize(
            UIConstants.SIDEBAR_ICON_SIZE, UIConstants.SIDEBAR_ICON_SIZE
        )
        self.toggle_btn.setStyleSheet("""
        QPushButton {
        background-color: rgba(255,255,255,0.1);
        color: white;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        }
        QPushButton:hover {
        background-color: rgba(255,255,255,0.2);
        }""")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        toggle_container.addWidget(self.toggle_btn)
        toggle_container.addStretch()
        self.sidebar_layout.addLayout(toggle_container)

        self.sidebar_options = []
        for text in ["Dashboard", "Kanban Board", "Manage Tags", "Trash Bin"]:
            btn = QPushButton("")
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
            QPushButton {
            background-color: rgba(255,255,255,0.05);
            color: white;
            border-radius: 10px;
            font-size: 14px;
            border: 1px solid rgba(255,255,255,0.1);
            }
            QPushButton:hover {
            background-color: rgba(255,255,255,0.15);
            }""")
            if text == "Dashboard":
                btn.clicked.connect(lambda: self.set_mode("active"))
            elif text == "Kanban Board":
                btn.clicked.connect(lambda: self.set_mode("kanban"))
            elif text == "Manage Tags":
                btn.clicked.connect(lambda: self.set_mode("tags"))
            elif text == "Trash Bin":
                btn.clicked.connect(lambda: self.set_mode("trash"))

            self.sidebar_layout.addWidget(btn)
            self.sidebar_options.append((btn, text))
        self.sidebar_layout.addStretch()

        # ---------------- STACKED WIDGET CORE ----------------
        self.content_stack = QStackedWidget()

        # --- PAGE 1: Dashboard ---
        self.page_dashboard = QWidget()
        dash_main_layout = QHBoxLayout(self.page_dashboard)
        dash_main_layout.setContentsMargins(0, 0, 0, 0)

        task_section_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title_label = QLabel("My Tasks")
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: white;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Sorting Dropdown (New Feature)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Due Date", "Priority"])
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 10px; padding: 5px; border: 1px solid rgba(255,255,255,0.2);
            }
            QComboBox:hover { background-color: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); }
        """)
        self.sort_combo.currentTextChanged.connect(self.handle_sort_change)
        header_layout.addWidget(self.sort_combo)

        # Tag Filter Dropdown
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.setFixedWidth(140)
        self.tag_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 10px; padding: 5px; border: 1px solid rgba(255,255,255,0.2);
            }
            QComboBox:hover { background-color: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); }
        """)
        self.tag_filter_combo.currentIndexChanged.connect(
            lambda: self.handle_tag_filter_change(self.tag_filter_combo.currentData())
        )
        header_layout.addWidget(self.tag_filter_combo)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks...")
        self.search_bar.setFixedWidth(200)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 10px;
                padding: 5px 8px;
                color: white;
            }
            QLineEdit:hover { background-color: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); }
        """)
        self.search_bar.textChanged.connect(lambda: self.load_tasks())
        header_layout.addWidget(self.search_bar)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 30px;
                border-radius: 20px;
                padding-bottom: 4px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        self.add_btn.clicked.connect(self.show_add_task_dialog)
        header_layout.addWidget(self.add_btn)

        task_section_layout.addLayout(header_layout)

        # Urgent Banner
        self.urgent_banner_btn = QPushButton()
        self.urgent_banner_btn.setStyleSheet("""
            QPushButton { background-color: #FF4D4D; color: white; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #FF6666; }
        """)
        self.urgent_banner_btn.hide()
        self.urgent_banner_btn.clicked.connect(
            lambda: (
                self.search_bar.setText("")
                if self.search_bar.text() == "is:urgent"
                else self.search_bar.setText("is:urgent")
            )
        )
        task_section_layout.addWidget(self.urgent_banner_btn)

        # MODULAR TASK LIST COMPONENT
        self.task_list_view = TaskListView(dashboard=self)
        task_section_layout.addWidget(self.task_list_view)

        # Right Panel
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setSpacing(20)

        # Calendar Container (ISO 25010: Cohesive UI)
        calendar_container = QFrame()
        calendar_container.setStyleSheet("""
            QFrame { background-color: rgba(0,0,0,0.3); border-radius: 15px; border: 1px solid rgba(255,255,255,0.05); }
        """)
        cal_layout = QVBoxLayout(calendar_container)
        calendar = QCalendarWidget()
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { background: transparent; color: white; }
            QCalendarWidget QAbstractItemView { background-color: transparent; selection-background-color: #6579BE; selection-color: white; }
            QCalendarWidget QToolButton { color: white; background: transparent; }
            QCalendarWidget QMenu { background-color: #1E2328; color: white; }
            QCalendarWidget QSpinBox { color: white; background: transparent; }
        """)
        cal_layout.addWidget(calendar)

        self.analytics_widget = AnalyticsWidget()
        right_panel_layout.addWidget(calendar_container)
        right_panel_layout.addWidget(self.analytics_widget)

        dash_main_layout.addLayout(task_section_layout, 3)
        dash_main_layout.addLayout(right_panel_layout, 2)

        # --- PAGE 2: Kanban ---
        self.page_kanban = QWidget()
        kanban_page_layout = QVBoxLayout(self.page_kanban)

        kanban_header = QHBoxLayout()
        k_title = QLabel("Kanban Board")
        k_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        kanban_header.addWidget(k_title)
        kanban_header.addStretch()

        # Kanban Sorting Dropdown
        self.kanban_sort_combo = QComboBox()
        self.kanban_sort_combo.addItems(["Due Date", "Priority"])
        self.kanban_sort_combo.setFixedWidth(120)
        self.kanban_sort_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 10px; padding: 5px;
            }
            QComboBox:hover { background-color: rgba(255,255,255,0.15); }
        """)
        self.kanban_sort_combo.currentTextChanged.connect(self.handle_sort_change)
        kanban_header.addWidget(self.kanban_sort_combo)

        # Kanban Tag Filter
        self.kanban_tag_filter_combo = QComboBox()
        self.kanban_tag_filter_combo.setFixedWidth(140)
        self.kanban_tag_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 10px; padding: 5px; border: 1px solid rgba(255,255,255,0.2);
            }
            QComboBox:hover { background-color: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); }
        """)
        self.kanban_tag_filter_combo.currentIndexChanged.connect(
            lambda: self.handle_tag_filter_change(
                self.kanban_tag_filter_combo.currentData()
            )
        )
        kanban_header.addWidget(self.kanban_tag_filter_combo)

        self.kanban_search_bar = QLineEdit()
        self.kanban_search_bar.setPlaceholderText("Search kanban...")
        self.kanban_search_bar.setFixedWidth(200)
        self.kanban_search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 10px; padding: 5px;
            }
            QLineEdit:hover { background-color: rgba(255,255,255,0.15); }
        """)
        self.kanban_search_bar.textChanged.connect(lambda: self.load_tasks())
        kanban_header.addWidget(self.kanban_search_bar)

        # Re-added Kanban Add Button
        self.kanban_add_btn = QPushButton("+")
        self.kanban_add_btn.setFixedSize(40, 40)
        self.kanban_add_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                font-size: 30px;
                border-radius: 20px;
                padding-bottom: 4px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        self.kanban_add_btn.clicked.connect(self.show_add_task_dialog)
        kanban_header.addWidget(self.kanban_add_btn)

        kanban_page_layout.addLayout(kanban_header)

        # Kanban Urgent Banner
        self.kanban_urgent_banner_btn = QPushButton()
        self.kanban_urgent_banner_btn.setStyleSheet("""
            QPushButton { background-color: #FF4D4D; color: white; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #FF6666; }
        """)
        self.kanban_urgent_banner_btn.hide()
        self.kanban_urgent_banner_btn.clicked.connect(
            lambda: (
                self.kanban_search_bar.setText("")
                if self.kanban_search_bar.text() == "is:urgent"
                else self.kanban_search_bar.setText("is:urgent")
            )
        )
        kanban_page_layout.addWidget(self.kanban_urgent_banner_btn)

        # MODULAR KANBAN BOARD COMPONENT
        self.kanban_board_view = KanbanBoardView(dashboard=self)
        kanban_page_layout.addWidget(self.kanban_board_view)

        # Assemble Stack
        self.content_stack.addWidget(self.page_dashboard)
        self.content_stack.addWidget(self.page_kanban)
        self.page_trash = TrashWidget(self)
        self.content_stack.addWidget(self.page_trash)
        self.page_tags = TagsManagementWidget(self, self.task_manager)
        self.content_stack.addWidget(self.page_tags)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack, stretch=1)

        self.current_tag_filter = None
        self.populate_tag_filters()

    def populate_tag_filters(self):
        current_active = (
            self.tag_filter_combo.currentData()
            if hasattr(self, "tag_filter_combo")
            else None
        )
        current_kanban = (
            self.kanban_tag_filter_combo.currentData()
            if hasattr(self, "kanban_tag_filter_combo")
            else None
        )

        tags = self.task_manager.get_all_tags()

        for combo, current_sel in [
            (self.tag_filter_combo, current_active),
            (self.kanban_tag_filter_combo, current_kanban),
        ]:
            if not combo:
                continue
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("All Tags", None)
            for tag in tags:
                combo.addItem(f"🏷️ {tag.name}", tag.id)

            if current_sel is not None:
                idx = combo.findData(current_sel)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def handle_tag_filter_change(self, tag_id):
        self.current_tag_filter = tag_id
        for combo in [self.tag_filter_combo, self.kanban_tag_filter_combo]:
            if combo:
                combo.blockSignals(True)
                idx = combo.findData(tag_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.blockSignals(False)
        self.load_tasks()

    def toggle_sidebar(self):
        """Animated Sidebar functionality"""
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(UIConstants.SIDEBAR_COLLAPSED_WIDTH)
            for btn, text in self.sidebar_options:
                btn.setText("")
        else:
            self.sidebar.setFixedWidth(UIConstants.SIDEBAR_EXPANDED_WIDTH)
            for btn, text in self.sidebar_options:
                btn.setText(text)
        self.sidebar_expanded = not self.sidebar_expanded

    def handle_sort_change(self, text):
        """
        Synchronizes sorting criteria across all views and triggers a UI refresh.
        """
        self.current_sort = text

        # Sync the combo boxes so they always match
        if hasattr(self, "sort_combo"):
            self.sort_combo.blockSignals(True)
            self.sort_combo.setCurrentText(text)
            self.sort_combo.blockSignals(False)

        if hasattr(self, "kanban_sort_combo"):
            self.kanban_sort_combo.blockSignals(True)
            self.kanban_sort_combo.setCurrentText(text)
            self.kanban_sort_combo.blockSignals(False)

        self.load_tasks()

    def load_tasks(self):
        """
        Refreshes the entire dashboard view by querying the database and repopulating widgets.
        ISO 25010: High Analyzability and Functional Suitability.
        """
        query = ""
        if self.current_mode == "kanban" and hasattr(self, "kanban_search_bar"):
            query = self.kanban_search_bar.text()
        elif hasattr(self, "search_bar"):
            query = self.search_bar.text()

        # Filter handling
        db_query = "" if query == "is:urgent" else query
        tasks = self.task_manager.get_all_tasks(db_query)

        # Urgency Logic
        from PySide6.QtCore import QDate, QDateTime

        def is_task_urgent(t):
            if t.status == UIStrings.STATUS_DONE or not t.due_date:
                return False
            due_str = str(t.due_date).strip()
            dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
            if not dt.isValid():
                d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                if not d.isValid():
                    return False
                dt = QDateTime(d, QDateTime.currentDateTime().time())
            return QDateTime.currentDateTime().secsTo(dt) <= (2 * 24 * 3600)

        if query == "is:urgent":
            tasks = [t for t in tasks if is_task_urgent(t)]

        if hasattr(self, "current_tag_filter") and self.current_tag_filter is not None:
            tasks = [
                t
                for t in tasks
                if any(tag.id == self.current_tag_filter for tag in t.tags)
            ]

        # Update Banners
        urgent_count = sum(1 for t in tasks if is_task_urgent(t))
        if urgent_count > 0:
            msg = (
                f"⚠️ {urgent_count} Urgent Tasks!"
                if query == "is:urgent"
                else f"⚠️ {urgent_count} urgent tasks require attention."
            )
            self.urgent_banner_btn.setText(msg)
            self.urgent_banner_btn.show()
            if hasattr(self, "kanban_urgent_banner_btn"):
                self.kanban_urgent_banner_btn.setText(msg)
                self.kanban_urgent_banner_btn.show()
        else:
            self.urgent_banner_btn.hide()
            if hasattr(self, "kanban_urgent_banner_btn"):
                self.kanban_urgent_banner_btn.hide()

        # DELEGATE TO MODULAR COMPONENTS
        self.task_list_view.render_tasks(tasks, self.current_sort)
        self.kanban_board_view.render_tasks(tasks, self.current_sort)

        # Refresh analytics panel
        if hasattr(self, "analytics_widget"):
            self.analytics_widget.refresh(self.task_manager, tasks)

    def show_kanban_context_menu(self, task, global_pos):
        """
        Spawns the right-click interactive menu for Kanban and TreeWidget entities.

        Dynamically adjusts allowed operations based on whether the user is viewing
        active tasks (Standard) or deleted tasks (Trash mode), then routes the execution
        to the appropriate CRUD database operation.

        Args:
            task (Task): The data payload of the selected item.
            global_pos (QPoint): The exact absolute screen coordinates to draw the menu.
        """
        menu = QMenu(self)
        if self.current_mode in ("active", "kanban"):
            pending_action = menu.addAction(f"Move to {UIStrings.STATUS_TODO}")
            progress_action = menu.addAction(f"Move to {UIStrings.STATUS_IN_PROGRESS}")
            done_action = menu.addAction(f"Move to {UIStrings.STATUS_DONE}")
            menu.addSeparator()
            edit_action = menu.addAction(UIStrings.ACTION_EDIT_TASK)
            delete_action = menu.addAction(UIStrings.ACTION_DELETE_TASK)

            action = menu.exec(global_pos)
            if action == pending_action:
                self.task_manager.update_task_status(task.id, UIStrings.STATUS_TODO)
            elif action == progress_action:
                self.task_manager.update_task_status(
                    task.id, UIStrings.STATUS_IN_PROGRESS
                )
            elif action == done_action:
                self.task_manager.update_task_status(task.id, UIStrings.STATUS_DONE)
            elif action == edit_action:
                self.edit_specific_task(task.id)
            elif action == delete_action:
                self.delete_specific_task(task.id)

        elif self.current_mode == "trash":
            restore_action = menu.addAction(UIStrings.ACTION_RESTORE)
            perm_delete_action = menu.addAction(UIStrings.ACTION_PERM_DELETE)
            action = menu.exec(global_pos)
            if action == restore_action:
                self.task_manager.restore_task(task.id)
            elif action == perm_delete_action:
                confirm = QMessageBox.warning(
                    self,
                    UIStrings.ACTION_PERM_DELETE,
                    UIStrings.CONFIRM_PERM_DELETE,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    self.task_manager.permanently_delete_task(task.id)
        self.load_tasks()

    def show_table_menu(self, pos):
        """
        Displays a context-sensitive menu for TreeWidget items when right-clicked.
        """
        # ISO 25010: Fixing reference to modular component
        item = self.task_list_view.task_tree.itemAt(pos)

        if item is None or item.parent() is None:
            return

        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            self.show_kanban_context_menu(
                task, self.task_list_view.task_tree.viewport().mapToGlobal(pos)
            )

    def edit_specific_task(self, task_id):
        """
        Instantiates the TaskEditorDialog in 'Edit' mode and synchronizes database updates.

        Args:
            task_id (int): The unique primary key of the target task to modify.
        """

        # We abstracted this so the Kanban card can call it without relying on a QListWidgetItem
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            dialog = TaskEditorDialog(self, task=task)
            if dialog.exec():
                data = dialog.get_data()
                updated_task = Task(
                    id=task_id,
                    title=data["title"],
                    description=data["description"],
                    status=data["status"],
                    created_at=task.created_at,
                    due_date=data["due_date"],
                    priority=data["priority"],
                    color=data.get("color", "#333333"),
                    tags=data.get("tags", []),
                    attachments=data.get("attachments", []),
                )
                self.task_manager.update_task(updated_task)
                self.load_tasks()

    def delete_specific_task(self, task_id):
        """
        Deletes a specific task after user confirmation.

        Args:
            task_id (int): The unique primary key of the target task to delete.
        """
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Send this task to the Trash Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.task_manager.delete_task(task_id)
            self.load_tasks()

    def show_add_task_dialog(self):
        """
        Opens the dialog to create a new task. Provides a success notification
        upon successfully saving the task to the database.
        """
        dialog = TaskEditorDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # Create Task Object
            new_task = Task(
                id=None,
                title=data["title"],
                description=data["description"],
                status=data["status"],
                created_at=datetime.now(),
                due_date=data["due_date"],
                priority=data["priority"],
                color=data.get("color", "#333333"),
                tags=data.get("tags", []),
                attachments=data.get("attachments", []),
            )

            # Save to DB safely
            result_id = self.task_manager.add_task(new_task)

            if result_id != -1:
                # ISO 25010 Usability: Visual confirmation of success
                QMessageBox.information(
                    self,
                    "Success",
                    f"Task '{new_task.title}' was successfully created!",
                )
                self.load_tasks()
            else:
                QMessageBox.critical(
                    self, "Error", "A database error occurred while saving the task."
                )

    def show_context_menu(self, pos):
        """
        Displays a context-sensitive menu for ListWidget items when right-clicked.

        Args:
            pos (QPoint): The local position within the list widget where the click occurred.
        """
        item = self.task_list.itemAt(pos)
        if item:
            menu = QMenu(self)

            if self.current_mode == "active":
                edit_action = menu.addAction("Edit Task")
                delete_action = menu.addAction("Move to Trash")
                action = menu.exec(self.task_list.mapToGlobal(pos))

                if action == delete_action:
                    self.delete_current_task(item)
                elif action == edit_action:
                    self.edit_current_task(item)

            elif self.current_mode == "trash":
                restore_action = menu.addAction("Restore Task")
                perm_delete_action = menu.addAction("Permanently Delete")
                action = menu.exec(self.task_list.mapToGlobal(pos))

                if action == restore_action:
                    task_id = item.data(Qt.ItemDataRole.UserRole)
                    self.task_manager.restore_task(task_id)
                    self.load_tasks()
                elif action == perm_delete_action:
                    task_id = item.data(Qt.ItemDataRole.UserRole)
                    confirm = QMessageBox.warning(
                        self,
                        "Permanent Delete",
                        "This will permanently obliterate this task. Are you sure?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        self.task_manager.permanently_delete_task(task_id)
                        self.load_tasks()

    def delete_current_task(self, item):
        """
        Deletes the currently selected task from the list view.

        Args:
            item (QListWidgetItem): The list item to delete.
        """
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                "Are you sure you want to delete this task?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task_id)
                self.load_tasks()

    def set_mode(self, mode):
        """
        Executes a High-Level layout pivot between major Application Views.

        Adjusts the QStackedWidget index, hides/shows appropriate global action buttons,
        and fundamentally shifts the underlying SQL queries for the view matrix.

        Args:
            mode (str): The target application state ("active", "kanban", or "trash").
        """
        self.current_mode = mode
        if mode == "trash":
            self.title_label.setText("Trash Bin")
            self.add_btn.hide()
            self.content_stack.setCurrentIndex(2)  # TrashWidget
            self.page_trash.refresh()
        elif mode == "tags":
            self.title_label.setText("Manage Tags")
            self.add_btn.hide()
            self.content_stack.setCurrentIndex(3)  # TagsWidget
            self.page_tags.refresh()
        elif mode == "active":
            self.title_label.setText(UIStrings.NAV_TASKS)
            self.add_btn.show()
            self.content_stack.setCurrentIndex(0)  # Dashboard Profile
            self.populate_tag_filters()
            self.load_tasks()
        elif mode == "kanban":
            # Swaps the screen purely to the massive Kanban Board!
            self.title_label.setText(UIStrings.NAV_KANBAN)
            self.content_stack.setCurrentIndex(1)
            self.populate_tag_filters()
            self.load_tasks()

    def sync_group_arrow(self, item):
        """
        Force-updates the arrow text based on the item's actual expansion state.
        This is connected to native itemExpanded and itemCollapsed signals.
        """
        if item.childCount() > 0:
            expanded = item.isExpanded()
            text = item.text(0)

            # Identify name safely
            if "To-Do" in text:
                name = "To-Do"
            elif "In Progress" in text:
                name = "In Progress"
            elif "Done" in text:
                name = "Done"
            else:
                name = text.strip(" ►▼")

            arrow = "▼" if expanded else "►"
            item.setText(0, f"   {arrow} {name}")

    def toggle_group_expansion(self, item, column):
        """
        Toggles state on click. The arrow itself is updated by sync_group_arrow
        via the native itemExpanded/itemCollapsed signals.
        """
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
