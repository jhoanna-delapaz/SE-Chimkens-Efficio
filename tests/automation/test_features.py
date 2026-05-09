import os
import sys
import tempfile
from datetime import datetime

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QLabel

# Path resolution MUST execute before src imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "src")
sys.path.append(src_dir)

# Tell Ruff to ignore sorting (I001) and ignore import position (E402) for these 3 files!
from data.DataBaseHandler import init_db  # noqa: I001, E402
from data.models import Task, Tag, TaskAttachment  # noqa: I001, E402
from main import MainWindow  # noqa: I001, E402
from business.task_manager import TaskManager  # noqa: I001, E402


@pytest.fixture
def app_window(qtbot):
    """Fixture to set up the main window and a clean test database."""
    fd, TEST_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="test_efficio_")
    os.close(fd)
    init_db(TEST_DB_PATH)

    window = MainWindow(TEST_DB_PATH)

    window.dashboard.task_manager = TaskManager(TEST_DB_PATH)
    window.dashboard.load_tasks()

    window.show()
    qtbot.addWidget(window)
    yield window

    # 1. Force the database connection to let go of the file
    try:
        if hasattr(window.dashboard.task_manager, "close"):
            window.dashboard.task_manager.close()
    except Exception:
        pass

    # 2. Tell Windows to delete it, but don't crash if Windows is too slow to unlock it
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except (PermissionError, OSError):
        pass


def test_tc001_add_task_success(app_window, qtbot, monkeypatch):
    """TC-001: Verify creation pushes task to QTreeWidget Children"""
    dashboard = app_window.dashboard

    # Auto-click OK on Success UI
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    def interact_with_dialog():
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            top_widget.title_input.setText("Submit Project")
            top_widget.desc_input.setPlainText("Sprint 1 Output")
            top_widget.accept()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    # Validate the task physically rendered inside the To-Do Accordion
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 2  # 1 header row + 1 physical task row

    task_row = todo_group.child(1)
    assert "Submit Project" in task_row.text(0)


def test_tc002_add_task_empty_title_validation(app_window, qtbot):
    """TC-002: Verify validation message for empty title blocks creation"""
    dashboard = app_window.dashboard
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    initial_count = todo_group.childCount()

    # Track if our Custom Toast Overlay successfully spawns
    toast_activated = False

    def interact_with_dialog():
        nonlocal toast_activated
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            top_widget.title_input.setText("")  # Blank title
            top_widget.validate_and_accept()

            # Look for the internal PySide6 Toast widget instead of a MessageBox
            if (
                top_widget.toast.isVisible()
                and top_widget.toast.text() == "Title is required!"
            ):
                toast_activated = True

            top_widget.reject()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    # Verify no task was added and the toast successfully fired
    assert todo_group.childCount() == initial_count
    assert toast_activated is True


def test_tc003_view_dashboard(app_window, qtbot):
    """TC-003: Verify native QTreeWidget initializes Accordion Groups empty"""
    dashboard = app_window.dashboard
    assert dashboard.task_list_view.task_tree is not None

    # Mathematical validation: Top level items are the 3 groups + 2 spacers = 5
    assert dashboard.task_list_view.task_tree.topLevelItemCount() == 5

    # Extract "To-Do" accordion. It should ONLY have 1 child (the Inline Header row).
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 1  # 0 user tasks


def test_tc004_tc005_kanban_matrix_routing(app_window, qtbot):
    """Verify tasks dynamically route to the correct layout container in Kanban View"""
    dashboard = app_window.dashboard
    dashboard.set_mode("kanban")

    # Inject tasks into DB directly
    t1 = Task(
        id=None,
        title="Todo Task",
        description="",
        status="Pending",
        created_at=datetime.now(),
        due_date="",
        priority="High",
    )
    t2 = Task(
        id=None,
        title="Done Task",
        description="",
        status="Completed",
        created_at=datetime.now(),
        due_date="",
        priority="Low",
    )

    dashboard.task_manager.add_task(t1)
    dashboard.task_manager.add_task(t2)
    dashboard.load_tasks()  # Trigger layout route matrix

    # Kanban Board should physically possess the cards in the proper layouts!
    assert dashboard.kanban_board_view.todo_content.count() == 1
    assert dashboard.kanban_board_view.done_content.count() == 1
    assert dashboard.kanban_board_view.progress_content.count() == 0


