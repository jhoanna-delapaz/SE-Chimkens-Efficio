from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None
from data.models import Task
from utils.constants import ACTIVE_THEME_MAP
from utils.strings import UIStrings


class KanbanCard(QFrame):
    """
    Custom QFrame GUI component representing a single task in the Kanban board.
    ISO 25010: Improves Modifiability by isolating card rendering logic.
    """

    def __init__(self, task: Task, dashboard: any):
        super().__init__()
        self.task = task
        self.dashboard = dashboard
        self.setObjectName("KanbanCard")
        self.setup_ui()

    def setup_ui(self):
        task = self.task
        bg_hex = (
            task.color
            if (hasattr(task, "color") and task.color in ACTIVE_THEME_MAP)
            else "#333333"
        )
        fg_hex = ACTIVE_THEME_MAP.get(bg_hex, "#FFFFFF")

        bg_color = QColor(bg_hex)
        bg_css = f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 120)"

        import re

        URL_PATTERN = re.compile(r"(https?://[^\s]+)")

        def shatter_gibberish(text):
            if not text:
                return ""

            # Tokenize by whitespace but keep URLs intact
            parts = re.split(r"(\s+)", text)
            shattered_parts = []

            for p in parts:
                if not p.strip() or URL_PATTERN.match(p):
                    shattered_parts.append(p)
                elif len(p) > 20:
                    # Only shatter long non-URL words
                    shattered_parts.append(
                        "\u200b".join(p[i : i + 15] for i in range(0, len(p), 15))
                    )
                else:
                    shattered_parts.append(p)
            return "".join(shattered_parts)

        # --------- URGENCY BORDER OVERRIDE ---------
        from PySide6.QtCore import QDate, QDateTime

        def is_task_urgent(t):
            if t.status == UIStrings.STATUS_DONE or not t.due_date:
                return False
            due_str = str(t.due_date).strip()
            dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
            if not dt.isValid():
                d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                if not d.isValid():
                    return False
                dt = QDateTime(d, QDateTime.currentDateTime().time())
            return QDateTime.currentDateTime().secsTo(dt) <= (2 * 24 * 3600)

        urgent = is_task_urgent(task)
        border_css = (
            "border: 1px solid rgba(255,255,255,0.2); border-left: 5px solid #FF4D4D;"
            if urgent
            else "border: 1px solid rgba(255,255,255,0.2);"
        )

        bg_hover_css = (
            f"rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 180)"
        )

        border_hover_css = (
            "border: 1px solid rgba(255,255,255,0.4); border-left: 5px solid #FF4D4D;"
            if urgent
            else "border: 1px solid rgba(255,255,255,0.4);"
        )

        self.setStyleSheet(f"""
            #KanbanCard {{
                background-color: {bg_css};
                border-radius: 12px;
                {border_css}
            }}
            #KanbanCard:hover {{
                background-color: {bg_hover_css};
                {border_hover_css}
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

        header_layout = QHBoxLayout()
        title_lbl = QLabel(shatter_gibberish(task.title))
        title_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_lbl.setWordWrap(True)
        title_lbl.setMinimumWidth(1)
        title_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )  # Hover pass-through

        priority_lbl = QLabel(task.priority)
        priority_lbl.setStyleSheet(f"""
            background-color: {fg_hex};
            color: {bg_hex};
            border-radius: 6px;
            padding: 4px 8px;
            font-weight: bold;
            font-size: 11px;
        """)
        priority_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        header_layout.addWidget(title_lbl, stretch=1)
        header_layout.addWidget(priority_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_layout)

        if task.description:
            raw_desc = shatter_gibberish(task.description)
            # Auto-link URLs
            html_desc = URL_PATTERN.sub(
                r'<a href="\1" style="color: #58a6ff; text-decoration: none;">\1</a>',
                raw_desc,
            )

            desc_lbl = QLabel(html_desc)
            desc_lbl.setStyleSheet("font-size: 13px; opacity: 0.9;")
            desc_lbl.setWordWrap(True)
            desc_lbl.setMinimumWidth(1)
            desc_lbl.setOpenExternalLinks(True)
            desc_lbl.setTextInteractionFlags(
                Qt.TextInteractionFlag.LinksAccessibleByMouse
                | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(desc_lbl)

        if task.due_date:
            from PySide6.QtCore import QDate, QDateTime

            due_str = str(task.due_date).strip()
            parsed_dt = QDateTime.fromString(due_str, Qt.DateFormat.ISODate)
            if parsed_dt.isValid():
                display_str = parsed_dt.toString("MMM d, yyyy - h:mm AP")
            else:
                parsed_d = QDate.fromString(due_str, Qt.DateFormat.ISODate)
                display_str = (
                    parsed_d.toString("MMM d, yyyy") if parsed_d.isValid() else due_str
                )

            footer_layout = QHBoxLayout()
            due_lbl = QLabel(f"📅 {display_str}")
            due_lbl.setStyleSheet("font-size: 12px; font-weight: bold; opacity: 0.8;")
            due_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            footer_layout.addWidget(due_lbl)
            footer_layout.addStretch()
            layout.addLayout(footer_layout)

        if hasattr(task, "tags") and task.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setContentsMargins(0, 4, 0, 0)
            tags_layout.setSpacing(4)
            displayed_tags = task.tags[:3]
            for tag in displayed_tags:
                tag_badge = QLabel(tag.name)
                t_color = "#FFFFFF"
                try:
                    hex_c = tag.color.lstrip("#")
                    r, g, b = (
                        int(hex_c[0:2], 16),
                        int(hex_c[2:4], 16),
                        int(hex_c[4:6], 16),
                    )
                    luma = 0.299 * r + 0.587 * g + 0.114 * b
                    t_color = "#000000" if luma > 160 else "#FFFFFF"
                except Exception:
                    pass
                tag_badge.setStyleSheet(
                    f"background-color: {tag.color}; color: {t_color}; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold;"
                )
                tags_layout.addWidget(tag_badge)

            if len(task.tags) > 3:
                more_lbl = QLabel(f"+{len(task.tags) - 3}")
                more_lbl.setStyleSheet(
                    "color: #A0A0A0; font-size: 11px; font-weight: bold;"
                )
                tags_layout.addWidget(more_lbl)

            tags_layout.addStretch()
            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        # --------- ATTACHMENTS CAROUSEL ---------
        if hasattr(task, "attachments") and task.attachments:
            carousel_scroll = QScrollArea()
            carousel_scroll.setWidgetResizable(True)
            carousel_scroll.setFrameShape(QFrame.Shape.NoFrame)
            carousel_scroll.setStyleSheet(
                "background-color: transparent; border: none;"
            )
            carousel_scroll.setFixedHeight(60)
            carousel_scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            carousel_scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )

            carousel_container = QWidget()
            carousel_container.setStyleSheet("background: transparent;")
            carousel_layout = QHBoxLayout(carousel_container)
            carousel_layout.setContentsMargins(0, 0, 0, 0)
            carousel_layout.setSpacing(5)
            carousel_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            for att in task.attachments:
                thumb = QLabel()
                thumb.setFixedSize(50, 50)
                thumb.setScaledContents(True)
                thumb.setCursor(Qt.CursorShape.PointingHandCursor)

                if att.file_path.lower().endswith(".pdf"):
                    thumb.setText("PDF")
                    thumb.setStyleSheet("""
                        QLabel {
                            background-color: #EE2222; color: white; border-radius: 6px;
                            font-weight: bold; font-size: 11px; border: 1px solid rgba(255,255,255,0.2);
                        }
                        QLabel:hover { background-color: #FF3333; }
                    """)
                    thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    thumb.mousePressEvent = lambda e, p=att.file_path: (
                        self._open_image_popup(p)
                    )
                else:
                    pixmap = QPixmap(att.file_path)
                    if not pixmap.isNull():
                        thumb.setPixmap(
                            pixmap.scaled(
                                50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding
                            )
                        )
                        # Connect click event
                        thumb.mousePressEvent = lambda e, p=att.file_path: (
                            self._open_image_popup(p)
                        )
                    else:
                        thumb.setText("🖼️")
                        thumb.setStyleSheet(
                            "background: rgba(255,255,255,0.1); border-radius: 4px;"
                        )
                        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)

                carousel_layout.addWidget(thumb)

            carousel_layout.addStretch()
            carousel_scroll.setWidget(carousel_container)
            layout.addWidget(carousel_scroll)

        # Tooltip Countdown
        from utils.sorter import TaskSorter

        countdown = TaskSorter.format_due_countdown(task.due_date, task.status)
        if countdown:
            self.setToolTip(countdown)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)

    def show_menu(self, pos):
        self.dashboard.show_kanban_context_menu(self.task, self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, event):
        """
        ISO 25010: Enhances Usability. Opens the edit dialog on double-click.
        """
        self.dashboard.edit_specific_task(self.task.id)

    def sizeHint(self):
        return QSize(200, super().sizeHint().height())

    def _open_image_popup(self, file_path):
        popup = ImagePopup(file_path, self.dashboard)
        popup.exec()


class ImagePopup(QDialog):
    """
    Modal dialog to show full-size image with Escape key support.
    """

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Darkened overlay
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # This frame acts as the background overlay
        self.overlay = QFrame()
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.85);")
        self.overlay.mousePressEvent = lambda e: (
            self.accept()
        )  # Close on background click

        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(40, 40, 40, 40)

        # Content Container (stops click propagation)
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background-color: transparent; border: none;")
        self.content_frame.mousePressEvent = lambda e: (
            e.accept()
        )  # Don't close when clicking content

        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Floating Close Button Container
        close_btn_row = QHBoxLayout()
        close_btn_row.addStretch()
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white; border-radius: 20px; font-size: 18px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #EE2222; }
        """)
        self.close_btn.clicked.connect(self.accept)
        close_btn_row.addWidget(self.close_btn)
        content_layout.addLayout(close_btn_row)

        # Content area
        if file_path.lower().endswith(".pdf") and QWebEngineView:
            self.viewer = QWebEngineView()
            self.viewer.settings().setAttribute(
                self.viewer.settings().WebAttribute.PluginsEnabled, True
            )
            self.viewer.settings().setAttribute(
                self.viewer.settings().WebAttribute.PdfViewerEnabled, True
            )
            self.viewer.setUrl(QUrl.fromLocalFile(file_path))
            # Dynamic size: 90% of screen width, 85% of screen height
            screen_size = self.screen().size()
            target_w = int(screen_size.width() * 0.9)
            target_h = int(screen_size.height() * 0.85)
            self.viewer.setMinimumSize(target_w, target_h)
            content_layout.addWidget(self.viewer)
        else:
            # Image display
            self.img_lbl = QLabel()
            self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(file_path)

            if not pixmap.isNull():
                screen_size = self.screen().size()
                max_w, max_h = screen_size.width() * 0.8, screen_size.height() * 0.8
                scaled_pixmap = pixmap.scaled(
                    max_w,
                    max_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.img_lbl.setPixmap(scaled_pixmap)
            else:
                self.img_lbl.setText(
                    "Failed to load content."
                    if not file_path.lower().endswith(".pdf")
                    else "PDF Viewer not available."
                )
                self.img_lbl.setStyleSheet("color: white; font-size: 20px;")

            content_layout.addWidget(self.img_lbl)

        overlay_layout.addWidget(self.content_frame)
        self.main_layout.addWidget(self.overlay)

        self.setFixedSize(self.screen().size())

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        super().keyPressEvent(event)
