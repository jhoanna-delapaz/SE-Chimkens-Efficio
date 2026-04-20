"""
Analytics Widget for the Efficio Dashboard.

Provides a self-contained QWidget that renders three productivity metric
sections — a completion ratio donut chart, a priority distribution bar panel,
and an overdue KPI chip — inside a scrollable glassmorphism card.

ISO 25010 Compliance:
    - Modifiability: Each section is a private builder method; adding a new
      metric requires adding one method and one call in refresh().
    - Functional Suitability: Data is consumed via a plain dict from
      TaskManager.get_task_stats(), keeping this widget DB-agnostic.
    - Usability: Empty-state labels guide the user when no data is available.
"""

from PySide6.QtCharts import QChart, QChartView, QPieSlice, QPieSeries
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ── Colour palette aligned with ACTIVE_THEME_MAP in dashboard.py ──────────────
_STATUS_COLOURS = {
    "Pending": ("#6579BE", "#EAB099"),  # bg_hex, label_hex
    "In Progress": ("#92736C", "#FDF1F5"),
    "Completed": ("#285B23", "#F2CFF1"),
}

_PRIORITY_COLOURS = {
    "Low": "#6579BE",
    "Medium": "#8A6729",
    "High": "#F54800",
    "Critical": "#FF4D4D",
}

_CARD_STYLE = """
    QFrame {
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
"""

_SECTION_TITLE_STYLE = (
    "color: rgba(255,255,255,0.7); font-size: 11px; "
    "font-weight: bold; letter-spacing: 1px;"
)


