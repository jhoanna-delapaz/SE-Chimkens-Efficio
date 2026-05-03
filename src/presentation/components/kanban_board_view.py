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

        self.todo_container, self.todo_content = self._create_lane(UIStrings.LABEL_TODO)
        self.progress_container, self.progress_content = self._create_lane(
            UIStrings.LABEL_IN_PROGRESS
        )
        self.done_container, self.done_content = self._create_lane(UIStrings.LABEL_DONE)

        self.lane_layout.addWidget(self.todo_container, 1)
        self.lane_layout.addWidget(self.progress_container, 1)
        self.lane_layout.addWidget(self.done_container, 1)
        self.lane_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)

    def _create_lane(self, title_text):
        container = QFrame()
        container.setMinimumWidth(UIConstants.KANBAN_LANE_MIN_WIDTH)
        container.setStyleSheet(
            "background-color: rgba(0,0,0,0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
        )

        layout = QVBoxLayout(container)
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
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.setSpacing(15)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return container, content_layout

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
