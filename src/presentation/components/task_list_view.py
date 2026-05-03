from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QLabel,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from utils.constants import ACTIVE_THEME_MAP, UIConstants
from utils.sorter import TaskSorter
from utils.strings import UIStrings


from typing import Optional


class TaskListView(QWidget):
    """
    Modular Task List View using QTreeWidget with Status Grouping.
    ISO 25010: Improves Modularity and Analyzability.
    """

    def __init__(
        self, parent: Optional[QWidget] = None, dashboard: Optional[any] = None
    ):
        super().__init__(parent)
        self.dashboard = dashboard
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.task_tree = QTreeWidget()
        self.task_tree.setColumnCount(3)
        self.task_tree.setHeaderHidden(True)
        self.task_tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.task_tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.task_tree.setIndentation(0)

        self.task_tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(30, 35, 40, 0.8);
                color: white;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.08);
                font-size: 13px;
            }
            QTreeWidget::item:hover { background-color: rgba(255,255,255,0.15); }
            QTreeWidget::item:selected { background-color: rgba(255,255,255,0.1); }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings { image: none; }
        """)

        header = self.task_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.task_tree.setColumnWidth(1, UIConstants.TREE_COL_DATE_WIDTH)
        self.task_tree.setColumnWidth(2, UIConstants.TREE_COL_PRIO_WIDTH)

        # Context Menu & Expansion Signals
        self.task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_tree.customContextMenuRequested.connect(
            self.dashboard.show_table_menu
        )
        self.task_tree.itemClicked.connect(self.dashboard.toggle_group_expansion)
        self.task_tree.itemExpanded.connect(self.dashboard.sync_group_arrow)
        self.task_tree.itemCollapsed.connect(self.dashboard.sync_group_arrow)

        # ISO 25010: Enhances Usability. Opens the edit dialog on double-click.
        self.task_tree.itemDoubleClicked.connect(self.handle_double_click)

        self.main_layout.addWidget(self.task_tree)

    def handle_double_click(self, item, column):
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        if task_id:
            self.dashboard.edit_specific_task(task_id)

    def render_tasks(self, tasks, criteria="Due Date"):
        self.task_tree.clear()

        # Professional sorting using TaskSorter
        sorted_tasks = TaskSorter.sort(tasks, criteria)

        # Groups initialization
        self.todo_group = self._create_group(f"   ▼ {UIStrings.LABEL_TODO}")
        self.progress_group = self._create_group(f"   ▼ {UIStrings.LABEL_IN_PROGRESS}")
        self.done_group = self._create_group(f"   ▼ {UIStrings.LABEL_DONE}")

        for grp in [self.todo_group, self.progress_group, self.done_group]:
            if grp != self.todo_group:
                spacer = QTreeWidgetItem(["", "", ""])
                spacer.setFlags(Qt.ItemFlag.NoItemFlags)
                spacer.setSizeHint(0, QSize(0, 20))
                self.task_tree.addTopLevelItem(spacer)

            self.task_tree.addTopLevelItem(grp)
            grp.setExpanded(True)

            # Inline Headers
            inline_header = QTreeWidgetItem(
                ["     Task Title", "Due Date", "Priority   "]
            )
            inline_header.setFlags(Qt.ItemFlag.NoItemFlags)
            inline_header.setSizeHint(0, QSize(0, 32))
            inline_font = inline_header.font(0)
            inline_font.setPointSize(11)
            inline_font.setBold(True)
            for col in range(3):
                inline_header.setForeground(col, QColor(160, 170, 180))
                inline_header.setBackground(col, QColor(15, 20, 25, 80))
                inline_header.setFont(col, inline_font)

            inline_header.setTextAlignment(
                1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            inline_header.setTextAlignment(
                2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            grp.addChild(inline_header)

        # Task items
        for task in sorted_tasks:
            if task.status == UIStrings.STATUS_DONE:
                parent_grp = self.done_group
            elif task.status == UIStrings.STATUS_IN_PROGRESS:
                parent_grp = self.progress_group
            else:
                parent_grp = self.todo_group

            # --------- URGENCY LOGIC ---------
            from PySide6.QtCore import QDateTime, QDate

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

            urgent = is_task_urgent(task)

            # Format date nicely
            display_str = "--"
            if task.due_date:
                due_str = str(task.due_date).strip()
                parsed_dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
                if parsed_dt.isValid():
                    display_str = parsed_dt.toString("MMM d, yy - h:mm AP")
                else:
                    parsed_d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                    display_str = (
                        parsed_d.toString("MMM d, yy")
                        if parsed_d.isValid()
                        else due_str
                    )

            row_item = QTreeWidgetItem([task.title, display_str, task.priority])
            row_item.setSizeHint(0, QSize(0, 32))
            row_item.setData(0, Qt.ItemDataRole.UserRole, task.id)

            bg_hex = (
                task.color
                if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
                else "#333333"
            )
            fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")
            base = QColor(bg_hex)

            # Row Background
            for col in range(3):
                row_item.setBackground(
                    col, QColor(base.red(), base.green(), base.blue(), 50)
                )

            # Tooltip Countdown
            countdown = TaskSorter.format_due_countdown(task.due_date, task.status)
            if countdown:
                for col in range(3):
                    row_item.setToolTip(col, countdown)

            row_item.setForeground(
                0, QColor(0, 0, 0, 0)
            )  # Transparent for widget overlay
            row_item.setForeground(1, QColor("#FF4D4D" if urgent else fg_hex))
            row_item.setForeground(2, QColor(0, 0, 0, 0))
            row_item.setTextAlignment(
                1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )

            # Cell Overlay (Title + Urgent Indicator)
            cell_container = QWidget()
            cell_layout = QHBoxLayout(cell_container)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(6)

            if urgent:
                indicator = QFrame()
                indicator.setFixedSize(4, 20)
                indicator.setStyleSheet(
                    "background-color: #FF4D4D; border-radius: 2px;"
                )
                cell_layout.addWidget(indicator)
            else:
                spacer = QFrame()
                spacer.setFixedSize(4, 20)
                cell_layout.addWidget(spacer)

            title_lbl = QLabel(task.title)
            title_lbl.setStyleSheet(f"color: {fg_hex}; font-size: 13px;")
            cell_layout.addWidget(title_lbl, 1)

            parent_grp.addChild(row_item)
            self.task_tree.setItemWidget(row_item, 0, cell_container)

            # Badge Overlay (Priority)
            badge = QLabel(task.priority)
            badge.setFixedSize(70, 20)
            badge.setStyleSheet(
                f"background-color: {bg_hex}; color: {fg_hex}; border-radius: 4px; font-weight: bold;"
            )
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge_container = QWidget()
            badge_layout = QHBoxLayout(badge_container)
            badge_layout.addStretch()
            badge_layout.addWidget(badge)
            self.task_tree.setItemWidget(row_item, 2, badge_container)

    def _create_group(self, title: str) -> QTreeWidgetItem:
        """Helper to create a styled status group header."""
        group = QTreeWidgetItem([title, "", ""])
        group.setFirstColumnSpanned(True)
        group.setSizeHint(0, QSize(0, 50))
        for col in range(3):
            group.setBackground(col, QColor(0, 0, 0, 160))
        font = group.font(0)
        font.setBold(True)
        font.setPointSize(13)
        group.setFont(0, font)
        group.setForeground(0, QColor(255, 255, 255, 220))
        return group
