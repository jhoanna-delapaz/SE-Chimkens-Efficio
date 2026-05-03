import os
import sys


def get_asset_path(relative_path: str) -> str:
    """
    Resolves the absolute path to a resource asset, ensuring compatibility
    between development environments and bundled executables (PyInstaller).
    ISO 25010: Improves Portability and Installability.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not bundled, use the standard project root resolution
        # This assumes the project structure: src/utils/paths.py
        # We go up two levels to reach the project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
