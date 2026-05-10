import os
import platform
from pathlib import Path


def get_default_db_path():
    """
    ISO 25010 Security (Confidentiality) Update:
    Instead of storing the database in the open `src/data` folder where anyone
    with access to the project can read it, we now store it in the OS's secure
    user-specific AppData / Home directory.

    This leverages native OS file permissions (sandboxing), ensuring that
    only the currently logged-in user can access the database file.
    """
    # 1. Determine the secure user-specific data directory based on the OS
    if platform.system() == "Windows":
        # Usually C:\Users\Username\AppData\Roaming
        base_dir = Path(os.environ.get("APPDATA", Path.home()))
    elif platform.system() == "Darwin":
        # macOS: ~/Library/Application Support
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        # Linux/Unix: ~/.local/share
        base_dir = Path.home() / ".local" / "share"

    # 2. Append our specific application folder
    app_dir = base_dir / "Efficio" / "data"

    # 3. Create the directory securely if it doesn't exist
    app_dir.mkdir(parents=True, exist_ok=True)

    # 4. Return the absolute path to the secure database
    return str(app_dir / "efficio.db")
