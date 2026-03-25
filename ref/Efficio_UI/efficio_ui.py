import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QLabel,
    QCalendarWidget, QPushButton, QGraphicsBlurEffect,
    QLineEdit
)
from PyQt6.QtGui import QPixmap, QAction, QIcon
from PyQt6.QtCore import Qt


class Dashboard(QWidget):
    def __init__(self, image_path="images/pastel-bg.jpg"):
        super().__init__()
        self.setWindowTitle("Task Dashboard")

        # --- resizable window with a minimum starting point ---
        self.setMinimumSize(900, 600)
        self.image_path = image_path

        # --- Code for the menu, it starts out minimized ---
        self.sidebar_expanded = False

        # ---------------- Background Image ----------------
        self.bg_label = QLabel(self)
        self.update_background()  # Initial background set
        self.bg_label.setStyleSheet("border: none;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(30)
        self.bg_label.setGraphicsEffect(blur)

        # ---------------- Main Layout ----------------
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # ---------------- Sidebar ----------------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(60)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.4);
                border-radius: 20px;
            }
        """)

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(15)

        # Toggle Button Container (Pinned to the LEFT)
        toggle_container = QHBoxLayout()
        self.toggle_btn = QPushButton("≡")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        toggle_container.addWidget(self.toggle_btn)
        toggle_container.addStretch()
        self.sidebar_layout.addLayout(toggle_container)

        # Sidebar Buttons (Placeholders)
        self.sidebar_options = []
        for i in range(1, 4):
            btn = QPushButton("")
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: white;
                    border-radius: 10px;
                    font-size: 14px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                }
            """)
            self.sidebar_layout.addWidget(btn)
            self.sidebar_options.append(btn)

        self.sidebar_layout.addStretch()

        # ---------------- Task Section ----------------
        task_section_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        title = QLabel("My Tasks")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # ---------------- Sort Button ----------------
        sort_btn = QPushButton("↑↓")
        sort_btn.setFixedSize(40, 40)
        sort_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,0);
                border-radius: 20px;
                font-size: 30px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
               background-color: rgba(255,255,255,0.1);
            }
        """)
        header_layout.addWidget(sort_btn)

        # ---------------- Add Button ----------------
        add_btn = QPushButton("+")
        add_btn.setFixedSize(40, 40)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,0);
                border-radius: 20px;
                font-size: 35px;
                font-weight: bold;
                color: white;
                padding-top: -8px;
                padding-left: 2px;
            }
            QPushButton:hover {
               background-color: rgba(255,255,255,0.1);
            }
        """)

        header_layout.addWidget(add_btn)
        task_section_layout.addLayout(header_layout)
        task_section_layout.addSpacing(1)

        # ---------------- Task Card ----------------
        task_card = QFrame()
        task_card.setStyleSheet("""
            QFrame {
                background-color: rgba(0,0,0,0.5);
                border-radius: 20px;
                padding: 20px;
                border: 1px solid rgba(255,255,255,0.1);
            }
        """)
        task_layout = QVBoxLayout(task_card)
        task_layout.setSpacing(10)

        # Search Bar Row
        search_row = QHBoxLayout()
        search_row.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks...")
        self.search_bar.setFixedWidth(200)

        # Search Icon
        search_icon = QIcon("images/search_icon.png")
        self.search_bar.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)

        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 5px 8px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 0.4);
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        search_row.addWidget(self.search_bar)
        task_layout.addLayout(search_row)

        # --- CHANGED: Removed fixed height from empty_area to let it expand ---
        empty_area = QFrame()
        empty_area.setStyleSheet("""
            QFrame {
                background-color: rgba(0,0,0,0.35);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.15);
            }
        """)
        task_layout.addWidget(empty_area)
        task_layout.addStretch()

        task_section_layout.addWidget(task_card)

        # ---------------- Right Panel ----------------
        right_panel_layout = QVBoxLayout()

        # ---------------- Calendar Card ----------------
        calendar_card = QFrame()
        calendar_card.setStyleSheet("""
            QFrame {
                background-color: rgba(0,0,0,0.5);
                border-radius: 20px;
                padding: 15px;
            }
        """)

        cal_layout = QVBoxLayout(calendar_card)
        cal_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.setSpacing(0)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        # --- CHANGED: Set a reasonable minimum height but not a fixed one ---
        calendar.setMinimumHeight(280)

        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: rgba(0,0,0,0);
                color: white;
                border: none;
            }
            QCalendarWidget QToolButton {
                background-color: rgba(0,0,0,0);
                color: white;
                border: none;
                qproperty-iconSize: 24px 24px;
                padding-left: 10px;
                padding-right: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: url(images/down-arrow.png);
                subcontrol-position: right center;
                subcontrol-origin: padding;
            }
            QCalendarWidget QSpinBox {
                max-width: 1px;
                min-width: 1px;
                background-color: rgba(0,0,0,0);
                border: none;
            }
            QCalendarWidget QAbstractItemView {
                background-color: rgba(0,0,0,0);
                color: white;
                selection-background-color: #ff4ecb;
                selection-color: white;
            }
            QCalendarWidget QHeaderView::section {
                background-color: rgba(0,0,0,0);
                color: white;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: rgba(0,0,0,0);
                spacing: 10px;
            }
        """)

        cal_layout.addWidget(calendar)

        # ---------------- Performance/Analytics Card ----------------
        performance_card = QFrame()
        performance_card.setStyleSheet("""
            QFrame {
                background-color: rgba(0,0,0,0.5);
                border-radius: 20px;
                padding: 15px;
            }
        """)
        perf_layout = QVBoxLayout(performance_card)
        perf_layout.addStretch()

        right_panel_layout.addWidget(calendar_card)
        right_panel_layout.addWidget(performance_card)

        # ---------------- Add to Main Layout ----------------
        self.main_layout.addWidget(self.sidebar)
        # --- CHANGED: Task section takes 60% of width, Right panel takes 40% ---
        self.main_layout.addLayout(task_section_layout, 3)
        self.main_layout.addLayout(right_panel_layout, 2)

        self.setLayout(self.main_layout)

    # --- NEW: Updates background size and image whenever window resizes ---
    def resizeEvent(self, event):
        self.update_background()
        super().resizeEvent(event)

    def update_background(self):
        pixmap = QPixmap(self.image_path).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

    # ---------------- Toggle Sidebar ----------------
    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(60)
            for btn in self.sidebar_options:
                btn.setText("")
        else:
            self.sidebar.setFixedWidth(150)
            for i, btn in enumerate(self.sidebar_options):
                btn.setText(f"Option {i + 1}")

        self.sidebar_expanded = not self.sidebar_expanded


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard("images/pastel-bg.jpg")
    window.show()
    sys.exit(app.exec())