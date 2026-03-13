"""
Central configuration for the application.
Single source of truth for paths and settings.
"""
import os
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
def get_default_db_path() -> str:
    """Return the default SQLite database path. Overridable for tests."""
    return os.path.join(_SRC_DIR, "data", "efficio.db")