"""
Archive Widget for the Efficio Dashboard (FT05).

Provides a self-contained QWidget that renders archived tasks with a
distinctive faded aesthetic, a restore button, and a permanent delete option.

Lifecycle:
    Active -> Archived (after 3 days if Completed, or manually) ->
    Trash (after 14 days in archive) -> Permanently Deleted (after 14 days in trash).

ISO 25010 Compliance:
    - Modifiability: Self-contained widget, cleanly separated from the Dashboard.
    - Usability: Faded card style makes it instantly clear the user is in the Archive.
"""

from datetime import datetime
import qtawesome as qta

from PySide6.QtCore import Qt
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


class ArchiveWidget(QWidget):
    """Self-contained Archive view for the Efficio Dashboard.

    Renders archived tasks with a muted, faded style and provides context
    menu actions for restoration (back to active) and permanent deletion.
    """

    def __init__(self, dashboard) -> None:
        """Initialise the widget and build layout.

        Args:
            dashboard: The main DashboardInterface (for access to task_manager).
        """
        super().__init__()
        self.dashboard = dashboard
        self.task_manager = dashboard.task_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ── Header ──────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_label = QLabel("🗂️  Archive")
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)

        info_label = QLabel("Tasks are auto-archived after 3 days of completion")
        info_label.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.4); font-style: italic;"
        )
        header_layout.addWidget(info_label)
        header_layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search archived tasks...")
        self.search_bar.setFixedWidth(250)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 8px; border-radius: 10px;
                background-color: rgba(255,255,255,0.1); color: white;
            }
            QLineEdit:hover { background-color: rgba(255,255,255,0.15); }
        """)
        self.search_bar.textChanged.connect(self.refresh)
        header_layout.addWidget(self.search_bar)

        layout.addLayout(header_layout)

        # ── Tree Widget ─────────────────────────────────────────────────────
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderHidden(False)
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.setHeaderLabels(
            ["#", "Task Title", "Status", "Priority", "Archived On"]
        )
        self.task_tree.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.task_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.task_tree.setAlternatingRowColors(False)
        self.task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_tree.customContextMenuRequested.connect(self._show_context_menu)

        # Column sizing
        header = self.task_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.task_tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 10px 6px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }
            QTreeWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
            }
            QHeaderView::section {
                background-color: rgba(255,255,255,0.06);
                color: rgba(255,255,255,0.8);
                padding: 6px;
                border: none;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)

        layout.addWidget(self.task_tree)

    def refresh(self) -> None:
        """Reload archived tasks from the database and re-render the list."""
        query = self.search_bar.text() if hasattr(self, "search_bar") else ""
        tasks = self.task_manager.get_archived_tasks(query)
        self.task_tree.clear()

        if not tasks:
            empty = QTreeWidgetItem(["", "  No archived tasks found.", "", "", ""])
            empty.setForeground(1, QColor("rgba(255,255,255,0.3)"))
            self.task_tree.addTopLevelItem(empty)
            return

        for i, task in enumerate(tasks, start=1):
            # Format the archived_at timestamp
            archived_str = "—"
            if task.archived_at:
                try:
                    for fmt in (
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d",
                    ):
                        try:
                            dt = datetime.strptime(task.archived_at, fmt)
                            archived_str = dt.strftime("%b %d, %Y")
                            break
                        except ValueError:
                            continue
                except Exception:
                    archived_str = str(task.archived_at)

            item = QTreeWidgetItem(
                [
                    str(i),
                    f"  {task.title}",
                    task.status,
                    task.priority or "—",
                    archived_str,
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, task)

            # Priority color badge
            priority_colors = {
                "Critical": QColor(255, 80, 80),
                "High": QColor(255, 165, 0),
                "Medium": QColor(255, 215, 0),
                "Low": QColor(144, 238, 144),
            }
            p_color = priority_colors.get(task.priority, QColor(200, 200, 200))
            item.setForeground(3, p_color)

            self.task_tree.addTopLevelItem(item)

    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu for archive actions."""
        item = self.task_tree.itemAt(pos)
        if not item:
            return
        task = item.data(0, Qt.ItemDataRole.UserRole)
        if not task:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1f2e;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
                padding: 4px;
                color: white;
            }
            QMenu::item { padding: 8px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: rgba(255,255,255,0.1); }
        """)

        restore_action = menu.addAction(
            qta.icon("fa5s.undo", color="#A0A0A0"), "Restore to Active"
        )
        menu.addSeparator()
        delete_action = menu.addAction(
            qta.icon("fa5s.trash-alt", color="#A0A0A0"), "Move to Trash"
        )

        action = menu.exec(self.task_tree.viewport().mapToGlobal(pos))

        if action == restore_action:
            self.task_manager.restore_from_archive(task.id)
            self.refresh()
            if hasattr(self.dashboard, "load_tasks"):
                self.dashboard.load_tasks()
        elif action == delete_action:
            confirm = QMessageBox.question(
                self,
                "Move to Trash",
                f"Move '{task.title}' to the Trash Bin?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task.id)
                self.refresh()