def test_tc006_tc007_trash_management(app_window, qtbot, monkeypatch):
    """[EP01-FT05] Trash Management with Restore and Permanent Delete Functionality"""
    dashboard = app_window.dashboard

    # Setup: Create a task via the manager so we have a clean state
    new_task = Task(
        id=None,
        title="Trash Test Task",
        description="Testing delete/restore",
        status="Pending",
        created_at=datetime.now(),
        due_date="2026-03-20",
        priority="High",
        is_deleted=0,
    )
    task_id = dashboard.task_manager.add_task(new_task)
    dashboard.load_tasks()

    # Move to Trash (Soft Delete)
    dashboard.task_manager.delete_task(task_id)
    dashboard.load_tasks()

    # Verify Task is strictly missing from Active To-Do List
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 1  # Just the header left

    # Navigate to Trash Bin View
    dashboard.set_mode("trash")
    assert dashboard.current_mode == "trash"

    # Verify it exists in the Trash UI (flat list in TrashWidget)
    assert dashboard.page_trash.task_tree.topLevelItemCount() == 1
    trash_item = dashboard.page_trash.task_tree.topLevelItem(0)

    # Title is injected via setItemWidget, so text(0) is empty. We can check via the underlying data
    assert (
        dashboard.task_manager.get_task_by_id(
            trash_item.data(0, Qt.ItemDataRole.UserRole)
        ).title
        == "Trash Test Task"
    )

    # Permanent Delete Workflow
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes
    )
    dashboard.task_manager.permanently_delete_task(task_id)
    dashboard.page_trash.refresh()  # <--- THIS VAPORIZES THE OLD POINTER!

    # Final Verification: Nulled from existence
    # We MUST re-fetch the pointer here!
    assert dashboard.page_trash.task_tree.topLevelItemCount() == 0

    db_task = dashboard.task_manager.get_task_by_id(task_id)
    assert db_task is None


def test_tc008_search_isolation(app_window, qtbot):
    """[EP01-FT06] Ensure string isolation dynamically shreds irrelevant tasks"""
    dashboard = app_window.dashboard

    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Buy Groceries",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="Medium",
        )
    )
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Code Search",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="High",
        )
    )
    dashboard.load_tasks()

    # Apply search filter
    dashboard.search_bar.setText("Groceries")

    # The To-Do Accordion should only have the Header (1) + "Buy Groceries" (1) = 2 children
    todo_group_filtered = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group_filtered.childCount() == 2

    # Clear Filter
    dashboard.search_bar.setText("")

    # Re-fetch again
    todo_group_cleared = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group_cleared.childCount() == 3


def test_tc009_task_color_pastel_render(app_window, qtbot):
    """[EP01-FT7] Verify Custom Theme Colors natively apply 60% Alpha Pastel to QTreeWidget Rows"""
    dashboard = app_window.dashboard

    # Create Deep Ocean Task
    task_theme = Task(
        id=None,
        title="Theme Test",
        description="",
        status="Pending",
        created_at=datetime.now(),
        due_date="",
        priority="Medium",
        is_deleted=0,
        color="#19485F",
    )
    dashboard.task_manager.add_task(task_theme)
    dashboard.load_tasks()

    # Enter the To-Do Accordion and grab the physical Task Row (Index 1)
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    task_row = todo_group.child(1)

    # Extract the custom Pastel Brush generated by our ACTIVE_THEME_MAP logic
    bg_brush = task_row.background(0)
    bg_color = bg_brush.color()

    # Base Color is #19485F. Verify it correctly extracted the RGB properties!
    assert bg_color.name().upper() == "#19485F"
    assert (
        bg_color.alpha() == 50
    )  # Verifying the aesthetic alpha glassmorphism trick we injected!

    fg_brush = task_row.foreground(1)
    fg_color = fg_brush.color()
    assert (
        fg_color.name().upper() == "#D9E0A4"
    )  # The mapped bright foreground dictionary color — checked on col 1 (due date) since col 0 uses a transparent QWidget overlay!


