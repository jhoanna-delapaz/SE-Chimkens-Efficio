from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QLabel,
)
from PySide6.QtCore import Qt
from presentation.components.kanban_card import KanbanCard
from utils.sorter import TaskSorter
from utils.constants import UIConstants
from utils.strings import UIStrings


from typing import Optional


class KanbanLane(QFrame):
    """
    Subclass of QFrame that handles drag-and-drop events for Kanban lanes.
    """

    def __init__(self, title, status, dashboard):
        super().__init__()
        self.status = status
        self.dashboard = dashboard
        self.setAcceptDrops(True)
        self.setup_ui(title)

    def setup_ui(self, title_text):
        self.setMinimumWidth(UIConstants.KANBAN_LANE_MIN_WIDTH)
        self.setStyleSheet(
            "background-color: rgba(0,0,0,0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
        )

        layout = QVBoxLayout(self)
        title = QLabel(title_text)
        title.setStyleSheet(
            "color: white; font-weight: bold; font-size: 16px; padding: 10px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(15)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(
                "background-color: rgba(255,255,255,0.1); border-radius: 12px; border: 2px dashed rgba(255,255,255,0.3);"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            "background-color: rgba(0,0,0,0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
        )

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.setStyleSheet(
            "background-color: rgba(0,0,0,0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
        )
        task_id_str = event.mimeData().text()
        try:
            task_id = int(task_id_str)
            if self.dashboard:
                self.dashboard.task_manager.update_task_status(task_id, self.status)
                self.dashboard.load_tasks()
            event.acceptProposedAction()
        except ValueError:
            event.ignore()


class KanbanBoardView(QWidget):
    """
    Extracted Kanban Board View Component.
    ISO 25010: Improves Modifiability and Separation of Concerns.
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "background: rgba(0,0,0,0.3); border-radius: 16px; border: none;"
        )

        self.container = QWidget()
        self.lane_layout = QHBoxLayout(self.container)
        self.lane_layout.setContentsMargins(15, 15, 15, 15)
        self.lane_layout.setSpacing(15)

        self.todo_lane = KanbanLane(
            UIStrings.LABEL_TODO, UIStrings.STATUS_TODO, self.dashboard
        )
        self.progress_lane = KanbanLane(
            UIStrings.LABEL_IN_PROGRESS, UIStrings.STATUS_IN_PROGRESS, self.dashboard
        )
        self.done_lane = KanbanLane(
            UIStrings.LABEL_DONE, UIStrings.STATUS_DONE, self.dashboard
        )

        self.lane_layout.addWidget(self.todo_lane, 1)
        self.lane_layout.addWidget(self.progress_lane, 1)
        self.lane_layout.addWidget(self.done_lane, 1)
        self.lane_layout.addStretch()

        self.todo_content = self.todo_lane.content_layout
        self.progress_content = self.progress_lane.content_layout
        self.done_content = self.done_lane.content_layout

        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)

    def render_tasks(self, tasks, criteria="Due Date"):
        # Clear existing cards
        for layout in [self.todo_content, self.progress_content, self.done_content]:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # Sort tasks
        sorted_tasks = TaskSorter.sort(tasks, criteria)

        for task in sorted_tasks:
            card = KanbanCard(task, self.dashboard)
            if task.status == UIStrings.STATUS_DONE:
                self.done_content.addWidget(card)
            elif task.status == UIStrings.STATUS_IN_PROGRESS:
                self.progress_content.addWidget(card)
            else:
                self.todo_content.addWidget(card)
