
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from data.DataBaseHandler import init_db
from presentation.dashboard import DashboardInterface

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        
        btn_dash = QPushButton("Dashboard")

        btn_dash.setStyleSheet("""
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
        """)
        
        nav_layout.addWidget(btn_dash)
        nav_layout.addStretch()
        
        main_layout.addWidget(self.nav_bar)

        # Content Area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        
        # Initialize Dashboard
        self.dashboard = DashboardInterface(self)
        content_layout.addWidget(self.dashboard)
        
        main_layout.addWidget(self.content_area)

if __name__ == "__main__":
    # Initialize DB
    db_file = os.path.join(current_dir, "data", "efficio.db")
    init_db(db_file)

    # Run App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
