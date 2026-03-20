import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout,
    QWidget, QHBoxLayout, QPushButton
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
        self.resize(1000, 700)

        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Simple Sidebar Navigation
        self.nav_bar = QWidget()
        self.nav_bar.setFixedWidth(200)
        self.nav_bar.setStyleSheet("""
                                    background-color: #2d2d2d;
                                    color: white;
                                    border-right: 1px solid #444;
                                """)

        nav_layout = QVBoxLayout(self.nav_bar)

        self.btn_dash = QPushButton("Dashboard")
        self.btn_trash = QPushButton("Trash Bin")

        nav_style = """
                        QPushButton {
                            text-align: left;
                            padding: 10px;
                            border: none;
                            background-color: transparent;
                            color: white;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #3d3d3d;
                        }
                    """
        self.btn_dash.setStyleSheet(nav_style)
        self.btn_trash.setStyleSheet(nav_style)

        nav_layout.addWidget(self.btn_dash)
        nav_layout.addWidget(self.btn_trash)
        nav_layout.addStretch()

        main_layout.addWidget(self.nav_bar)

        # Content Area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)

        # Initialize Dashboard
        self.dashboard = DashboardInterface(self, self.db_file)
        content_layout.addWidget(self.dashboard)

        # Connect Navigation Buttons to Dashboard Modes
        self.btn_dash.clicked.connect(lambda: self.dashboard.set_mode("active"))
        self.btn_trash.clicked.connect(lambda: self.dashboard.set_mode("trash"))

        main_layout.addWidget(self.content_area)


if __name__ == "__main__":
    # Initialize DB
    db_file = get_default_db_path()
    init_db(db_file)

    # Run App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
