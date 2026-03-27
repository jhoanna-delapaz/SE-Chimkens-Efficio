import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow
)
from config import get_default_db_path
from data.DataBaseHandler import init_db
from presentation.dashboard import DashboardInterface

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


class MainWindow(QMainWindow):
    def __init__(self, db_file=None):
        super().__init__()

        if db_file is None:
            db_file = get_default_db_path()

        self.db_file = db_file
        self.setWindowTitle("EFFICIO - PySide6")
        self.resize(1200, 850)

        self.dashboard = DashboardInterface(self, self.db_file)
        self.setCentralWidget(self.dashboard)


if __name__ == "__main__":
    # Initialize DB
    db_file = get_default_db_path()
    init_db(db_file)

    # Run App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