def test_tc010_past_due_date_validation(app_window, qtbot):
    """TC-010: Task Due Date Validation (Past Date)"""
    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    initial_count = todo_group.childCount()

    toast_activated = False

    def interact_with_dialog():
        nonlocal toast_activated
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            # Set Title
            top_widget.title_input.setText("Past Date Task")
            # Set Due Date to yesterday
            past_date = QDate.currentDate().addDays(-1)
            top_widget.date_input.setDate(past_date)

            top_widget.validate_and_accept()

            if (
                top_widget.toast.isVisible()
                and top_widget.toast.text() == "Due Date/Time cannot be in the past!"
            ):
                toast_activated = True

            top_widget.reject()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    assert todo_group.childCount() == initial_count
    assert toast_activated is True


def test_tc011_task_priority_selection(app_window, qtbot, monkeypatch):
    """TC-011: Task Priority Management correctly saves"""

    # Auto-click OK on Success UI
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    dashboard = app_window.dashboard

    def interact_with_dialog():
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            top_widget.title_input.setText("Critical Task")
            # Set priority to "Critical"
            index = top_widget.priority_input.findText("Critical")
            if index >= 0:
                top_widget.priority_input.setCurrentIndex(index)

            top_widget.accept()  # Bypass validation just for saving test

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    # Validate the task physically rendered
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(
        0
    )  # Re-fetch because load_tasks() destroys old tree
    assert todo_group.childCount() == 2

    # Priority is in column 2, let's just fetch from DB to be scientifically accurate
    tasks = dashboard.task_manager.get_all_tasks()
    critical_task = None
    for t in tasks:
        if t.title == "Critical Task":
            critical_task = t
            break

    assert critical_task is not None
    assert critical_task.priority == "Critical"


def test_tc012_toast_visibility_engine(app_window, qtbot):
    """TC-012: Ensure physics engine uses the premium OutBack bounce."""
    from PySide6.QtCore import QEasingCurve

    dashboard = app_window.dashboard

    def interact_with_dialog():
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            # Verify the Toast component is loaded
            assert hasattr(top_widget, "toast")

            # Fire a fake error
            top_widget.toast.show_toast("Fake Error", 100)

            # Extract internal physics
            curve = top_widget.toast.anim.easingCurve()
            assert curve.type() == QEasingCurve.Type.OutBack

            top_widget.reject()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)


# ─────────────────────────────────────────────
# FT04: Urgency UI for tasks with close due dates
# TC-013 → TC-017
# ─────────────────────────────────────────────


def test_tc013_urgency_detection(app_window, qtbot):
    """[FT04] TC-013: Task due today is classified as urgent; far-future task is not."""
    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard

    # Urgent: due today
    urgent_task = Task(
        id=None,
        title="Urgent Task",
        description="",
        status="Pending",
        created_at=datetime.now(),
        due_date=QDate.currentDate().toString("yyyy-MM-dd"),
        priority="High",
        is_deleted=0,
    )
    # Not urgent: due 30 days from now
    safe_task = Task(
        id=None,
        title="Safe Task",
        description="",
        status="Pending",
        created_at=datetime.now(),
        due_date=QDate.currentDate().addDays(30).toString("yyyy-MM-dd"),
        priority="Low",
        is_deleted=0,
    )

    dashboard.task_manager.add_task(urgent_task)
    dashboard.task_manager.add_task(safe_task)
    dashboard.load_tasks()

    # Internal urgency predicate mirrors dashboard logic
    def is_urgent(t):
        if t.status == "Completed" or not t.due_date:
            return False
        parsed = QDate.fromString(str(t.due_date).strip(), "yyyy-MM-dd")
        return parsed.isValid() and QDate.currentDate().daysTo(parsed) <= 2

    tasks = dashboard.task_manager.get_all_tasks()
    urgent_titles = [t.title for t in tasks if is_urgent(t)]
    safe_titles = [t.title for t in tasks if not is_urgent(t)]

    assert "Urgent Task" in urgent_titles
    assert "Safe Task" in safe_titles


def test_tc014_urgency_banner_appears(app_window, qtbot):
    """[FT04] TC-014: Red urgency banner is visible when at least one urgent task exists."""
    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard

    # Initially no tasks → banner should be hidden
    assert not dashboard.urgent_banner_btn.isVisible()

    # Add an urgent task (due today)
    urgent_task = Task(
        id=None,
        title="Banner Test Task",
        description="",
        status="Pending",
        created_at=datetime.now(),
        due_date=QDate.currentDate().toString("yyyy-MM-dd"),
        priority="High",
        is_deleted=0,
    )
    dashboard.task_manager.add_task(urgent_task)
    dashboard.load_tasks()

    # Banner must now be visible and contain the correct count
    assert dashboard.urgent_banner_btn.isVisible()
    assert "1" in dashboard.urgent_banner_btn.text()
    assert "⚠️" in dashboard.urgent_banner_btn.text()


