import os
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from config import get_default_db_path
from data.DataBaseHandler import init_db
from presentation.dashboard import DashboardInterface

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        background: rgba(255, 255, 255, 0.03);
        width: 8px;
        border-radius: 4px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 0.35);
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;  /* removes the arrow buttons */
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
    }
    QScrollBar:horizontal {
        background: rgba(255, 255, 255, 0.03);
        height: 8px;
        border-radius: 4px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(255, 255, 255, 0.35);
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
    }
"""


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
    app.setStyleSheet(SCROLLBAR_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