class AnalyticsWidget(QWidget):
    """Self-contained analytics panel for the Efficio Dashboard right-sidebar.

    Renders three productivity metric sections:

    1. **Completion Donut** — QPieSeries breakdown of task status.
    2. **Priority Bars** — Styled QProgressBar rows per priority level.
    3. **Overdue Chip** — KPI badge flagging past-due tasks.

    The widget owns all internal layout logic. The caller (DashboardInterface)
    only needs to call :meth:`refresh` after any task mutation.

    Example:
        >>> widget = AnalyticsWidget()
        >>> widget.refresh(task_manager)   # called inside load_tasks()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the widget and build static layout scaffolding.

        Args:
            parent: Optional parent widget passed through to QWidget.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ── Outer frame (glassmorphism card) ──────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QFrame()
        card.setStyleSheet(_CARD_STYLE)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(12)

        # Panel title
        title = QLabel("📊  Performance")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        card_layout.addWidget(title)

        # ── Scrollable inner area (enables adding more metrics freely) ────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: rgba(0,0,0,0.2); width: 6px; "
            "border-radius: 3px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.3); "
            "border-radius: 3px; }"
        )

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(14)

        scroll.setWidget(self._inner)
        card_layout.addWidget(scroll)
        outer.addWidget(card)

        # ── Build placeholder sections (populated on first refresh) ───────────
        self._donut_container = self._make_section_container()
        self._priority_container = self._make_section_container()
        self._overdue_container = self._make_section_container()

        self._inner_layout.addWidget(self._donut_container)
        self._inner_layout.addWidget(self._priority_container)
        self._inner_layout.addWidget(self._overdue_container)
        self._inner_layout.addStretch()

        # Render with zero-data empty state immediately
        self._render_empty_state()

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self, task_manager) -> None:
        """Re-render all metric sections using the latest database snapshot.

        Calls ``task_manager.get_task_stats()`` and pipes the resulting dict
        into each builder method. Designed to be called at the end of
        ``DashboardInterface.load_tasks()`` with zero overhead.

        Args:
            task_manager: An instance of ``business.task_manager.TaskManager``.
        """
        stats = task_manager.get_task_stats()
        self._clear_container(self._donut_container)
        self._clear_container(self._priority_container)
        self._clear_container(self._overdue_container)

        if stats["total"] == 0:
            self._render_empty_state()
            return

        self._build_donut_section(stats)
        self._build_priority_bars(stats)
        self._build_overdue_chip(stats)

    # ── Private builder methods ────────────────────────────────────────────────

    def _build_donut_section(self, stats: dict) -> None:
        """Render the QPieSeries donut chart into the donut container.

        Creates one pie slice per status (Pending / In Progress / Completed)
        using glassmorphism-alpha fill colours from the ACTIVE_THEME_MAP
        palette. Slices with zero count are omitted to keep the chart clean.

        Args:
            stats: Aggregate dict from ``TaskManager.get_task_stats()``.
        """
        layout = self._donut_container.layout()

        lbl = QLabel("COMPLETION RATIO")
        lbl.setStyleSheet(_SECTION_TITLE_STYLE)
        layout.addWidget(lbl)

        series = QPieSeries()
        series.setHoleSize(0.55)

        for status, (bg_hex, _label_hex) in _STATUS_COLOURS.items():
            count = stats.get(status, 0)
            if count == 0:
                continue
            slc = series.append(f"{status}  {count}", count)
            colour = QColor(bg_hex)
            colour.setAlpha(180)
            slc.setBrush(colour)
            slc.setLabelColor(QColor("white"))
            slc.setLabelVisible(True)
            slc.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)

        chart = QChart()
        chart.addSeries(series)
        chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setVisible(False)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet("background: transparent; border: none;")
        view.setFixedHeight(180)

        layout.addWidget(view)

    def _build_priority_bars(self, stats: dict) -> None:
        """Render one styled QProgressBar row per priority level.

        Bar value is expressed as a percentage of total active tasks, giving
        an instant visual sense of workload distribution. Zero-count priorities
        are still rendered at 0% to maintain layout consistency.

        Args:
            stats: Aggregate dict from ``TaskManager.get_task_stats()``.
        """
        layout = self._priority_container.layout()

        lbl = QLabel("PRIORITY DISTRIBUTION")
        lbl.setStyleSheet(_SECTION_TITLE_STYLE)
        layout.addWidget(lbl)

        total = max(stats["total"], 1)  # Guard zero-division

        for priority, hex_colour in _PRIORITY_COLOURS.items():
            count = stats.get(priority, 0)
            pct = int((count / total) * 100)

            row = QHBoxLayout()
            row.setSpacing(8)

            name_lbl = QLabel(priority)
            name_lbl.setFixedWidth(55)
            name_lbl.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 11px;")
            row.addWidget(name_lbl)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255,255,255,0.1);
                    border-radius: 4px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {hex_colour};
                    border-radius: 4px;
                }}
            """)
            row.addWidget(bar, stretch=1)

            count_lbl = QLabel(str(count))
            count_lbl.setFixedWidth(18)
            count_lbl.setStyleSheet(
                "color: rgba(255,255,255,0.55); font-size: 11px; font-weight: bold;"
            )
            count_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            row.addWidget(count_lbl)

            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_w.setLayout(row)
            layout.addWidget(row_w)

    def _build_overdue_chip(self, stats: dict) -> None:
        """Render the overdue KPI pill badge into the overdue container.

        Displays a red warning pill when overdue tasks exist, or a calm
        green confirmation chip when all tasks are within schedule. Reuses
        the same due-date detection logic established in FT04 (urgency UI).

        Args:
            stats: Aggregate dict from ``TaskManager.get_task_stats()``.
        """
        layout = self._overdue_container.layout()

        lbl = QLabel("OVERDUE STATUS")
        lbl.setStyleSheet(_SECTION_TITLE_STYLE)
        layout.addWidget(lbl)

        overdue = stats.get("overdue", 0)

        if overdue > 0:
            text = f"⚠  {overdue} task{'s' if overdue > 1 else ''} overdue"
            chip_style = (
                "background-color: rgba(255, 77, 77, 0.25); "
                "color: #FF4D4D; "
                "border: 1px solid rgba(255, 77, 77, 0.5); "
                "border-radius: 10px; padding: 6px 12px; font-size: 12px; font-weight: bold;"
            )
        else:
            text = "✓  All tasks on schedule"
            chip_style = (
                "background-color: rgba(40, 91, 35, 0.3); "
                "color: #A8D5A2; "
                "border: 1px solid rgba(40, 91, 35, 0.5); "
                "border-radius: 10px; padding: 6px 12px; font-size: 12px; font-weight: bold;"
            )

        chip = QLabel(text)
        chip.setStyleSheet(chip_style)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setObjectName("overdue_chip")
        layout.addWidget(chip)

    def _render_empty_state(self) -> None:
        """Render a friendly placeholder when the task database is empty.

        Called on first initialisation and whenever refresh() receives a
        zero-task stats dict. Clears all three containers and injects a
        single centred label with premium typography.
        """
        for container in (
            self._donut_container,
            self._priority_container,
            self._overdue_container,
        ):
            self._clear_container(container)

        layout = self._donut_container.layout()
        empty_lbl = QLabel("No tasks yet\nStart planning to see insights!")
        empty_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.35); font-size: 13px; font-style: italic;"
        )
        empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_lbl.setObjectName("empty_state_label")
        layout.addWidget(empty_lbl)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_section_container() -> QFrame:
        """Create a transparent QFrame used as a section slot in the scroll area.

        Returns:
            QFrame: An empty container with a vertical layout and no border.
        """
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        return frame

    @staticmethod
    def _clear_container(container: QFrame) -> None:
        """Remove all child widgets from a section container without memory leaks.

        Uses ``deleteLater()`` to safely schedule PySide6 widget destruction
        on the next event-loop cycle, preventing dangling C++ object references.

        Args:
            container: The QFrame whose layout children will be cleared.
        """
        layout = container.layout()
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
