from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from utils.constants import ACTIVE_THEME_MAP


from data.models import Task
from utils.strings import UIStrings


class KanbanCard(QFrame):
    """
    Custom QFrame GUI component representing a single task in the Kanban board.
    ISO 25010: Improves Modifiability by isolating card rendering logic.
    """

    def __init__(self, task: Task, dashboard: any):
        super().__init__()
        self.task = task
        self.dashboard = dashboard
        self.setup_ui()

    def setup_ui(self):
        task = self.task
        bg_hex = (
            task.color
            if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
            else "#333333"
        )
        fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")

        bg_color = QColor(bg_hex)
        bg_css = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 120)"

        def shatter_gibberish(text):
            if not text:
                return ""
            words = text.split(" ")
            shattered = []
            for w in words:
                if len(w) > 20:
                    shattered.append(
                        "\u200b".join(w[i : i + 15] for i in range(0, len(w), 15))
                    )
                else:
                    shattered.append(w)
            return " ".join(shattered)

        # --------- URGENCY BORDER OVERRIDE ---------
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
        border_css = (
            "border: 1px solid rgba(255,255,255,0.2); border-left: 5px solid #FF4D4D;"
            if urgent
            else "border: 1px solid rgba(255,255,255,0.2);"
        )

        bg_hover_css = (
            f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 180)"
        )

        border_hover_css = (
            "border: 1px solid rgba(255,255,255,0.4); border-left: 5px solid #FF4D4D;"
            if urgent
            else "border: 1px solid rgba(255,255,255,0.4);"
        )

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_css};
                border-radius: 12px;
                {border_css}
            }}
            QFrame:hover {{
                background-color: {bg_hover_css};
                {border_hover_css}
            }}
            QLabel {{
                color: {fg_hex};
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        title_lbl = QLabel(shatter_gibberish(task.title))
        title_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_lbl.setWordWrap(True)
        title_lbl.setMinimumWidth(1)
        title_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )  # Hover pass-through

        priority_lbl = QLabel(task.priority)
        priority_lbl.setStyleSheet(f"""
            background-color: {fg_hex};
            color: {bg_hex};
            border-radius: 6px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 11px;
        """)
        priority_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        header_layout.addWidget(title_lbl, stretch=1)
        header_layout.addWidget(priority_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_layout)

        if task.description:
            desc_lbl = QLabel(shatter_gibberish(task.description))
            desc_lbl.setStyleSheet("font-size: 13px; opacity: 0.9;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setMinimumWidth(1)
            desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(desc_lbl)

        if task.due_date:
            from PySide6.QtCore import QDate, QDateTime

            due_str = str(task.due_date).strip()
            parsed_dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
            if parsed_dt.isValid():
                display_str = parsed_dt.toString("MMM d, yyyy - h:mm AP")
            else:
                parsed_d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                display_str = (
                    parsed_d.toString("MMM d, yyyy") if parsed_d.isValid() else due_str
                )

            footer_layout = QHBoxLayout()
            due_lbl = QLabel(f"📅 {display_str}")
            due_lbl.setStyleSheet("font-size: 12px; font-weight: bold; opacity: 0.8;")
            due_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            footer_layout.addWidget(due_lbl)
            footer_layout.addStretch()
            layout.addLayout(footer_layout)

        if hasattr(task, "tags") and task.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setContentsMargins(0, 4, 0, 0)
            tags_layout.setSpacing(4)
            displayed_tags = task.tags[:3]
            for tag in displayed_tags:
                tag_badge = QLabel(tag.name)
                t_color = "#FFFFFF"
                try:
                    hex_c = tag.color.lstrip("#")
                    r, g, b = (
                        int(hex_c[0:2], 16),
                        int(hex_c[2:4], 16),
                        int(hex_c[4:6], 16),
                    )
                    luma = 0.299 * r + 0.587 * g + 0.114 * b
                    t_color = "#000000" if luma > 160 else "#FFFFFF"
                except Exception:
                    pass
                tag_badge.setStyleSheet(
                    f"background-color: {tag.color}; color: {t_color}; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold;"
                )
                tags_layout.addWidget(tag_badge)

            if len(task.tags) > 3:
                more_lbl = QLabel(f"+{len(task.tags) - 3}")
                more_lbl.setStyleSheet(
                    "color: #A0A0A0; font-size: 11px; font-weight: bold;"
                )
                tags_layout.addWidget(more_lbl)

            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        # Tooltip Countdown
        from utils.sorter import TaskSorter

        countdown = TaskSorter.format_due_countdown(task.due_date, task.status)
        if countdown:
            self.setToolTip(countdown)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    def show_menu(self, pos):
        self.dashboard.show_kanban_context_menu(self.task, self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, event):
        """
        ISO 25010: Enhances Usability. Opens the edit dialog on double-click.
        """
        self.dashboard.edit_specific_task(self.task.id)

    def sizeHint(self):
        return QSize(200, super().sizeHint().height())