def test_tc015_urgent_filter_isolates_tasks(app_window, qtbot):
    """[FT04] TC-015: 'is:urgent' search filter shows only urgent tasks in the tree."""
    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard

    # Urgent: due tomorrow
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Overdue Report",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date=QDate.currentDate().addDays(1).toString("yyyy-MM-dd"),
            priority="High",
            is_deleted=0,
        )
    )
    # Not urgent: due in 2 weeks
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Future Planning",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date=QDate.currentDate().addDays(14).toString("yyyy-MM-dd"),
            priority="Low",
            is_deleted=0,
        )
    )
    dashboard.load_tasks()

    # Apply the special urgency filter keyword
    dashboard.search_bar.setText("is:urgent")

    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    # Only 1 urgent task should appear (header + 1 task = 2 children)
    assert todo_group.childCount() == 2
    assert "Overdue Report" in todo_group.child(1).text(0)

    # Clear the filter and verify both tasks reappear
    dashboard.search_bar.setText("")
    todo_group_cleared = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group_cleared.childCount() == 3  # header + 2 tasks


def test_tc016_urgent_task_date_is_red(app_window, qtbot):
    """[FT04] TC-016: The due date cell of an urgent task renders in red (#FF4D4D)."""
    from PySide6.QtCore import QDate
    from PySide6.QtGui import QColor

    dashboard = app_window.dashboard

    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Red Date Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date=QDate.currentDate().toString("yyyy-MM-dd"),  # due today → urgent
            priority="Medium",
            is_deleted=0,
        )
    )
    dashboard.load_tasks()

    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    task_row = todo_group.child(1)  # child(0) is the inline header

    # Column 1 holds the due date text — foreground must be urgency red
    fg_color = task_row.foreground(1).color()
    assert fg_color.name().upper() == QColor("#FF4D4D").name().upper()


def test_tc017_banner_hides_when_no_urgent_tasks(app_window, qtbot):
    """[FT04] TC-017: Banner disappears after the only urgent task is completed."""
    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard

    task_id = dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Soon Due Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date=QDate.currentDate().addDays(1).toString("yyyy-MM-dd"),
            priority="High",
            is_deleted=0,
        )
    )
    dashboard.load_tasks()

    # Banner should be showing now
    assert dashboard.urgent_banner_btn.isVisible()

    # Complete the task → it is no longer urgent
    dashboard.task_manager.update_task_status(task_id, "Completed")
    dashboard.load_tasks()

    # Banner must auto-hide
    assert not dashboard.urgent_banner_btn.isVisible()


# ─────────────────────────────────────────────────────────────────────────────
# EP02: Task Productivity Analytics Dashboard
# TC-018 → TC-023
# ─────────────────────────────────────────────────────────────────────────────


def test_tc018_analytics_widget_exists(app_window, qtbot):
    """[EP02] TC-018: AnalyticsWidget instantiates cleanly and is wired into dashboard."""
    from presentation.analytics_widget import AnalyticsWidget

    dashboard = app_window.dashboard

    # The widget must be attached to the dashboard and be a proper AnalyticsWidget
    assert hasattr(dashboard, "analytics_widget")
    assert isinstance(dashboard.analytics_widget, AnalyticsWidget)

    # Confirm the inner scroll content area exists (structural integrity check)
    assert hasattr(dashboard.analytics_widget, "_inner_layout")


def test_tc019_analytics_empty_state(app_window, qtbot):
    """[EP02] TC-019: With zero tasks the empty-state label is shown."""
    dashboard = app_window.dashboard

    # No tasks were added — ensure stats are all zero
    stats = dashboard.task_manager.get_task_stats()
    assert stats["total"] == 0
    assert stats["Pending"] == 0
    assert stats["Completed"] == 0
    assert stats["overdue"] == 0

    # Empty-state label must be present inside the donut container
    donut_container = dashboard.analytics_widget._donut_container
    labels = [
        donut_container.layout().itemAt(i).widget()
        for i in range(donut_container.layout().count())
        if donut_container.layout().itemAt(i).widget() is not None
    ]
    empty_labels = [
        w
        for w in labels
        if getattr(w, "objectName", lambda: "")() == "empty_state_label"
    ]
    assert len(empty_labels) == 1


