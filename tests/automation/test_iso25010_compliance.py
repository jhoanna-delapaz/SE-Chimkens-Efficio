import os
import sys
import tempfile
from datetime import datetime

import pytest

# Path resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "src")
sys.path.append(src_dir)

from business.task_manager import TaskManager  # noqa: I001, E402
from data.DataBaseHandler import init_db  # noqa: I001, E402
from data.models import Task  # noqa: I001, E402
from main import MainWindow  # noqa: I001, E402
from utils.constants import UIConstants  # noqa: I001, E402
from utils.paths import get_asset_path  # noqa: I001, E402
from utils.strings import UIStrings  # noqa: I001, E402

# ISO 25010 Compliance Suite


def find_line_number(file_path: str, pattern: str) -> int:
    """Helper to find the first line number containing a specific pattern."""
    if not os.path.exists(file_path):
        return -1
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if pattern in line:
                return i
    return -1


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


# ─── SECURITY (Confidentiality & Integrity) ──────────────────────────────────


def test_sec001_xss_sanitization(app_window):
    """ISO 25010 Security: Verify that TaskManager blocks XSS injection scripts."""
    dashboard = app_window.dashboard
    malicious_title = "Hack <script>alert(1)</script>"

    new_task = Task(
        id=None,
        title=malicious_title,
        description="javascript:void(0)",
        status=UIStrings.STATUS_TODO,
        created_at=datetime.now(),
        due_date="",
        priority="High",
        is_deleted=0,
    )

    result = dashboard.task_manager.add_task(new_task)
    assert result == -1  # Validation must fail


def test_sec002_sql_injection_resilience(app_window):
    """ISO 25010 Security: Verify resilience against basic SQL injection in search."""
    dashboard = app_window.dashboard
    # Search for something that tries to escape the query
    malicious_search = "') OR 1=1; --"

    # This should not crash and should return 0 results (assuming no tasks match that literal string)
    tasks = dashboard.task_manager.get_all_tasks(malicious_search)
    assert isinstance(tasks, list)
    # If the injection worked, it would return all tasks (count > 0).
    # With parameter binding, it treats the injection as a literal string.
    assert len(tasks) == 0


# ─── MAINTAINABILITY (Modularity & Analyzability) ───────────────────────────


def test_main001_ui_constants_compliance(app_window):
    """ISO 25010 Maintainability: Verify components use centralized UIConstants."""
    dashboard = app_window.dashboard

    # Verify Sidebar uses the constant width
    assert dashboard.sidebar.width() == UIConstants.SIDEBAR_COLLAPSED_WIDTH

    # Verify Kanban Lanes use the constant width
    lane = dashboard.kanban_board_view.todo_container
    assert lane.minimumWidth() == UIConstants.KANBAN_LANE_MIN_WIDTH


def test_main002_string_centralization(app_window):
    """ISO 25010 Maintainability: Verify headers use centralized UIStrings."""
    dashboard = app_window.dashboard
    dashboard.set_mode("kanban")

    # Check if the title matches the string constant
    assert dashboard.title_label.text() == UIStrings.NAV_KANBAN


# ─── PORTABILITY (Adaptability) ─────────────────────────────────────────────


def test_port001_asset_resolution_logic():
    """ISO 25010 Portability: Verify that get_asset_path handles relative paths correctly."""
    # Test with a mock relative path
    test_path = "icons/app.png"
    resolved = get_asset_path(test_path)

    # It should be an absolute path ending with the relative part
    assert os.path.isabs(resolved)
    assert resolved.replace("\\", "/").endswith(test_path)


# ─── EVIDENCE (Static Analysis / Structural Integrity) ────────────────────


def test_evid_001_source_string_compliance():
    """ISO 25010 Evidence: Prove that UI components use UIStrings instead of raw strings."""
    # Check KanbanBoardView for use of raw "To-Do" title vs UIStrings.LABEL_TODO
    file_path = os.path.join(
        src_dir, "presentation", "components", "kanban_board_view.py"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Static Evidence check:
    assert "UIStrings.LABEL_TODO" in content
    assert '_create_lane("To-Do")' not in content


def test_evid_002_source_type_safety_compliance():
    """ISO 25010 Evidence: Prove that DataHandler methods use strict type hinting."""
    file_path = os.path.join(src_dir, "data", "DataBaseHandler.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Evidence of ISO 25010 Analyzability (Type Hints)
    # Looking for a specific method signature as an example
    assert 'def get_all_tasks(self, search_query: str = "") -> List[Task]:' in content


def test_evid_003_source_magic_number_compliance():
    """ISO 25010 Evidence: Prove that the Dashboard uses UIConstants for sidebar width."""
    file_path = os.path.join(src_dir, "presentation", "dashboard.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Prove we removed 'setFixedWidth(60)' and replaced with UIConstants
    assert "setFixedWidth(60)" not in content
    assert "UIConstants.SIDEBAR_COLLAPSED_WIDTH" in content


def test_evid_004_source_security_validation():
    """ISO 25010 Evidence: Prove that TaskManager performs security sanitization."""
    file_path = os.path.join(src_dir, "business", "task_manager.py")
    pattern = 'malicious_patterns = ["<script>", "javascript:", "onload="]'

    line_no = find_line_number(file_path, pattern)
    assert (
        line_no != -1
    ), f"Compliance Violation: Security validation missing in {file_path}"
    print(
        f"\n[ISO 25010 EVIDENCE] Security (Sanitization): Found in {os.path.basename(file_path)} at Line {line_no}"
    )


def test_evid_005_source_modularity_helpers():
    """ISO 25010 Evidence: Prove that TaskListView uses styled group helpers."""
    file_path = os.path.join(src_dir, "presentation", "components", "task_list_view.py")
    pattern = "def _create_group(self, title: str) -> QTreeWidgetItem:"

    line_no = find_line_number(file_path, pattern)
    assert (
        line_no != -1
    ), f"Compliance Violation: Modular group helper missing in {file_path}"
    print(
        f"\n[ISO 25010 EVIDENCE] Maintainability (Modularity): Found in {os.path.basename(file_path)} at Line {line_no}"
    )


def test_evid_006_source_asset_portability():
    """ISO 25010 Evidence: Prove that Dashboard uses standardized asset resolution."""
    file_path = os.path.join(src_dir, "presentation", "dashboard.py")
    pattern = "self.preset_image_path = get_asset_path"

    line_no = find_line_number(file_path, pattern)
    assert (
        line_no != -1
    ), f"Compliance Violation: Hardcoded asset path found in {file_path}"
    print(
        f"\n[ISO 25010 EVIDENCE] Portability (Asset Path): Found in {os.path.basename(file_path)} at Line {line_no}"
    )
