import os
import sys
import tempfile
from datetime import datetime

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

# Path resolution MUST execute before src imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "src")
sys.path.append(src_dir)

# Tell Ruff to ignore sorting (I001) and ignore import position (E402) for these 3 files!
from data.DataBaseHandler import init_db  # noqa: I001, E402
from data.models import Task  # noqa: I001, E402
from main import MainWindow  # noqa: I001, E402


@pytest.fixture
def app_window(qtbot):
    """Fixture to set up the main window and a clean test database."""
    fd, TEST_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="test_efficio_")
    os.close(fd)
    init_db(TEST_DB_PATH)

    window = MainWindow(TEST_DB_PATH)
    from business.task_manager import TaskManager

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
    todo_group = dashboard.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 2  # 1 header row + 1 physical task row

    task_row = todo_group.child(1)
    assert "Submit Project" in task_row.text(0)


def test_tc002_add_task_empty_title_validation(app_window, qtbot):
    """TC-002: Verify validation message for empty title blocks creation"""
    dashboard = app_window.dashboard
    todo_group = dashboard.task_tree.topLevelItem(0)
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
    assert dashboard.task_tree is not None

    # Mathematical validation: Top level items are the 3 groups + 2 spacers = 5
    assert dashboard.task_tree.topLevelItemCount() == 5

    # Extract "To-Do" accordion. It should ONLY have 1 child (the Inline Header row).
    todo_group = dashboard.task_tree.topLevelItem(0)
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
    assert dashboard.todo_layout.count() == 1
    assert dashboard.done_layout.count() == 1
    assert dashboard.inprogress_layout.count() == 0


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
    todo_group = dashboard.task_tree.topLevelItem(0)
    assert todo_group.childCount() == 1  # Just the header left

    # Navigate to Trash Bin View
    dashboard.set_mode("trash")
    assert dashboard.current_mode == "trash"

    # Verify it exists in the Trash UI
    trash_todo_group = dashboard.task_tree.topLevelItem(0)
    assert trash_todo_group.childCount() == 2
    assert "Trash Test Task" in trash_todo_group.child(1).text(0)

    # Permanent Delete Workflow
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes
    )
    dashboard.task_manager.permanently_delete_task(task_id)
    dashboard.load_tasks()

    # Permanent Delete Workflow
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes
    )
    dashboard.task_manager.permanently_delete_task(task_id)
    dashboard.load_tasks()  # <--- THIS VAPORIZES THE OLD POINTER!

    # Final Verification: Nulled from existence
    # We MUST re-fetch the pointer here!
    trash_todo_group_cleared = dashboard.task_tree.topLevelItem(0)
    assert trash_todo_group_cleared.childCount() == 1

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
    todo_group_filtered = dashboard.task_tree.topLevelItem(0)
    assert todo_group_filtered.childCount() == 2

    # Clear Filter
    dashboard.search_bar.setText("")

    # Re-fetch again
    todo_group_cleared = dashboard.task_tree.topLevelItem(0)
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
    todo_group = dashboard.task_tree.topLevelItem(0)
    task_row = todo_group.child(1)

    # Extract the custom Pastel Brush generated by our ACTIVE_THEME_MAP logic
    bg_brush = task_row.background(0)
    bg_color = bg_brush.color()

    # Base Color is #19485F. Verify it correctly extracted the RGB properties!
    assert bg_color.name().upper() == "#19485F"
    assert (
        bg_color.alpha() == 50
    )  # Verifying the aesthetic alpha glassmorphism trick we injected!

    fg_brush = task_row.foreground(0)
    fg_color = fg_brush.color()
    assert (
        fg_color.name().upper() == "#D9E0A4"
    )  # The mapped bright foreground dictionary color!


def test_tc010_past_due_date_validation(app_window, qtbot):
    """TC-010: Task Due Date Validation (Past Date)"""
    from PySide6.QtCore import QDate, QTimer
    from PySide6.QtWidgets import QApplication

    dashboard = app_window.dashboard
    todo_group = dashboard.task_tree.topLevelItem(0)
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
                and top_widget.toast.text() == "Due Date cannot be in the past!"
            ):
                toast_activated = True

            top_widget.reject()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    assert todo_group.childCount() == initial_count
    assert toast_activated is True


def test_tc011_task_priority_selection(app_window, qtbot, monkeypatch):
    """TC-011: Task Priority Management correctly saves"""
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox

    # Auto-click OK on Success UI
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    dashboard = app_window.dashboard
    todo_group = dashboard.task_tree.topLevelItem(0)

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
    todo_group = dashboard.task_tree.topLevelItem(
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
    from PySide6.QtCore import QEasingCurve, Qt, QTimer
    from PySide6.QtWidgets import QApplication

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
