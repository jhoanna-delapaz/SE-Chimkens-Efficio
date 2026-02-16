import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

# 1. Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from data.DataBaseHandler import init_db

# Simple placeholder dashboard for now
class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dashboard - Waiting for Implementation"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EFFICIO")
        self.resize(900, 700)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add Dashboard
        self.dashboard = DashboardInterface()
        self.layout.addWidget(self.dashboard)

if __name__ == "__main__":
    # 1. Initialize DB
    db_file = os.path.join(current_dir, "data", "efficio.db")
    init_db(db_file)

    # 2. Run App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())