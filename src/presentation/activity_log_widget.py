"""
Activity Log Widget for the Efficio Dashboard.

Provides a scrollable timeline of task actions with:
- Phase 2: Real-time filter bar (text search + action type dropdown)
- Phase 3: Per-entry revert button to undo status changes and edits

ISO 25010:
    - Functional Suitability: Covers all task lifecycle events.
    - Usability: Color-coded entries with clear typography.
    - Maintainability: Each item is a self-contained ActivityLogItem.
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Qt, QDate, QSize, Signal, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from data.models import ActivityLog

# ── Color mapping per action ───────────────────────────────────────────────────
ACTION_COLORS = {
    "Created": "#4CAF50",  # Green
    "Edited": "#2196F3",  # Blue
    "Status Changed": "#FF9800",  # Orange
    "Moved to Trash": "#f44336",  # Red
    "Restored": "#9C27B0",  # Purple
    "Permanently Deleted": "#607D8B",  # Slate
    "Reverted": "#00BCD4",  # Cyan
}
_DEFAULT_COLOR = "#A0A0A0"


class ActivityLogWidget(QWidget):
    """
    Full Activity Log view with search, filter, and revert capabilities.
    """

    request_more = Signal(int)  # Emits the new limit requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_logs: List[ActivityLog] = []
        self._on_revert: Optional[Callable] = None
        self._current_limit = 100
        self._setup_ui()

    def set_revert_callback(self, callback: Callable):
        """Bind a callback(log: ActivityLog) -> bool used when revert is clicked."""
        self._on_revert = callback

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ── Header ────────────────────────────────────────────────────────────
        header_container = QVBoxLayout()
        header_container.setSpacing(2)

        title = QLabel("Activity History")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")

        subtitle = QLabel("Showing latest 100 entries • 30-day retention policy")
        subtitle.setStyleSheet(
            "font-size: 11px; color: rgba(255, 255, 255, 0.4); font-style: italic;"
        )

        header_container.addWidget(title)
        header_container.addWidget(subtitle)

        layout.addLayout(header_container)

        # ── Heatmap Header Card ───────────────────────────────────────────────
        self.heatmap_card = QFrame()
        self.heatmap_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        self.heatmap_layout = QVBoxLayout(self.heatmap_card)
        self.heatmap_layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(self.heatmap_card)

        # ── Phase 2: Filter Bar ───────────────────────────────────────────────
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search task name or details...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px; padding: 7px 12px;
                color: white; font-size: 13px;
            }
            QLineEdit:focus { border-color: rgba(255,255,255,0.4); }
        """)
        self.search_box.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search_box, stretch=2)

        self.action_filter = QComboBox()
        self.action_filter.addItem("All Actions", None)
        for action in ACTION_COLORS.keys():
            self.action_filter.addItem(action, action)
        self.action_filter.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px; padding: 7px 12px;
                color: white; font-size: 13px; min-width: 140px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e2328; color: white;
                selection-background-color: #2d333b;
            }
        """)
        self.action_filter.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.action_filter)

        layout.addLayout(filter_bar)

        # ── Scroll Area ───────────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.content = QWidget()
        self.timeline_layout = QVBoxLayout(self.content)
        self.timeline_layout.setContentsMargins(10, 10, 10, 10)
        self.timeline_layout.setSpacing(15)
        self.timeline_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def refresh(self, logs: List[ActivityLog], activity_counts: dict = None):
        """Load a fresh set of logs and re-render."""
        self._all_logs = logs
        if activity_counts is not None:
            self._build_heatmap(activity_counts)

        self._apply_filters()

    def _on_load_more(self):
        self._current_limit += 100
        self.request_more.emit(self._current_limit)

    def _build_heatmap(self, counts: dict):
        """Phase 4: Render the activity heatmap in the header card."""
        # Clear existing
        while self.heatmap_layout.count():
            item = self.heatmap_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lbl = QLabel("ACTIVITY (LAST 52 WEEKS)")
        lbl.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold; letter-spacing: 1px;"
        )
        self.heatmap_layout.addWidget(lbl)

        today = QDate.currentDate()
        days_since_monday = today.dayOfWeek() - 1
        grid_start = today.addDays(-(52 * 7 - 1 + days_since_monday))

        def day_color(count: int) -> str:
            if count == 0:
                return "rgba(255,255,255,0.06)"
            intensity = min(count / 5.0, 1.0)
            r = 0
            g = int(100 + intensity * 112)
            b = int(120 + intensity * 80)
            alpha = int(80 + intensity * 175)
            return f"rgba({r},{g},{b},{alpha})"

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(3)
        grid.setContentsMargins(0, 10, 0, 10)

        for row_idx, name in enumerate(["Mon", "", "Wed", "", "Fri", "", "Sun"]):
            if name:
                d_lbl = QLabel(name)
                d_lbl.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 9px;")
                grid.addWidget(d_lbl, row_idx, 0)

        current = grid_start
        col = 1
        while current <= today:
            row = current.dayOfWeek() - 1
            date_str = current.toString("yyyy-MM-dd")
            count = counts.get(date_str, 0)

            cell = QLabel()
            cell.setFixedSize(QSize(12, 12))
            cell.setStyleSheet(
                f"background-color: {day_color(count)}; border-radius: 2px;"
            )
            if count > 0:
                cell.setToolTip(
                    f"{date_str}: {count} action{'s' if count != 1 else ''}"
                )

            grid.addWidget(cell, row, col)
            current = current.addDays(1)
            if current.dayOfWeek() == 1:
                col += 1

        grid.setColumnStretch(col + 1, 1)
        self.heatmap_layout.addWidget(grid_widget)

        # Legend
        legend = QHBoxLayout()
        legend.addStretch()
        for label, color in [
            ("Less", "rgba(255,255,255,0.06)"),
            ("", "rgba(0,140,120,100)"),
            ("", "rgba(0,180,160,180)"),
            ("More", "rgba(0,212,200,255)"),
        ]:
            if label:
                lbl_legend = QLabel(label)
                lbl_legend.setStyleSheet(
                    "color: rgba(255,255,255,0.4); font-size: 10px;"
                )
                legend.addWidget(lbl_legend)
            box = QLabel()
            box.setFixedSize(QSize(10, 10))
            box.setStyleSheet(f"background:{color}; border-radius: 2px;")
            legend.addWidget(box)
        self.heatmap_layout.addLayout(legend)

    def _apply_filters(self):
        """Phase 2: Filter by search text and action type, then re-render."""
        query = self.search_box.text().lower().strip()
        action_sel = self.action_filter.currentData()

        filtered = self._all_logs
        if query:
            filtered = [
                log
                for log in filtered
                if query in log.task_title.lower()
                or query in (log.details or "").lower()
            ]
        if action_sel:
            filtered = [log for log in filtered if log.action == action_sel]

        self._render(filtered)

    def _render(self, logs: List[ActivityLog]):
        # Save current scroll position
        vbar = self.scroll.verticalScrollBar()
        old_val = vbar.value()

        # Clear existing
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not logs:
            lbl = QLabel("No matching activity found.")
            lbl.setStyleSheet("color: #808080; font-style: italic; font-size: 14px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.timeline_layout.addWidget(lbl)
            return

        for log in logs:
            item = ActivityLogItem(log, revert_callback=self._handle_revert)
            self.timeline_layout.addWidget(item)

        # Dynamically append the Load More button at the very bottom of the scroll list
        if len(self._all_logs) >= self._current_limit and len(logs) == len(
            self._all_logs
        ):
            load_more_btn = QPushButton("Load More Activities")
            load_more_btn.setFixedWidth(200)
            load_more_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 8px; padding: 10px; margin-top: 10px;
                    color: rgba(255,255,255,0.7); font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.1);
                    color: white;
                }
            """)
            load_more_btn.clicked.connect(self._on_load_more)

            # Wrap in a horizontal layout to center it
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.addWidget(load_more_btn)

            self.timeline_layout.addWidget(btn_container)

        # Restore scroll position after layout updates
        if old_val > 0:
            QTimer.singleShot(50, lambda v=old_val: vbar.setValue(v))

    def _handle_revert(self, log: ActivityLog):
        """Phase 3: Dispatch revert to the registered callback."""
        if not self._on_revert:
            QMessageBox.warning(self, "Revert", "Revert is not available.")
            return
        if not log.snapshot:
            QMessageBox.information(
                self,
                "Revert",
                "This action cannot be reverted (no snapshot available).",
            )
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Revert",
            f"Revert '{log.task_title}' to its state before this action?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success = self._on_revert(log)
            if success:
                QMessageBox.information(
                    self,
                    "Reverted",
                    f"'{log.task_title}' has been reverted successfully.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Revert Failed",
                    "Could not revert this action. The task may have been deleted.",
                )


