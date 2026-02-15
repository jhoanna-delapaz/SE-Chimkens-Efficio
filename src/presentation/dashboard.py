from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import SubtitleLabel

class DashboardInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")
        
        layout = QVBoxLayout(self)
        
        # Add a placeholder title
        title = SubtitleLabel("Dashboard Overview", self)
        layout.addWidget(title)
        
        # Add a stretch to push content to the top
        layout.addStretch(1)