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


def test_feature1_add_task_success(app_window, qtbot):
    """TC-001: Verify successful task creation"""
    dashboard = app_window.dashboard
    initial_count = dashboard.task_list.count()
    
    # In PySide, modal dialogs block the test execution if we just click the button.
    # To test the isolated logic of AddTaskDialog, we'll instantiate it directly,
    # fill it out, and call accept(), then manually trigger the save flow.
    # OR we use a QTimer to interact with it right after it opens.
    
    def interact_with_dialog():
        # Find the active dialog
        top_widget = QApplication.activeModalWidget()
        if top_widget:
            top_widget.title_input.setText("Submit Project")
            top_widget.desc_input.setPlainText("Sprint 1 Output")
            top_widget.accept()
            
    # Trigger the interaction right after the event loop starts the dialog
    QTimer.singleShot(100, interact_with_dialog)
    
    # Click Add Task (this will block until the QTimer accepts the dialog)
    qtbot.mouseClick(dashboard.add_btn, Qt.LeftButton)
    
    # Verify the task count increased
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
    """TC-006: Verify successful task deletion"""
    dashboard = app_window.dashboard
    
    # Add a dummy task directly
    from data.models import Task
    from datetime import datetime
    new_task = Task(id=None, title="Task To Delete", description="", status="Pending", 
                    created_at=datetime.now(), due_date="", priority="Medium")
    dashboard.task_manager.add_task(new_task)
    dashboard.load_tasks()
    
    assert dashboard.task_list.count() == 1
    item = dashboard.task_list.item(0)
    task_id = item.data(Qt.ItemDataRole.UserRole)
    
    # Mock confirmation dialog to automatically say Yes
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    
    # Call the delete method directly
    dashboard.delete_current_task(item)
    
    # Verify UI is updated
    assert dashboard.task_list.count() == 0
    
    # Verify DB is updated
    db_task = dashboard.task_manager.get_task_by_id(task_id)
    assert db_task is None

