import os
import sys
import tempfile
import pytest
from PySide6.QtCore import Qt, QTimer
# We must import QApplication to prevent pytest-qt from complaining or crashing if it's not set up
from PySide6.QtWidgets import QApplication

# Add src directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "src")
sys.path.append(src_dir)

from main import MainWindow
from data.DataBaseHandler import init_db

@pytest.fixture
def app_window(qtbot):
    """Fixture to set up the main window and a clean test database."""
    # Use a unique temp DB path per test to avoid cross-test pollution (locked files, leftover data)
    fd, TEST_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="test_efficio_")
    os.close(fd)
    init_db(TEST_DB_PATH)

    # Initialize main window
    window = MainWindow(TEST_DB_PATH)

    # Replace with TaskManager using test DB (close old connection to avoid ResourceWarning)
    from business.task_manager import TaskManager
    try:
        window.dashboard.task_manager.close()
    except Exception:
        pass
    window.dashboard.task_manager = TaskManager(TEST_DB_PATH)

    window.dashboard.load_tasks() # Reload with test DB

    window.show()
    qtbot.addWidget(window)
    yield window

    # Teardown: close DB connection before removing file (avoids lock on Windows)
    try:
        window.dashboard.task_manager.close()
    except Exception:
        pass
    window.close()
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except (PermissionError, OSError):
        pass

def test_feature2_view_dashboard(app_window, qtbot):
    """TC-003: Verify tasks display on dashboard"""
    dashboard = app_window.dashboard
    assert dashboard.task_list is not None
    assert dashboard.add_btn.text() == "+ New Task"
    # By default, the clean database should have 0 tasks shown
    assert dashboard.task_list.count() == 0

def test_feature1_add_task_success(app_window, qtbot, monkeypatch):
    """TC-001: Verify successful task creation & Handle ISO 25010 Success Popup"""
    dashboard = app_window.dashboard
    initial_count = dashboard.task_list.count()

    # Force the test to instantly click "OK" on the new Success QMessageBox!
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)

    def interact_with_dialog():
        # Find the active dialog
        from PySide6.QtWidgets import QApplication
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            top_widget.title_input.setText("Submit Project")
            top_widget.desc_input.setPlainText("Sprint 1 Output")
            top_widget.accept()

    # Trigger the interaction right after the event loop starts the dialog
    from PySide6.QtCore import QTimer
    QTimer.singleShot(100, interact_with_dialog)

    # Click Add Task (this will block until the QTimer accepts the dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    # Verify the task count increased exactly once
    assert dashboard.task_list.count() == initial_count + 1

    # Verify it displays correctly
    item = dashboard.task_list.item(0)
    assert "Submit Project" in item.text()
    assert item.checkState() == Qt.CheckState.Unchecked

def test_feature1_add_task_empty_title_validation(app_window, qtbot, monkeypatch):
    """TC-002: Verify validation message for empty title"""
    dashboard = app_window.dashboard
    initial_count = dashboard.task_list.count()

    # Mock the critical QMessageBox to click 'OK' automatically so it doesn't block forever
    message_box_called = False

    from PySide6.QtWidgets import QMessageBox
    def mock_warning(*args, **kwargs):
        nonlocal message_box_called
        message_box_called = True
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", mock_warning)

    def interact_with_dialog():
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            # Leave title blank purposely
            top_widget.title_input.setText("")
            # Trigger validate_and_accept which should fail and call QMessageBox
            top_widget.validate_and_accept()
            # Then we force close it so the test can proceed
            top_widget.reject()

    QTimer.singleShot(100, interact_with_dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)

    # Verify no task was added
    assert dashboard.task_list.count() == initial_count
    assert message_box_called is True

