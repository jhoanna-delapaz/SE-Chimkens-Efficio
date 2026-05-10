from PySide6.QtWidgets import (
    QMenu,
    QWidgetAction,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QCheckBox,
)
from PySide6.QtCore import Signal


class TagSelectMenu(QMenu):
    """
    A GitHub-style dropdown menu for selecting tags.
    Features a search bar and a scrollable checklist of tags.
    """

    tags_changed = Signal(
        list
    )  # Emits the new list of selected Tag objects when closed

    def __init__(self, all_tags, selected_tags, parent=None):
        super().__init__(parent)
        self.all_tags = all_tags
        self.selected_tags = {
            t.id: t for t in selected_tags
        }  # Dictionary for fast lookup
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QMenu {
                background-color: #2F3239;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
            }
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tags...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.1);
                color: white; border-radius: 4px; padding: 6px; border: 1px solid rgba(255,255,255,0.2);
            }
            QLineEdit:focus {
                border: 1px solid #6579BE;
            }
        """)
        self.search_input.textChanged.connect(self.filter_tags)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(200)
        self.list_widget.setMaximumHeight(250)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent; border: none; color: white; outline: none;
            }
            QListWidget::item { border-bottom: 1px solid rgba(255,255,255,0.05); }
            QListWidget::item:hover { background-color: rgba(255,255,255,0.05); }
        """)

        self.items_data = []

        for tag in self.all_tags:
            item = QListWidgetItem()

            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(4, 4, 4, 4)
            h_layout.setSpacing(8)

            cb = QCheckBox()
            cb.setChecked(tag.id in self.selected_tags)
            # Connect using partial to capture loop variable
            cb.clicked.connect(
                lambda checked, t=tag, c=cb: self.on_tag_toggled(t, c.isChecked())
            )

            badge = QLabel(tag.name)
            # Smart contrast
            t_color = "#FFFFFF"
            try:
                hex_c = tag.color.lstrip("#")
                r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
                luma = 0.299 * r + 0.587 * g + 0.114 * b
                t_color = "#000000" if luma > 160 else "#FFFFFF"
            except Exception:
                pass

            badge.setStyleSheet(f"""
                background-color: {tag.color};
                color: {t_color};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            """)

            h_layout.addWidget(cb)
            h_layout.addWidget(badge)
            h_layout.addStretch()

            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

            self.items_data.append({"item": item, "tag": tag})

        layout.addWidget(self.list_widget)

        action = QWidgetAction(self)
        action.setDefaultWidget(container)
        self.addAction(action)

    def filter_tags(self, text):
        search_text = text.lower()
        for data in self.items_data:
            item = data["item"]
            tag = data["tag"]
            item.setHidden(search_text not in tag.name.lower())

    def on_tag_toggled(self, tag, is_checked):
        if is_checked:
            self.selected_tags[tag.id] = tag
        else:
            if tag.id in self.selected_tags:
                del self.selected_tags[tag.id]

    def hideEvent(self, event):
        super().hideEvent(event)
        # Emit signal when menu closes
        self.tags_changed.emit(list(self.selected_tags.values()))