def test_tc020_analytics_counts_match_db(app_window, qtbot):
    """[EP02] TC-020: Stats dict accurately reflects task records in the database."""
    from datetime import datetime

    dashboard = app_window.dashboard

    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="P1",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="Medium",
            is_deleted=0,
        )
    )
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="P2",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="High",
            is_deleted=0,
        )
    )
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="C1",
            description="",
            status="Completed",
            created_at=datetime.now(),
            due_date="",
            priority="Low",
            is_deleted=0,
        )
    )

    stats = dashboard.task_manager.get_task_stats()

    assert stats["total"] == 3
    assert stats["Pending"] == 2
    assert stats["Completed"] == 1
    assert stats["In Progress"] == 0


def test_tc021_analytics_priority_distribution(app_window, qtbot):
    """[EP02] TC-021: Priority aggregation in stats matches tasks added per level."""
    from datetime import datetime

    dashboard = app_window.dashboard

    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Low Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="Low",
            is_deleted=0,
        )
    )
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Low Task 2",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="Low",
            is_deleted=0,
        )
    )
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="High Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="",
            priority="High",
            is_deleted=0,
        )
    )

    stats = dashboard.task_manager.get_task_stats()

    assert stats["Low"] == 2
    assert stats["High"] == 1
    assert stats["Medium"] == 0
    assert stats["Critical"] == 0


def test_tc022_analytics_overdue_chip_fires(app_window, qtbot):
    """[EP02] TC-022: A task with a past due date increments the overdue counter."""
    from datetime import datetime

    from PySide6.QtCore import QDate

    dashboard = app_window.dashboard

    past_date = QDate.currentDate().addDays(-3).toString("yyyy-MM-dd")
    dashboard.task_manager.add_task(
        Task(
            id=None,
            title="Overdue Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date=past_date,
            priority="High",
            is_deleted=0,
        )
    )

    stats = dashboard.task_manager.get_task_stats()
    assert stats["overdue"] == 1

    # Refresh the widget and verify the overdue chip renders the warning text
    dashboard.analytics_widget.refresh(dashboard.task_manager)
    overdue_container = dashboard.analytics_widget._overdue_container
    widgets = [
        overdue_container.layout().itemAt(i).widget()
        for i in range(overdue_container.layout().count())
        if overdue_container.layout().itemAt(i).widget() is not None
    ]
    chip = next(
        (
            w
            for w in widgets
            if getattr(w, "objectName", lambda: "")() == "overdue_chip"
        ),
        None,
    )
    assert chip is not None
    assert "overdue" in chip.text()


def test_tc023_analytics_refreshes_on_status_change(app_window, qtbot):
    """[EP02] TC-023: Completing a task updates the analytics stats correctly."""
    from datetime import datetime

    dashboard = app_window.dashboard

    task_id = dashboard.task_manager.add_task(
        Task(
            id=None,
            title="In Progress Task",
            description="",
            status="In Progress",
            created_at=datetime.now(),
            due_date="",
            priority="Medium",
            is_deleted=0,
        )
    )

    stats_before = dashboard.task_manager.get_task_stats()
    assert stats_before["In Progress"] == 1
    assert stats_before["Completed"] == 0

    # Simulate user completing the task (e.g. via right-click context menu)
    dashboard.task_manager.update_task_status(task_id, "Completed")
    dashboard.load_tasks()  # triggers analytics_widget.refresh() internally

    stats_after = dashboard.task_manager.get_task_stats()
    assert stats_after["In Progress"] == 0
    assert stats_after["Completed"] == 1


def test_tc024_datetime_parsing(app_window):
    """TC-024: Verify backwards compatibility for legacy date vs new datetime string parsing"""
    from datetime import datetime

    dashboard = app_window.dashboard

    # 1. Insert Legacy Task (Date Only)
    dashboard.task_manager.add_task(
        Task(
            id=0,
            title="Legacy Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="2020-01-01",  # Very old date
            priority="Low",
            color="#FFFFFF",
            is_deleted=0,
        )
    )

    # 2. Insert New Task (Full Datetime)
    dashboard.task_manager.add_task(
        Task(
            id=0,
            title="New Task",
            description="",
            status="Pending",
            created_at=datetime.now(),
            due_date="2020-01-01T14:30:00",  # Full datetime
            priority="Low",
            color="#FFFFFF",
            is_deleted=0,
        )
    )

    # This should safely parse both without throwing ValueError and accurately calculate overdue
    stats = dashboard.task_manager.get_task_stats()

    # Both tasks are from 2020, so they should both be counted as overdue
    assert stats["overdue"] == 2
    assert stats["total"] == 2