def test_feature3_mark_task_completed(app_window, qtbot):
    """TC-004: Verify marking a task as completed"""
    dashboard = app_window.dashboard

    # Add a dummy task directly to DB to test
    from data.models import Task
    from datetime import datetime
    new_task = Task(id=None, title="Test Checkbox", description="", status="Pending", 
                    created_at=datetime.now(), due_date="", priority="High")
    dashboard.task_manager.add_task(new_task)
    dashboard.load_tasks()

    item = dashboard.task_list.item(0)
    assert item.checkState() == Qt.CheckState.Unchecked

    # Simulate user checking the box
    item.setCheckState(Qt.CheckState.Checked)

    # Fetch from DB to ensure it was saved
    task_id = item.data(Qt.ItemDataRole.UserRole)
    db_task = dashboard.task_manager.get_task_by_id(task_id)
    assert db_task.status == "Completed"

def test_feature4_delete_task(app_window, qtbot, monkeypatch):
    """TC-006: Verify successful task soft deletion (Sprint 2)"""
    dashboard = app_window.dashboard

    # Add a dummy task directly
    from data.models import Task
    from datetime import datetime
    new_task = Task(id=None, title="Task To Delete", description="", status="Pending", 
                    created_at=datetime.now(), due_date="", priority="Medium", is_deleted=0)
    dashboard.task_manager.add_task(new_task)
    dashboard.load_tasks()

    assert dashboard.task_list.count() == 1
    item = dashboard.task_list.item(0)
    task_id = item.data(Qt.ItemDataRole.UserRole)

    # Mock confirmation dialog to automatically say Yes
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)

    # Call the delete method directly (moves to trash)
    dashboard.delete_current_task(item)

    # Verify UI is updated (disappears from active dashboard)
    assert dashboard.task_list.count() == 0

    # Verify DB is updated to Soft Delete (is_deleted = 1) instead of completely wiped
    db_task = dashboard.task_manager.get_task_by_id(task_id)
    assert db_task is not None
    assert db_task.is_deleted == 1

def test_feature5_trash_management(app_window, qtbot, monkeypatch):
    """[EP01-FT05] Trash Management with Restore and Permanent Delete Functionality"""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMessageBox
    from datetime import datetime
    from data.models import Task

    dashboard = app_window.dashboard
    main_window = app_window

    # 1. Setup: Create a task via the manager so we have a clean state
    new_task = Task(id=None, title="Trash Test Task", description="Testing delete/restore", 
                    status="Pending", created_at=datetime.now(), due_date="2026-03-20", 
                    priority="High", is_deleted=0)
    task_id = dashboard.task_manager.add_task(new_task)
    dashboard.load_tasks()

    # 2. Move to Trash (Soft Delete)
    # Mocking the confirmation dialog for deletion
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)

    initial_count = dashboard.task_list.count()
    dashboard.delete_current_task(dashboard.task_list.item(0))

    assert dashboard.task_list.count() == initial_count - 1 

    # 3. Navigate to Trash Bin View
    qtbot.mouseClick(main_window.btn_trash, Qt.MouseButton.LeftButton)
    assert dashboard.current_mode == "trash"
    # Ensure our specific task is the one in the trash
    item = dashboard.task_list.item(0)
    assert "Trash Test Task" in item.text()

    # 4. Restore the Task
    # Instead of calling task_manager.restore directly, trigger the UI action if possible
    dashboard.task_manager.restore_task(task_id)
    dashboard.load_tasks()
    assert dashboard.task_list.count() == 0 # Gone from trash view

    # Verify it's back on the Dashboard
    qtbot.mouseClick(main_window.btn_dash, Qt.MouseButton.LeftButton)
    assert dashboard.task_list.count() == initial_count
    assert "Trash Test Task" in dashboard.task_list.item(0).text()

    # 5. Permanent Delete
    dashboard.delete_current_task(dashboard.task_list.item(0)) # Back to trash
    qtbot.mouseClick(main_window.btn_trash, Qt.MouseButton.LeftButton)

    # Mock the permanent delete warning
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.StandardButton.Yes)

    dashboard.task_manager.permanently_delete_task(task_id)
    dashboard.load_tasks()

    # Final Database/UI Verifications
    assert dashboard.task_list.count() == 0
    db_task = dashboard.task_manager.get_task_by_id(task_id)
    assert db_task is None
