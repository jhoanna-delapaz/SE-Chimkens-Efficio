"""
Central configuration for the application.
Single source of truth for paths and settings.
"""

import os


def get_default_db_path():
    # This automatically finds the absolute path of the 'src' folder where config.py lives
    src_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the data folder
    data_dir = os.path.join(src_dir, "data")

    # Ensure the folder exists before SQLite tries to read/write!
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return os.path.join(data_dir, "efficio.db")