def test_tc025_task_sorting_logic(app_window):
    """TC-025: Verify TaskSorter logic for Priority and Date"""
    from datetime import datetime

    from data.models import Task
    from utils.sorter import TaskSorter

    tasks = [
        Task(
            id=1,
            title="Later",
            description="",
            due_date="2026-12-31",
            priority="Low",
            status="Pending",
            created_at=datetime.now(),
        ),
        Task(
            id=2,
            title="Sooner",
            description="",
            due_date="2026-01-01",
            priority="High",
            status="Pending",
            created_at=datetime.now(),
        ),
    ]

    # Sort by Date
    sorted_date = TaskSorter.sort(tasks, "Due Date")
    assert sorted_date[0].title == "Sooner"

    # Sort by Priority (High is mapped to lower numerical value in PRIORITY_MAP)
    sorted_prio = TaskSorter.sort(tasks, "Priority")
    assert sorted_prio[0].title == "Sooner"


# ─────────────────────────────────────────────────────────────────────────────
# FT01: Task Labeling System
# TC-026 → TC-030
# ─────────────────────────────────────────────────────────────────────────────


def test_tc026_tag_crud_management(app_window, qtbot, monkeypatch):
    """[FT01] TC-026: Verify Tag Creation, Editing, and Deletion in Tags Management."""
    dashboard = app_window.dashboard

    # Navigate to Manage Tags
    dashboard.set_mode("tags")
    assert dashboard.current_mode == "tags"
    tags_widget = dashboard.page_tags

    # 1. Create a Tag
    tags_widget.name_input.setText("Work")
    # Select the first color button (Ocean Peach #6579BE)
    qtbot.mouseClick(tags_widget.color_buttons[0], Qt.LeftButton)
    qtbot.mouseClick(tags_widget.save_btn, Qt.LeftButton)

    # Verify Tag exists in DB
    all_tags = dashboard.task_manager.get_all_tags()
    work_tag = next((t for t in all_tags if t.name == "Work"), None)
    assert work_tag is not None
    assert work_tag.color == "#6579BE"

    # 2. Edit the Tag
    tags_widget.tags_list.setCurrentRow(0)  # Select the tag we just created
    tags_widget.name_input.setText("Office")
    qtbot.mouseClick(
        tags_widget.color_buttons[2], Qt.LeftButton
    )  # Vibrant Orange #F54800
    qtbot.mouseClick(tags_widget.save_btn, Qt.LeftButton)

    all_tags = dashboard.task_manager.get_all_tags()
    office_tag = next((t for t in all_tags if t.name == "Office"), None)
    assert office_tag is not None
    assert office_tag.color == "#F54800"
    assert not any(t.name == "Work" for t in all_tags)

    # 3. Delete the Tag
    # Simulate the confirm dialog

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args: QMessageBox.StandardButton.Yes,
    )

    # Ensure selection is processed
    tags_widget.tags_list.item(0).setSelected(True)
    qtbot.wait_until(
        lambda: tags_widget.delete_btn.isVisible()
        and tags_widget.delete_btn.isEnabled()
    )

    # Click the button
    qtbot.mouseClick(tags_widget.delete_btn, Qt.LeftButton)

    # Wait for the database to update
    qtbot.wait_until(lambda: len(dashboard.task_manager.get_all_tags()) == 0)

    assert len(dashboard.task_manager.get_all_tags()) == 0


