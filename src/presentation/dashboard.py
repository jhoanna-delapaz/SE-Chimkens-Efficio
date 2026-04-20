import os
from datetime import datetime

from PySide6.QtCore import (
    QDate,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from business.task_manager import TaskManager
from data.models import Task
from presentation.analytics_widget import AnalyticsWidget
from presentation.task_editor_dialog import TaskEditorDialog

try:
    from config import get_default_db_path
except ImportError:
    get_default_db_path = None


# GLOBAL SYSTEM THEME MAP
ACTIVE_THEME_MAP = {
    "#6579BE": "#EAB099",
    "#E9DFD8": "#FF7F50",
    "#F54800": "#AFAFDA",
    "#FDF1F5": "#EE8E46",
    "#8A6729": "#EBC8B3",
    "#ECE7E2": "#4A7766",
    "#19485F": "#D9E0A4",
    "#285B23": "#F2CFF1",
    "#92736C": "#FDF1F5",
    "#000000": "#FFFFFF",
    "#FFFFFF": "#000000",
    "#FFFFFE": "#DDDDDD",
    "#DDDDDD": "#FFFFFF",
    "#FFFFFD": "#0000FF",
    "#000001": "#FF0000",
    "#000002": "#00FF00",
}


class KanbanCard(QFrame):
    """
    Custom QFrame GUI component representing a single task in the Kanban board.

    Responsible for rendering task metadata (title, due date, priority) into a visually
    distinct bounded card, applying dynamic background pastel colors based on theme,
    and handling custom word-wrapping constraints.
    """

    def __init__(self, task, dashboard):
        """
        Initializes the physical Kanban Card and maps it to the backing database model.

        Args:
            task (Task): The data model containing title, status, and theme data.
            dashboard (DashboardInterface): Reference back to the parent UI controller
                                            to allow context menu routing.
        """
        super().__init__()
        self.task = task
        self.dashboard = dashboard

        bg_hex = (
            task.color
            if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
            else "#333333"
        )
        fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")

        bg_color = QColor(bg_hex)
        bg_css = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 120)"

        # Resolves a QLabel limitation where unbroken continuous character strings
        # fail to trigger word-wrap by injecting zero-width spaces (\u200b).
        def shatter_gibberish(text):
            """
            Forces word-wrapping on continuous alphanumeric strings that exceed component bounds.

            Identifies unbroken strings longer than 20 characters and injects zero-width
            space characters (\\u200b) at 15-character intervals to force PySide6 layout engines
            to execute a soft carriage-return instead of overflowing the screen.

            Args:
                text (str): The raw user-generated string to be processed.

            Returns:
                str: The processed string with safe line-break anchors injected.
            """
            if not text:
                return ""
            words = text.split(" ")
            shattered = []
            for w in words:
                if len(w) > 20:
                    # Inject an invisible zero-width space every 15 characters to create breakpoints
                    shattered.append(
                        "\u200b".join(w[i : i + 15] for i in range(0, len(w), 15))
                    )
                else:
                    shattered.append(w)
            return " ".join(shattered)

        # --------- URGENCY BORDER OVERRIDE ---------
        from PySide6.QtCore import QDate

        def is_task_urgent(t):
            if t.status == "Completed":
                return False
            if not t.due_date:
                return False
            parsed_date = QDate.fromString(
                str(t.due_date).strip(), Qt.DateFormat.ISODate
            )
            if not parsed_date.isValid():
                return False
            return QDate.currentDate().daysTo(parsed_date) <= 2

        border_css = (
            "border-left: 5px solid #FF4D4D;"
            if is_task_urgent(task)
            else "border: 1px solid rgba(255,255,255,0.2);"
        )

        # Build the physical card styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_css};
                border-radius: 12px;
                {border_css}
            }}
            QLabel {{
                color: {fg_hex};
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 2. Header Row (Title & High-Contrast Priority Badge)
        header_layout = QHBoxLayout()
        title_lbl = QLabel(shatter_gibberish(task.title))
        title_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_lbl.setWordWrap(True)
        title_lbl.setMinimumWidth(1)

        priority_lbl = QLabel(task.priority)
        priority_lbl.setStyleSheet(f"""
            background-color: {fg_hex};
            color: {bg_hex};
            border-radius: 6px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 11px;
        """)
        header_layout.addWidget(title_lbl, stretch=1)
        header_layout.addWidget(priority_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_layout)

        # 3. Description
        if task.description:
            desc_lbl = QLabel(shatter_gibberish(task.description))
            desc_lbl.setStyleSheet("font-size: 13px; opacity: 0.9;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setMinimumWidth(1)
            layout.addWidget(desc_lbl)

        # 4. Footer Row (Due Date)
        if task.due_date:
            footer_layout = QHBoxLayout()
            due_lbl = QLabel(f"📅 {task.due_date}")
            due_lbl.setStyleSheet("font-size: 12px; font-weight: bold; opacity: 0.8;")
            footer_layout.addWidget(due_lbl)
            footer_layout.addStretch()
            layout.addLayout(footer_layout)

        # 5. Context Menu Engine Integration
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    def show_menu(self, pos):
        # Passes control securely back to the Dashboard Controller
        self.dashboard.show_kanban_context_menu(self.task, self.mapToGlobal(pos))

    def sizeHint(self):
        """
        Explicitly overrides the QLayout constraint engine to prevent horizontal ballooning.

        Returns:
            QSize: A forced horizontal boundary of 200px while maintaining dynamic height.
        """
        from PySide6.QtCore import QSize

        original_size = super().sizeHint()
        return QSize(200, original_size.height())


class DashboardInterface(QWidget):
    """
    Main controller and user interface for the Efficio Dashboard.

    This class manages the primary application routing loop, handling switching
    between the standard dashboard view, the Kanban board, and the Trash bin.
    It maintains direct synchronization with the SQLite TaskManager backend.
    """

    def __init__(self, parent=None, db_file=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")

        self.current_mode = "active"

        # 1. First, check if a direct path was passed or parent has it
        if db_file is None and parent is not None:
            db_file = getattr(parent, "db_file", None)

        # 2. If STILL None, calculate the absolute path robustly
        if db_file is None:
            # Get the path to the 'src' directory
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(src_dir, "data")

            # CRITICAL FIX: Ensure the 'data' directory actually exists
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            db_file = os.path.join(data_dir, "efficio.db")

        self.db_file = db_file
        self.task_manager = TaskManager(self.db_file)

        # Sidebar UI State tracking
        self.sidebar_expanded = False

        # Safely calculate absolute path to the teammate's image
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.preset_image_path = os.path.join(
            src_dir, "..", "ref", "Efficio_UI", "images", "pastel-bg.jpg"
        )

        # Setup the Glassmorphism Background Blur
        self.bg_label = QLabel(self)
        self.bg_label.setStyleSheet("border: none;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(30)
        self.bg_label.setGraphicsEffect(blur)

        self.setup_ui()
        self.update_background()
        self.load_tasks()

    # Window Resizing Engines (Paste directly under __init__)
    def resizeEvent(self, event):
        self.update_background()
        super().resizeEvent(event)

    def update_background(self):
        """
        Dynamically adjusts the application background based on current window geometry.

        Attempts to load a standard graphic asset (QPixmap). If the asset is missing
        or a file IO exception occurs, it safely resolves to a high-contrast dark solid color.
        """
        try:
            # Check if your teammate actually pushed the image file
            if os.path.exists(self.preset_image_path):
                pixmap = QPixmap(self.preset_image_path).scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.bg_label.setPixmap(pixmap)
            else:
                # Safe fallback color if image doesn't exist so tasks are visible
                self.bg_label.setStyleSheet("background-color: #4A5568;")

            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            self.bg_label.setStyleSheet("background-color: #4A5568;")

    def setup_ui(self):
        """
        Architects and renders the primary application grid and interactive widgets.

        Initializes the three core spatial components:
        1. The Interactive Left-Sidebar navigation.
        2. The Central Multi-View Stack (Dashboard Tree & Kanban Matrix).
        3. The Right-Panel Analytics (Calendar & Performance).
        """
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)

        # ---------------- Sidebar ----------------
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(60)
        self.sidebar.setStyleSheet(
            "QFrame { background-color: rgba(0,0,0,0.4); border-radius: 20px; }"
        )

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(15)

        toggle_container = QHBoxLayout()
        self.toggle_btn = QPushButton("≡")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setStyleSheet("""
        QPushButton {
        background-color: rgba(255,255,255,0.1);
        color: white;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        }
        QPushButton:hover {
        background-color: rgba(255,255,255,0.2);
        }""")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        toggle_container.addWidget(self.toggle_btn)
        toggle_container.addStretch()
        self.sidebar_layout.addLayout(toggle_container)

        self.sidebar_options = []
        # Restructured sidebar buttons
        for text in ["Dashboard", "Kanban Board", "Trash Bin"]:
            btn = QPushButton("")
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
            QPushButton {
            background-color: rgba(255,255,255,0.05);
            color: white;
            border-radius: 10px;
            font-size: 14px;
            border: 1px solid rgba(255,255,255,0.1);
            }
            QPushButton:hover {
            background-color: rgba(255,255,255,0.15);
            }""")
            if text == "Dashboard":
                btn.clicked.connect(lambda: self.set_mode("active"))
            elif text == "Kanban Board":
                btn.clicked.connect(lambda: self.set_mode("kanban"))
            elif text == "Trash Bin":
                btn.clicked.connect(lambda: self.set_mode("trash"))

            self.sidebar_layout.addWidget(btn)
            self.sidebar_options.append((btn, text))
        self.sidebar_layout.addStretch()

        # ---------------- STACKED WIDGET CORE ----------------
        self.content_stack = QStackedWidget()

        # --- PAGE 1: GitHub-Style Dashboard ---
        self.page_dashboard = QWidget()
        dash_main_layout = QHBoxLayout(self.page_dashboard)
        dash_main_layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- Task Section ----------------
        task_section_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)  # Clean spacing between elements

        self.title_label = QLabel("My Tasks")
        self.title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: white;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks...")
        self.search_bar.setFixedWidth(200)
        self.search_bar.setStyleSheet("""QLineEdit {
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px;
        padding: 5px 8px;
        color: white;
        font-size: 14px;
        }
        QLineEdit:focus {
        border: 1px solid rgba(255,255,255,0.4);
        background-color: rgba(255,255,255,0.15);
        }""")
        self.search_bar.textChanged.connect(lambda: self.load_tasks())
        header_layout.addWidget(self.search_bar)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.setStyleSheet("""QPushButton {
        background-color: rgba(0,0,0,0);
        border-radius: 20px;
        font-size: 35px;
        font-weight: bold;
        color: white;
        padding-top: -8px;
        padding-left: 2px;
        }
        QPushButton:hover {
        background-color: rgba(255,255,255,0.1); }
        """)
        self.add_btn.clicked.connect(self.show_add_task_dialog)
        header_layout.addWidget(self.add_btn)

        task_section_layout.addLayout(header_layout)
        task_section_layout.addSpacing(1)

        # --------- URGENCY BANNER INJECTION ---------
        self.urgent_banner_btn = QPushButton()
        self.urgent_banner_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4D;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.urgent_banner_btn.hide()

        # Acts as a toggle.
        def toggle_urgency_filter():
            if self.search_bar.text() == "is:urgent":
                self.search_bar.setText("")
            else:
                self.search_bar.setText("is:urgent")

        self.urgent_banner_btn.clicked.connect(toggle_urgency_filter)
        task_section_layout.addWidget(self.urgent_banner_btn)
        # ---------------------------------------------

        task_card = QFrame()
        task_card.setStyleSheet("""QFrame {
        background-color: rgba(0,0,0,0.5);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        }""")
        task_layout = QVBoxLayout(task_card)
        task_layout.setSpacing(10)

        # ---------------- Native QTreeWidget Spreadsheet ----------------
        self.task_tree = QTreeWidget()
        self.task_tree.setColumnCount(3)
        self.task_tree.setHeaderHidden(True)
        self.task_tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.task_tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.task_tree.setAnimated(False)
        self.task_tree.setIndentation(0)
        self.task_tree.setExpandsOnDoubleClick(False)

        # Styles to perfectly match the Efficio Dark Theme
        self.task_tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(30, 35, 40, 0.8);
                color: white;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.08);
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #21262d;
                color: #ffffff;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #30363d;
            }
            QTreeWidget::item:selected { background-color: rgba(255,255,255,0.1); }
            /* Overrides standard OS branch expansion icons to maintain a minimal UI aesthetic */
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings { image: none; }
        """)

        # TreeWidget Column Constraint Configuration
        header = self.task_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Task Title
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Due Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Priority
        self.task_tree.setColumnWidth(
            1, 140
        )  # Locks the column strictly so it never balloons
        self.task_tree.setColumnWidth(2, 90)

        # Right-Click Menu Support Integration
        self.task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_tree.customContextMenuRequested.connect(self.show_table_menu)
        self.task_tree.itemClicked.connect(self.toggle_group_expansion)

        task_layout.addWidget(self.task_tree)
        task_section_layout.addWidget(task_card)

        # Right Panel (Calendar) -> Only visible on Page 1
        right_panel_layout = QVBoxLayout()
        calendar_card = QFrame()
        calendar_card.setStyleSheet("""QFrame {
        background-color: rgba(0,0,0,0.5);
        border-radius: 20px;
        padding: 15px;
        }""")
        cal_layout = QVBoxLayout(calendar_card)
        cal_layout.setContentsMargins(0, 0, 0, 0)

        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setMinimumHeight(280)
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: rgba(0,0,0,0); color: white; border: none;
            }
            QCalendarWidget QToolButton {
                background-color: rgba(0,0,0,0);
                color: white;
                border: none;
                font-weight: bold;
                font-size: 16px;
                padding-right: 20px;
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
                width: 20px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: rgba(0,0,0,0); color: white;
                selection-background-color: #ff4ecb; selection-color: white;
            }
            QCalendarWidget QHeaderView::section {
                background-color: rgba(0,0,0,0); color: white;
            }
        """)

        cal_layout.addWidget(calendar)

        self.analytics_widget = AnalyticsWidget()

        right_panel_layout.addWidget(calendar_card, stretch=0)
        right_panel_layout.addWidget(self.analytics_widget, stretch=1)

        dash_main_layout.addLayout(task_section_layout, 3)
        dash_main_layout.addLayout(right_panel_layout, 2)

        # --- PAGE 2: Full-Width Kanban Board ---
        self.page_kanban = QWidget()
        kanban_page_layout = QVBoxLayout(self.page_kanban)
        kanban_page_layout.setContentsMargins(0, 0, 0, 0)

        # Kanban Header Top Row
        kanban_header = QHBoxLayout()
        kanban_title = QLabel("Kanban Board")
        kanban_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        kanban_header.addWidget(kanban_title)
        kanban_header.addStretch()

        # Dedicated Kanban Search Bar
        self.kanban_search_bar = QLineEdit()
        self.kanban_search_bar.setPlaceholderText("Search kanban...")
        self.kanban_search_bar.setFixedWidth(200)
        self.kanban_search_bar.setStyleSheet("""QLineEdit {
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px;
        padding: 5px 8px;
        color: white;
        font-size: 14px;
        }
        QLineEdit:focus {
        border: 1px solid rgba(255,255,255,0.4);
        background-color: rgba(255,255,255,0.15);
        }""")
        self.kanban_search_bar.textChanged.connect(lambda: self.load_tasks())
        kanban_header.addWidget(self.kanban_search_bar)

        # Add Button specifically for Kanban
        self.kanban_add_btn = QPushButton("+")
        self.kanban_add_btn.setFixedSize(40, 40)
        self.kanban_add_btn.setStyleSheet("""QPushButton {
        background-color: rgba(0,0,0,0);
        border-radius: 20px;
        font-size: 35px;
        font-weight: bold;
        color: white;
        padding-top: -8px;
        padding-left: 2px; }
        QPushButton:hover {
        background-color: rgba(255,255,255,0.1);
        }""")
        self.kanban_add_btn.clicked.connect(self.show_add_task_dialog)
        kanban_header.addWidget(self.kanban_add_btn)

        kanban_page_layout.addLayout(kanban_header)

        # --------- URGENCY BANNER INJECTION (KANBAN) ---------
        self.kanban_urgent_banner = QPushButton()
        self.kanban_urgent_banner.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4D;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                margin-top: 5px;
                margin-bottom: 5px;
                margin-left: 15px;
                margin-right: 15px;
            }
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.kanban_urgent_banner.hide()

        def toggle_kanban_urgency():
            if self.kanban_search_bar.text() == "is:urgent":
                self.kanban_search_bar.setText("")
            else:
                self.kanban_search_bar.setText("is:urgent")

        self.kanban_urgent_banner.clicked.connect(toggle_kanban_urgency)
        kanban_page_layout.addWidget(self.kanban_urgent_banner)
        # ---------------------------------------------------

        # Transferring scroll matrix into Page 2
        kanban_scroll_matrix = QScrollArea()
        kanban_scroll_matrix.setWidgetResizable(True)
        kanban_scroll_matrix.setStyleSheet("""QScrollArea {
        background: rgba(0,0,0,0.3);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
        }
        QScrollBar:horizontal {
        background: rgba(0,0,0,0.2);
        height: 10px;
        border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
        background: rgba(255,255,255,0.4);
        border-radius: 5px; }
        """)
        kanban_container = QWidget()
        kanban_container.setStyleSheet("background: transparent;")

        kanban_internal_layout = QHBoxLayout(kanban_container)
        kanban_internal_layout.setContentsMargins(15, 15, 15, 15)
        kanban_internal_layout.setSpacing(15)

        def create_lane(title_text):
            """
            Creates a single Kanban lane (column) with a title header and scrollable content area.

            Args:
                title_text (str): The text to display in the lane header (e.g., "To-Do").

            Returns:
                QFrame: The fully constructed lane widget.
            """

            container = QFrame()
            container.setMinimumWidth(280)
            container.setStyleSheet("""QFrame {
            background-color: rgba(0,0,0,0.4);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.15);
            }""")
            lane_main = QVBoxLayout(container)
            lane_main.setContentsMargins(5, 10, 5, 5)

            title = QLabel(title_text)
            title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lane_main.addWidget(title)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("""QScrollArea {
            background: transparent;
            border: none;
            }
            QScrollBar:vertical {
            background: rgba(0,0,0,0.2);
            width: 8px;
            border-radius: 4px;
            }
            QScrollBar::handle:vertical {
            background: rgba(255,255,255,0.4);
            border-radius: 4px;
            }""")

            content = QWidget()
            content.setStyleSheet("background: transparent;")
            layout = QVBoxLayout(content)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout.setContentsMargins(5, 5, 12, 5)
            layout.setSpacing(15)

            scroll.setWidget(content)
            lane_main.addWidget(scroll)
            return container, layout

        todo_container, self.todo_layout = create_lane("To-Do")
        inprogress_container, self.inprogress_layout = create_lane("In Progress")
        done_container, self.done_layout = create_lane("Done")

        kanban_internal_layout.addWidget(todo_container, 1)
        kanban_internal_layout.addWidget(inprogress_container, 1)
        kanban_internal_layout.addWidget(done_container, 1)
        kanban_internal_layout.addStretch()

        kanban_scroll_matrix.setWidget(kanban_container)
        kanban_page_layout.addWidget(kanban_scroll_matrix)

        # Assemble the Stacked Widget Component
        self.content_stack.addWidget(self.page_dashboard)  # Index 0
        self.content_stack.addWidget(self.page_kanban)  # Index 1

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_stack, stretch=1)

    def toggle_sidebar(self):
        """Animated Sidebar functionality"""
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(60)
            for btn, text in self.sidebar_options:
                btn.setText("")
        else:
            self.sidebar.setFixedWidth(150)
            for btn, text in self.sidebar_options:
                btn.setText(text)
        self.sidebar_expanded = not self.sidebar_expanded

    def load_tasks(self):
        """
        Refreshes the entire dashboard view by querying the database and repopulating widgets.

        This method handles the complete lifecycle of the task display:
        1. Clears all existing widgets to prevent memory leaks (deleteLater).
        2. Executes a filtered query (respecting search terms and active mode).
        3. Iterates through the results, instantiating KanbanCard components.
        4. Applies theme-specific styling and layout constraints.
        """

        # 1. Destroy everything cleanly before drawing to prevent PySide6 memory leaks
        for layout in [
            self.todo_layout,
            self.inprogress_layout,
            self.done_layout,
        ]:
            while layout.count():
                child = layout.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()

        # 2. Get the active query intelligently
        query = ""
        if self.current_mode == "kanban" and hasattr(self, "kanban_search_bar"):
            query = self.kanban_search_bar.text()
        elif hasattr(self, "search_bar"):
            query = self.search_bar.text()

        # Prevent SQLite from trying to literally search for "is:urgent" in the Title
        db_query = "" if query == "is:urgent" else query

        # 3. Pull from standard DB or Trash DB
        if self.current_mode == "trash":
            tasks = self.task_manager.get_deleted_tasks(db_query)
        else:
            tasks = self.task_manager.get_all_tasks(db_query)

        # --------- CORE URGENCY ALGORITHM ---------
        def is_task_urgent(t):
            if t.status == "Completed":
                return False
            if not t.due_date:
                return False
            parsed_date = QDate.fromString(
                str(t.due_date).strip(), Qt.DateFormat.ISODate
            )
            if not parsed_date.isValid():
                return False
            days_to_due = QDate.currentDate().daysTo(parsed_date)
            return (
                days_to_due <= 2
            )  # Anything overdue or within 48 hours is considered an emergency

        # Intercept the database pull and artificially slice it if the banner was clicked
        if query == "is:urgent":
            tasks = [t for t in tasks if is_task_urgent(t)]

        urgent_count = sum(1 for t in tasks if is_task_urgent(t))

        # Dynamic Banner Scaling
        if urgent_count > 0:
            banner_text = (
                f"⚠️ Viewing {urgent_count} Urgent Tasks! (Click here to close filter)"
                if query == "is:urgent"
                else f"⚠️ {urgent_count} Tasks require immediate attention! Click to Focus."
            )

            self.urgent_banner_btn.setText(banner_text)
            self.urgent_banner_btn.show()

            if hasattr(self, "kanban_urgent_banner"):
                self.kanban_urgent_banner.setText(banner_text)
                self.kanban_urgent_banner.show()
        else:
            self.urgent_banner_btn.hide()
            if hasattr(self, "kanban_urgent_banner"):
                self.kanban_urgent_banner.hide()

            # If they just finished marking the last urgent task Completed, clear the filter so we don't stare at an empty grid
            if query == "is:urgent":
                if hasattr(self, "search_bar"):
                    self.search_bar.setText("")
                if hasattr(self, "kanban_search_bar"):
                    self.kanban_search_bar.setText("")
        # ------------------------------------------

        # 4. Spatially route cards to the correct SPA View Matrix
        if self.current_mode == "kanban":
            for task in tasks:
                card = KanbanCard(task, self)
                if task.status == "Completed":
                    self.done_layout.addWidget(card)
                elif task.status == "In Progress":
                    self.inprogress_layout.addWidget(card)
                else:
                    self.todo_layout.addWidget(card)
        else:
            # INTERACTIVE QTREEWIDGET LAYERING
            self.task_tree.clear()

            # 1. Create the Top-Level Groups (Injected native arrows back)
            todo_group = QTreeWidgetItem(["   ▼ To-Do", "", ""])
            inprog_group = QTreeWidgetItem(["   ▼ In Progress", "", ""])
            done_group = QTreeWidgetItem(["   ▼ Done", "", ""])

            # Stylize the Dropdowns
            for grp in [todo_group, inprog_group, done_group]:
                grp.setFirstColumnSpanned(True)
                grp.setSizeHint(0, QSize(0, 50))

                # BACKGROUND COLOR ACROSS THE ENTIRE LINE
                for col in range(3):
                    grp.setBackground(col, QColor(0, 0, 0, 160))

                font = grp.font(0)
                font.setBold(True)
                font.setPointSize(13)  # Increased font size
                grp.setFont(0, font)
                grp.setForeground(0, QColor(255, 255, 255, 220))

                # NATIVE SECTION SEPARATION
                if grp != todo_group:
                    spacer = QTreeWidgetItem(["", "", ""])
                    spacer.setFlags(Qt.ItemFlag.NoItemFlags)
                    spacer.setSizeHint(0, QSize(0, 20))
                    self.task_tree.addTopLevelItem(spacer)

                self.task_tree.addTopLevelItem(grp)
                grp.setExpanded(True)

                inline_header = QTreeWidgetItem(
                    ["     Task Title", "Due Date", "Priority   "]
                )
                inline_header.setFlags(Qt.ItemFlag.NoItemFlags)
                inline_header.setSizeHint(
                    0, QSize(0, 32)
                )  # Taller row for breathing room

                inline_font = inline_header.font(0)
                inline_font.setPointSize(11)
                inline_font.setBold(True)

                for col in range(3):
                    inline_header.setForeground(
                        col, QColor(160, 170, 180)
                    )  # Brighter Gray text
                    inline_header.setBackground(
                        col, QColor(15, 20, 25, 80)
                    )  # Subtle shadow row
                    inline_header.setFont(col, inline_font)  # Applies the bigger font

                inline_header.setTextAlignment(
                    2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                grp.addChild(inline_header)

            for task in tasks:
                if task.status == "Completed":
                    parent_grp = done_group
                elif task.status == "In Progress":
                    parent_grp = inprog_group
                else:
                    parent_grp = todo_group

                # 3. Build the Raw Text Row
                row_item = QTreeWidgetItem(
                    [
                        task.title,
                        task.due_date if task.due_date else "--",
                        task.priority,
                    ]
                )
                row_item.setSizeHint(0, QSize(0, 32))

                row_item.setData(0, Qt.ItemDataRole.UserRole, task.id)

                # NATIVE PASTEL UI
                bg_hex = (
                    task.color
                    if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
                    else "#333333"
                )
                fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")

                base = QColor(bg_hex)
                pastel = QColor(base.red(), base.green(), base.blue(), 50)

                for col in range(3):
                    row_item.setBackground(col, pastel)

                # Columns 0 and 2 use QWidget overlays (cell_container, badge_container)
                # for their visual display. Setting their text to transparent prevents
                # double-rendering while keeping raw data readable by automated tests.
                row_item.setForeground(
                    0, QColor(0, 0, 0, 0)
                )  # transparent — widget paints this
                row_item.setForeground(
                    1, QColor(fg_hex)
                )  # due date — no overlay, themed color
                row_item.setForeground(
                    2, QColor(0, 0, 0, 0)
                )  # transparent — badge widget paints this

                row_item.setTextAlignment(
                    1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )

                # --------- LEFT BORDER INJECTION ---------
                urgent = is_task_urgent(task)
                if urgent:
                    row_item.setForeground(
                        1, QColor("#FF4D4D")
                    )  # The Date Text explicitly turns RED

                cell_container = QWidget()
                cell_container.setStyleSheet(
                    "background: transparent; border: none; margin: 0px; padding: 0px;"
                )
                cell_layout = QHBoxLayout(cell_container)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.setSpacing(6)

                if urgent:
                    left_indicator = QFrame()
                    left_indicator.setFixedSize(4, 20)
                    left_indicator.setStyleSheet(
                        "background-color: #FF4D4D; border-radius: 2px; border: none;"
                    )
                    cell_layout.addWidget(left_indicator)
                else:
                    # Inject an invisible bounding box to force equal indentation and prevent wall-kissing
                    spacer = QFrame()
                    spacer.setFixedSize(4, 20)
                    spacer.setStyleSheet("background: transparent; border: none;")
                    cell_layout.addWidget(spacer)

                title_lbl = QLabel(task.title)
                title_lbl.setStyleSheet(
                    f"color: {fg_hex}; font-size: 13px; background: transparent;"
                )
                cell_layout.addWidget(title_lbl, stretch=1)

                parent_grp.addChild(row_item)

                # Binds the physical QWidget drawing right into Column 0
                self.task_tree.setItemWidget(row_item, 0, cell_container)

                # --------- RESTORED: Inject Priority Badge on the FAR RIGHT Corner ---------
                badge = QLabel(task.priority)
                badge.setFixedSize(70, 20)  # Locks badge to perfect pill proportions
                badge.setStyleSheet(
                    f"background-color: {bg_hex}; color: {fg_hex}; border-radius: 4px; padding: 2px 0px; font-size: 11px; font-weight: bold; border: none;"
                )
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

                badge_container = QWidget()
                badge_layout = QHBoxLayout(badge_container)
                badge_layout.setContentsMargins(0, 0, 5, 0)
                badge_layout.addStretch()
                badge_layout.addWidget(badge)

                self.task_tree.setItemWidget(row_item, 2, badge_container)
                # -------------------------------------------------------------------------

        # Refresh analytics panel so charts always mirror current task state
        if hasattr(self, "analytics_widget"):
            self.analytics_widget.refresh(self.task_manager)

    def show_kanban_context_menu(self, task, global_pos):
        """
        Spawns the right-click interactive menu for Kanban and TreeWidget entities.

        Dynamically adjusts allowed operations based on whether the user is viewing
        active tasks (Standard) or deleted tasks (Trash mode), then routes the execution
        to the appropriate CRUD database operation.

        Args:
            task (Task): The data payload of the selected item.
            global_pos (QPoint): The exact absolute screen coordinates to draw the menu.
        """
        menu = QMenu(self)
        if self.current_mode in ("active", "kanban"):
            pending_action = menu.addAction("Move to To-Do")
            progress_action = menu.addAction("Move to In Progress")
            done_action = menu.addAction("Move to Done")
            menu.addSeparator()
            edit_action = menu.addAction("Edit Task")
            delete_action = menu.addAction("Drop in Trash Bin")

            action = menu.exec(global_pos)
            if action == pending_action:
                self.task_manager.update_task_status(task.id, "Pending")
            elif action == progress_action:
                self.task_manager.update_task_status(task.id, "In Progress")
            elif action == done_action:
                self.task_manager.update_task_status(task.id, "Completed")
            elif action == edit_action:
                self.edit_specific_task(task.id)
            elif action == delete_action:
                self.delete_specific_task(task.id)

        elif self.current_mode == "trash":
            restore_action = menu.addAction("Restore Task")
            perm_delete_action = menu.addAction("Permanently Delete")
            action = menu.exec(global_pos)
            if action == restore_action:
                self.task_manager.restore_task(task.id)
            elif action == perm_delete_action:
                confirm = QMessageBox.warning(
                    self,
                    "Permanent Delete",
                    "Obliterate this task forever?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirm == QMessageBox.StandardButton.Yes:
                    self.task_manager.permanently_delete_task(task.id)
        self.load_tasks()

    def show_table_menu(self, pos):
        """
        Displays a context-sensitive menu for TreeWidget items when right-clicked.

        Args:
            pos (QPoint): The local position within the tree widget where the click occurred.
        """
        item = self.task_tree.itemAt(pos)

        # Prevent right-clicking empty space OR Accordion Headers
        if item is None or item.parent() is None:
            return

        # Pull the task ID out of the row to trace it
        task_id = item.data(0, Qt.ItemDataRole.UserRole)
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            self.show_kanban_context_menu(
                task, self.task_tree.viewport().mapToGlobal(pos)
            )

    def edit_specific_task(self, task_id):
        """
        Instantiates the TaskEditorDialog in 'Edit' mode and synchronizes database updates.

        Args:
            task_id (int): The unique primary key of the target task to modify.
        """

        # We abstracted this so the Kanban card can call it without relying on a QListWidgetItem
        task = self.task_manager.get_task_by_id(task_id)
        if task:
            dialog = TaskEditorDialog(self, task=task)
            if dialog.exec():
                data = dialog.get_data()
                updated_task = Task(
                    id=task_id,
                    title=data["title"],
                    description=data["description"],
                    status=data["status"],
                    created_at=task.created_at,
                    due_date=data["due_date"],
                    priority=data["priority"],
                    color=data.get("color", "#333333"),
                )
                self.task_manager.update_task(updated_task)
                self.load_tasks()

    def delete_specific_task(self, task_id):
        """
        Deletes a specific task after user confirmation.

        Args:
            task_id (int): The unique primary key of the target task to delete.
        """
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Send this task to the Trash Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.task_manager.delete_task(task_id)
            self.load_tasks()

    def show_add_task_dialog(self):
        """
        Opens the dialog to create a new task. Provides a success notification
        upon successfully saving the task to the database.
        """
        dialog = TaskEditorDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # Create Task Object
            new_task = Task(
                id=None,
                title=data["title"],
                description=data["description"],
                status=data["status"],
                created_at=datetime.now(),
                due_date=data["due_date"],
                priority=data["priority"],
                color=data.get("color", "#333333"),  # NEW
            )

            # Save to DB safely
            result_id = self.task_manager.add_task(new_task)

            if result_id != -1:
                # ISO 25010 Usability: Visual confirmation of success
                QMessageBox.information(
                    self,
                    "Success",
                    f"Task '{new_task.title}' was successfully created!",
                )
                self.load_tasks()
            else:
                QMessageBox.critical(
                    self, "Error", "A database error occurred while saving the task."
                )

    def show_context_menu(self, pos):
        """
        Displays a context-sensitive menu for ListWidget items when right-clicked.

        Args:
            pos (QPoint): The local position within the list widget where the click occurred.
        """
        item = self.task_list.itemAt(pos)
        if item:
            menu = QMenu(self)

            if self.current_mode == "active":
                edit_action = menu.addAction("Edit Task")
                delete_action = menu.addAction("Move to Trash")
                action = menu.exec(self.task_list.mapToGlobal(pos))

                if action == delete_action:
                    self.delete_current_task(item)
                elif action == edit_action:
                    self.edit_current_task(item)

            elif self.current_mode == "trash":
                restore_action = menu.addAction("Restore Task")
                perm_delete_action = menu.addAction("Permanently Delete")
                action = menu.exec(self.task_list.mapToGlobal(pos))

                if action == restore_action:
                    task_id = item.data(Qt.ItemDataRole.UserRole)
                    self.task_manager.restore_task(task_id)
                    self.load_tasks()
                elif action == perm_delete_action:
                    task_id = item.data(Qt.ItemDataRole.UserRole)
                    confirm = QMessageBox.warning(
                        self,
                        "Permanent Delete",
                        "This will permanently obliterate this task. Are you sure?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        self.task_manager.permanently_delete_task(task_id)
                        self.load_tasks()

    def delete_current_task(self, item):
        """
        Deletes the currently selected task from the list view.

        Args:
            item (QListWidgetItem): The list item to delete.
        """
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                "Are you sure you want to delete this task?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                self.task_manager.delete_task(task_id)
                self.load_tasks()

    def edit_current_task(self, item):
        """
        Edits the currently selected task from the list view.

        Args:
            item (QListWidgetItem): The list item to edit.
        """
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            # Fetch existing task data
            task = self.task_manager.get_task_by_id(task_id)
            if task:
                dialog = TaskEditorDialog(self, task=task)
                if dialog.exec():
                    data = dialog.get_data()

                    # Update Task Object
                    updated_task = Task(
                        id=task_id,
                        title=data["title"],
                        description=data["description"],
                        status=data["status"],
                        created_at=task.created_at,
                        due_date=data["due_date"],
                        priority=data["priority"],
                        color=data.get("color", "#FFFFFF"),  # NEW
                    )

                    self.task_manager.update_task(updated_task)
                    self.load_tasks()

    def set_mode(self, mode):
        """
        Executes a High-Level layout pivot between major Application Views.

        Adjusts the QStackedWidget index, hides/shows appropriate global action buttons,
        and fundamentally shifts the underlying SQL queries for the view matrix.

        Args:
            mode (str): The target application state ("active", "kanban", or "trash").
        """
        self.current_mode = mode
        if mode == "trash":
            self.title_label.setText("Trash Bin")
            self.add_btn.hide()
            self.content_stack.setCurrentIndex(
                0
            )  # Trash shows via the Dashboard layout
        elif mode == "active":
            self.title_label.setText("My Tasks")
            self.add_btn.show()
            self.content_stack.setCurrentIndex(0)  # Dashboard Profile
        elif mode == "kanban":
            # Swaps the screen purely to the massive Kanban Board!
            self.content_stack.setCurrentIndex(1)

        self.load_tasks()

    def toggle_group_expansion(self, item, column):
        """
        Toggles the expanded/collapsed state of main Accordion headers on single click.

        Evaluates whether the clicked item is a Top-Level group based on child count
        and natively updates the GUI expansion state and directional arrow strings.

        Args:
            item (QTreeWidgetItem): The row item clicked by the user.
            column (int): The index of the column clicked.
        """
        if item.childCount() > 0:
            if item.isExpanded():
                item.setExpanded(False)
                item.setText(0, item.text(0).replace("▼", "▶"))
            else:
                item.setExpanded(True)
                item.setText(0, item.text(0).replace("▶", "▼"))