class ActivityLogItem(QFrame):
    """Single log entry card with color-coded action indicator and revert button."""

    def __init__(self, log: ActivityLog, revert_callback: Optional[Callable] = None):
        super().__init__()
        self.log = log
        self._revert_callback = revert_callback
        self._setup_ui()

    def _setup_ui(self):
        accent = ACTION_COLORS.get(self.log.action, _DEFAULT_COLOR)
        self.setObjectName("LogItem")
        self.setStyleSheet(f"""
            #LogItem {{
                background-color: rgba(255,255,255,0.05);
                border-radius: 8px;
                border-left: 4px solid {accent};
            }}
            #LogItem:hover {{
                background-color: rgba(255,255,255,0.08);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # ── Top row: action badge + timestamp + revert button ─────────────────
        top = QHBoxLayout()

        action_lbl = QLabel(self.log.action.upper())
        action_lbl.setStyleSheet(
            f"color: {accent}; font-weight: bold; font-size: 10px; letter-spacing: 1px;"
        )
        top.addWidget(action_lbl)
        top.addStretch()

        time_lbl = QLabel(self.log.timestamp.strftime("%b %d, %Y — %I:%M %p"))
        time_lbl.setStyleSheet("color: #ffffff; font-size: 11px;")
        top.addWidget(time_lbl)

        # Phase 3: Revert button — only shown for revertable actions
        revertable = {"Edited", "Status Changed"}
        if self.log.action in revertable and self.log.snapshot:
            revert_btn = QPushButton("↩ Revert")
            revert_btn.setFixedHeight(22)
            revert_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent};
                    color: white;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background-color: {accent};
                    border: 1px solid white;
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.2);
                }}
            """)
            revert_btn.clicked.connect(
                lambda: (
                    self._revert_callback(self.log) if self._revert_callback else None
                )
            )
            top.addSpacing(8)
            top.addWidget(revert_btn)

        layout.addLayout(top)

        # ── Task title ────────────────────────────────────────────────────────
        title_lbl = QLabel(self.log.task_title)
        title_lbl.setStyleSheet("color: white; font-size: 15px; font-weight: 500;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        # ── Details (field-level diff) ────────────────────────────────────────
        if self.log.details and self.log.details != "No significant changes":
            details_lbl = QLabel(self.log.details)
            details_lbl.setStyleSheet("color: #909090; font-size: 12px;")
            details_lbl.setWordWrap(True)
            layout.addWidget(details_lbl)