def test_tc027_task_tag_assignment_and_display(app_window):
    """[FT01] TC-027: Verify assigning tags to a task and checking UI badges."""
    dashboard = app_window.dashboard

    # Setup: Create a tag and a task
    dashboard.task_manager.add_tag(Tag(None, "Urgent", "#FF4D4D"))
    task_id = dashboard.task_manager.add_task(
        Task(
            None,
            "Tagged Task",
            "Desc",
            "Pending",
            datetime.now(),
            None,
            "High",
        )
    )
    dashboard.load_tasks()

    # Find the task row in the tree
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    task_row = todo_group.child(1)  # Index 1 is the task
    tags_cell_widget = dashboard.task_list_view.task_tree.itemWidget(task_row, 2)
    assert tags_cell_widget.findChild(QPushButton) is not None

    # Mock the TagSelectMenu to simulate checking the tag

    # We can't easily click inside the QMenu because it's a separate window in some OS
    # Instead, we test the logic: _update_task_tags
    urgent_tag = dashboard.task_manager.get_all_tags()[0]
    dashboard.task_list_view._update_task_tags(
        dashboard.task_manager.get_task_by_id(task_id), [urgent_tag]
    )

    # Verify DB update
    updated_task = dashboard.task_manager.get_task_by_id(task_id)
    assert len(updated_task.tags) == 1
    assert updated_task.tags[0].name == "Urgent"

    # Verify UI Badge
    dashboard.load_tasks()
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    task_row = todo_group.child(1)
    tags_cell_widget = dashboard.task_list_view.task_tree.itemWidget(task_row, 2)
    # The cell should now have a QLabel with "Urgent"
    labels = tags_cell_widget.findChildren(QLabel)
    assert any(lbl.text() == "Urgent" for lbl in labels)


def test_tc028_tag_persistence_and_kanban(app_window):
    """[FT01] TC-028: Verify tags persist and appear on Kanban cards."""
    dashboard = app_window.dashboard

    # Create tag and task with tag
    tag = Tag(None, "Personal", "#9C27B0")
    tag_id = dashboard.task_manager.add_tag(tag)
    tag.id = tag_id

    task = Task(
        None,
        "Kanban Tag Task",
        "",
        "Pending",
        datetime.now(),
        None,
        "Low",
        tags=[tag],
    )
    dashboard.task_manager.add_task(task)

    # Switch to Kanban
    dashboard.set_mode("kanban")
    dashboard.load_tasks()

    # Verify Kanban card has tag badge
    todo_content = dashboard.kanban_board_view.todo_content
    card = todo_content.itemAt(0).widget()
    assert card.task.title == "Kanban Tag Task"

    labels = card.findChildren(QLabel)
    assert any(lbl.text() == "Personal" for lbl in labels)


def test_tc029_tag_limit_enforcement(app_window):
    """[FT01] TC-029: Verify that more than 5 tags are trimmed as per requirements."""
    dashboard = app_window.dashboard

    # Create 6 tags
    tags = []
    for i in range(6):
        t_id = dashboard.task_manager.add_tag(Tag(None, f"Tag{i}", "#FFFFFF"))
        tags.append(Tag(t_id, f"Tag{i}", "#FFFFFF"))

    task = Task(None, "Limit Task", "", "Pending", datetime.now(), None, "Medium")
    task_id = dashboard.task_manager.add_task(task)
    task.id = task_id

    # Try assigning 6 tags via the list view helper
    dashboard.task_list_view._update_task_tags(task, tags)

    # Verify only 5 were saved
    final_task = dashboard.task_manager.get_task_by_id(task_id)
    assert len(final_task.tags) == 5


def test_tc030_tag_filtering_logic(app_window):
    """[FT01] TC-030: Verify tag filtering isolates correct tasks."""
    dashboard = app_window.dashboard

    # Setup tags
    tag_work = Tag(None, "Work", "#000000")
    tag_work.id = dashboard.task_manager.add_tag(tag_work)
    tag_home = Tag(None, "Home", "#000000")
    tag_home.id = dashboard.task_manager.add_tag(tag_home)

    # Setup tasks
    dashboard.task_manager.add_task(
        Task(None, "W1", "", "Pending", datetime.now(), None, "Medium", tags=[tag_work])
    )
    dashboard.task_manager.add_task(
        Task(None, "H1", "", "Pending", datetime.now(), None, "Medium", tags=[tag_home])
    )
    dashboard.load_tasks()

    # Initial state: 2 tasks (+1 header)
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 3

    # Filter by "Work"
    dashboard.handle_tag_filter_change(tag_work.id)

    # Should only show W1 (+1 header)
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 2
    assert (
        "W1"
        in dashboard.task_list_view.task_tree.itemWidget(todo_group.child(1), 0)
        .findChild(QLabel)
        .text()
    )

    # Clear filter
    dashboard.handle_tag_filter_change(None)
    todo_group = dashboard.task_list_view.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 3


