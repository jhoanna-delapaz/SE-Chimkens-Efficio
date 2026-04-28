"""
Trash Widget for the Efficio Dashboard.

Provides a self-contained QWidget that renders deleted tasks in a styled QTreeWidget.
Handles its own search bar and context menu (Restore, Permanently Delete).

ISO 25010 Compliance:
    - Modifiability: Extracts the trash view from the Dashboard god class.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class TrashWidget(QWidget):
    """Self-contained Trash Bin view for the Efficio Dashboard.

    Renders deleted tasks and provides context menu actions for restoration
    and permanent deletion.
    """

    def __init__(self, dashboard) -> None:
        """Initialise the widget and build layout.

        Args:
            dashboard: The main DashboardInterface (for access to task_manager and load_tasks).
        """
        super().__init__()
        self.dashboard = dashboard
        self.task_manager = dashboard.task_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ── Header ──────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_label = QLabel("🗑️ Trash Bin")
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search deleted tasks...")
        self.search_bar.setFixedWidth(250)
        self.search_bar.setStyleSheet(
            "padding: 8px; border-radius: 10px; background-color: rgba(255,255,255,0.1); color: white;"
        )
        self.search_bar.textChanged.connect(self.refresh)
        header_layout.addWidget(self.search_bar)

        layout.addLayout(header_layout)

        # ── Tree Widget ─────────────────────────────────────────────────────
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderHidden(False)
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.setHeaderLabels(["#", "Task Title", "Due Date", "Priority"])
        # Select entire rows, not individual cells
        self.task_tree.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        # Allow selecting multiple rows (Shift/Ctrl click)
        self.task_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        # THE MAGIC LINE: Forces the highlight to span the whole row evenly
        self.task_tree.setAllColumnsShowFocus(True)

        # Removes the ugly dotted outline that appears on the specific cell you click
        self.task_tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.task_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: rgba(30, 35, 40, 0.8);
                color: white;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.08);
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #30363d;
            }
            QTreeWidget::item:selected { background-color: rgba(255,255,255,0.1); }
        """
        )

        header = self.task_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.task_tree.setColumnWidth(2, 120)
        self.task_tree.setColumnWidth(3, 90)

        self.task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_tree.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.task_tree)

    def refresh(self) -> None:
        """Refreshes the trash view by querying the database."""
        from presentation.dashboard import ACTIVE_THEME_MAP

        self.task_tree.clear()
        query = self.search_bar.text()
        tasks = self.task_manager.get_deleted_tasks(query)

        for index, task in enumerate(tasks, start=1):
            row_item = QTreeWidgetItem(
                [
                    str(index),  # Column 0: The Row Number
                    task.title,  # Column 1: The Raw Title
                    task.due_date if task.due_date else "--",  # Column 2: Date
                    task.priority,  # Column 3: Priority
                ]
            )
            row_item.setSizeHint(0, QSize(0, 32))
            row_item.setData(0, Qt.ItemDataRole.UserRole, task.id)

            bg_hex = (
                task.color
                if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
                else "#333333"
            )
            fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")

            base = QColor(bg_hex)
            pastel = QColor(base.red(), base.green(), base.blue(), 50)

            for col in range(4):
                row_item.setBackground(col, pastel)

            row_item.setForeground(1, QColor(fg_hex))
            row_item.setTextAlignment(
                1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            # Priority Badge Setup (similar to Kanban)
            badge = QLabel(task.priority)
            badge.setFixedSize(70, 20)
            badge.setStyleSheet(
                f"background-color: {bg_hex}; color: {fg_hex}; border-radius: 4px; padding: 2px 0px; font-size: 11px; font-weight: bold; border: none;"
            )
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            badge_container = QWidget()
            badge_layout = QHBoxLayout(badge_container)
            badge_layout.setContentsMargins(30, 0, 5, 0)
            badge_layout.addStretch()
            badge_layout.addWidget(badge)

            # Title Setup
            title_container = QWidget()
            title_layout = QHBoxLayout(title_container)
            title_layout.setContentsMargins(10, 0, 0, 0)
            title_lbl = QLabel(task.title)
            title_lbl.setStyleSheet(
                f"color: {fg_hex}; font-size: 13px; background: transparent;"
            )
            title_layout.addWidget(title_lbl)
            title_layout.addStretch()

            self.task_tree.setItemWidget(row_item, 1, title_container)
            self.task_tree.setItemWidget(row_item, 3, badge_container)

            self.task_tree.addTopLevelItem(row_item)

    def show_context_menu(self, pos):
        """Displays context menu for restoring or deleting tasks permanently."""
        selected_items = self.task_tree.selectedItems()

        # Guard clause: Do nothing if they clicked empty space
        if not selected_items:
            return

        menu = QMenu(self)
        restore_action = menu.addAction(f"Restore ({len(selected_items)}) Tasks")
        perm_delete_action = menu.addAction(
            f"Permanently Delete ({len(selected_items)}) Tasks"
        )

        action = menu.exec(self.task_tree.viewport().mapToGlobal(pos))

        # Iterate and process
        if action == restore_action:
            for item in selected_items:
                task_id = item.data(0, Qt.ItemDataRole.UserRole)
                self.task_manager.restore_task(task_id)

            self.refresh()
            self.dashboard.load_tasks()

        elif action == perm_delete_action:
            confirm = QMessageBox.warning(
                self,
                "Permanent Delete",
                f"This will permanently obliterate {len(selected_items)} task(s). Are you sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                for item in selected_items:
                    task_id = item.data(0, Qt.ItemDataRole.UserRole)
                    self.task_manager.permanently_delete_task(task_id)
                self.refresh()