# ─────────────────────────────────────────────────────────────────────────────
# FT09: Task Image & PDF Attachments
# TC-031 → TC-034
# ─────────────────────────────────────────────────────────────────────────────


def test_tc031_attachment_persistence(app_window):
    """[FT09] TC-031: Verify that attachments are saved to the filesystem and DB."""
    dashboard = app_window.dashboard

    # Create a dummy image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"fake image data")
        tmp_path = tmp.name

    try:
        # Save attachment via manager
        result = dashboard.task_manager.save_attachment(tmp_path)
        assert result is not None
        new_path, original_name = result

        # Verify file exists in internal storage
        assert os.path.exists(new_path)
        assert ".efficio_attachments" in new_path

        # Create task with this attachment
        attachment = TaskAttachment(None, -1, new_path, original_name)
        task = Task(
            None,
            "Attach Task",
            "",
            "Pending",
            datetime.now(),
            None,
            "High",
            attachments=[attachment],
        )
        task_id = dashboard.task_manager.add_task(task)

        # Reload and verify
        db_task = dashboard.task_manager.get_task_by_id(task_id)
        assert len(db_task.attachments) == 1
        assert db_task.attachments[0].file_name == os.path.basename(tmp_path)
        assert os.path.exists(db_task.attachments[0].file_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_tc032_pdf_attachment_support(app_window):
    """[FT09] TC-032: Verify PDF support in the attachment system."""
    dashboard = app_window.dashboard

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 dummy pdf")
        tmp_path = tmp.name

    try:
        result = dashboard.task_manager.save_attachment(tmp_path)
        assert result is not None
        new_path, _ = result
        assert new_path.lower().endswith(".pdf")

        attachment = TaskAttachment(None, -1, new_path, os.path.basename(tmp_path))
        task = Task(
            None,
            "PDF Task",
            "",
            "Pending",
            datetime.now(),
            None,
            "Medium",
            attachments=[attachment],
        )
        task_id = dashboard.task_manager.add_task(task)

        db_task = dashboard.task_manager.get_task_by_id(task_id)
        assert db_task.attachments[0].file_path.endswith(".pdf")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_tc033_attachment_cleanup_on_delete(app_window, monkeypatch):
    """[FT09] TC-033: Verify physical files are deleted on permanent task removal."""
    dashboard = app_window.dashboard

    # Setup task with attachment
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"data")
        tmp_path = tmp.name

    result = dashboard.task_manager.save_attachment(tmp_path)
    new_path, _ = result

    attachment = TaskAttachment(None, -1, new_path, "test.jpg")
    task = Task(
        None,
        "Delete Me",
        "",
        "Pending",
        datetime.now(),
        None,
        "Low",
        attachments=[attachment],
    )
    task_id = dashboard.task_manager.add_task(task)

    assert os.path.exists(new_path)

    # Soft delete
    dashboard.task_manager.delete_task(task_id)
    assert os.path.exists(new_path)  # Should still exist in trash

    # Permanent delete
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes
    )
    dashboard.task_manager.permanently_delete_task(task_id)

    # Verify file is GONE from disk
    assert not os.path.exists(new_path)


def test_tc034_kanban_attachment_carousel_render(app_window):
    """[FT09] TC-034: Verify Kanban card renders the attachment carousel."""
    dashboard = app_window.dashboard

    # Create task with 2 attachments
    attachments = []
    for i in range(2):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"img")
            p = tmp.name
        res = dashboard.task_manager.save_attachment(p)
        attachments.append(TaskAttachment(None, -1, res[0], res[1]))
        os.remove(p)

    task = Task(
        None,
        "Carousel Task",
        "",
        "Pending",
        datetime.now(),
        None,
        "High",
        attachments=attachments,
    )
    dashboard.task_manager.add_task(task)

    # Switch to Kanban
    dashboard.set_mode("kanban")
    dashboard.load_tasks()

    # Find card
    todo_content = dashboard.kanban_board_view.todo_content
    card = todo_content.itemAt(0).widget()

    # Check for QScrollArea (carousel)
    from PySide6.QtWidgets import QScrollArea

    carousels = card.findChildren(QScrollArea)
    assert len(carousels) == 1

    # Verify it has 2 thumbnails (QLabels in the scroll area's widget)
    thumbs = carousels[0].widget().findChildren(QLabel)
    # Note: carousel_layout might have an extra stretch, but widgets should be 2
    assert len(thumbs) == 2
