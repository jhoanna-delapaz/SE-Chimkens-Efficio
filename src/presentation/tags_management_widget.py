import logging
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFrame,
    QGridLayout,
)

from data.models import Tag
from business.task_manager import TaskManager

logger = logging.getLogger(__name__)

# Reusing the aesthetic colors from the application
PRESET_COLORS = [
    ("#6579BE", "Ocean Peach"),
    ("#E9DFD8", "Warm Sand"),
    ("#F54800", "Vibrant Orange"),
    ("#FDF1F5", "Soft Cream"),
    ("#8A6729", "Earthy Brown"),
    ("#ECE7E2", "Muted Stone"),
    ("#19485F", "Deep Ocean"),
    ("#285B23", "Forest Pink"),
    ("#92736C", "Dusty Rose"),
    ("#000000", "Pitch Black"),
    ("#FFFFFF", "Pure White"),
    ("#FF4D4D", "Danger Red"),
    ("#FFA500", "Warning Orange"),
    ("#4CAF50", "Success Green"),
    ("#9C27B0", "Deep Purple"),
    ("#00BCD4", "Cyan Blue"),
    ("#E91E63", "Pink Ruby"),
    ("#FFEB3B", "Bright Yellow"),
    ("#607D8B", "Blue Grey"),
    ("#795548", "Coffee Brown"),
]


class TagsManagementWidget(QWidget):
    """
    Dedicated view for managing system tags (CRUD operations).
    ISO 25010: Enhances Modularity and Operability.
    """

    def __init__(self, parent=None, task_manager: TaskManager = None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.selected_color = "#333333"  # Default
        self.color_buttons = []
        self.editing_tag_id = None
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(30)

        # --- Left Panel: Tag List ---
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame { background-color: #2F3239; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        title_lbl = QLabel("🏷️ Manage Tags")
        title_lbl.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: white; border: none; background: transparent;"
        )
        left_layout.addWidget(title_lbl)

        self.tags_list = QListWidget()
        self.tags_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item { padding: 8px 12px; border-radius: 4px; margin-bottom: 4px; }
            QListWidget::item:hover { background-color: rgba(255, 255, 255, 0.05); }
            QListWidget::item:selected { background-color: rgba(101, 121, 190, 0.15); border-left: 4px solid #6579BE; border-radius: 4px; font-weight: bold; }
        """)
        self.tags_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.tags_list.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.tags_list)

        self.delete_btn = QPushButton("🗑️ Delete Selected Tag")
        self.delete_btn.hide()
        self.delete_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 0.05); color: #A0A0A0; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 77, 77, 0.2); color: #FF4D4D; }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_tags_bulk)
        left_layout.addWidget(self.delete_btn)

        # --- Right Panel: Create/Edit Form ---
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame { background-color: #2F3239; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        self.form_title = QLabel("Create New Tag")
        self.form_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white; border: none; background: transparent;"
        )
        right_layout.addWidget(self.form_title)

        right_layout.addWidget(
            QLabel(
                "Tag Name",
                styleSheet="color: #A0A0A0; font-size: 13px; border: none; background: transparent;",
            )
        )
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Work, Urgent, Bug")
        self.name_input.setStyleSheet("""
            QLineEdit { background-color: rgba(255,255,255,0.1); color: white; border-radius: 8px; padding: 10px; border: 1px solid rgba(255,255,255,0.2); }
            QLineEdit:focus { border: 1px solid #6579BE; background-color: rgba(255,255,255,0.15); }
        """)
        right_layout.addWidget(self.name_input)

        right_layout.addWidget(
            QLabel(
                "Select Color",
                styleSheet="color: #A0A0A0; font-size: 13px; border: none; background: transparent;",
            )
        )

        # Color Grid
        color_grid_widget = QWidget()
        color_grid_widget.setStyleSheet("background: transparent;")
        color_grid = QGridLayout(color_grid_widget)
        color_grid.setContentsMargins(0, 0, 0, 0)
        color_grid.setSpacing(10)

        row, col = 0, 0
        for hex_code, name in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(name)
            btn.setProperty("hex_code", hex_code)

            # Use property to identify selected
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {hex_code}; border-radius: 8px; border: 2px solid transparent; }}
                QPushButton:hover {{ border: 2px solid rgba(255,255,255,0.5); }}
                QPushButton[selected="true"] {{ border: 3px solid white; }}
            """)
            btn.clicked.connect(
                lambda checked, h=hex_code, b=btn: self.select_color(h, b)
            )
            self.color_buttons.append(btn)

            color_grid.addWidget(btn, row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1

        right_layout.addWidget(color_grid_widget)

        # Default select first color
        if self.color_buttons:
            self.select_color(PRESET_COLORS[0][0], self.color_buttons[0])

        right_layout.addStretch()

        self.save_btn = QPushButton("Save Tag")
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #285B23; color: white; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #367A2F; }
        """)
        self.save_btn.clicked.connect(self.save_tag)

        self.cancel_edit_btn = QPushButton("Cancel Edit")
        self.cancel_edit_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #A0A0A0; font-weight: bold; padding: 8px; border-radius: 6px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.05); color: white; }
        """)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit)
        self.cancel_edit_btn.hide()

        form_actions = QHBoxLayout()
        form_actions.addWidget(self.cancel_edit_btn)
        form_actions.addWidget(self.save_btn, stretch=1)
        right_layout.addLayout(form_actions)

        self.main_layout.addWidget(left_panel, stretch=1)
        self.main_layout.addWidget(right_panel, stretch=1)

    def select_color(self, hex_code, button):
        self.selected_color = hex_code
        for btn in self.color_buttons:
            btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        button.setProperty("selected", "true")
        button.style().unpolish(button)
        button.style().polish(button)

    def refresh(self):
        if not self.task_manager:
            return

        self.tags_list.clear()
        tags = self.task_manager.get_all_tags()

        for tag in tags:
            item = QListWidgetItem()
            # Custom widget for list item to show color badge
            widget = QWidget()
            widget.setStyleSheet("background: transparent;")
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)

            # Unify design: Render as a full pill badge instead of a circle next to text
            t_color = "#FFFFFF"
            try:
                hex_c = tag.color.lstrip("#")
                r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
                luma = 0.299 * r + 0.587 * g + 0.114 * b
                t_color = "#000000" if luma > 160 else "#FFFFFF"
            except Exception:
                pass

            badge_lbl = QLabel(tag.name)
            badge_lbl.setStyleSheet(
                f"background-color: {tag.color}; color: {t_color}; border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 12px;"
            )
            badge_lbl.setFixedHeight(26)
            badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(badge_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addStretch()

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background-color: rgba(255,255,255,0.1); border-radius: 6px; }"
            )
            edit_btn.clicked.connect(lambda checked, t=tag: self.edit_inline_tag(t))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background-color: rgba(255,77,77,0.2); border-radius: 6px; }"
            )
            del_btn.clicked.connect(lambda checked, t=tag: self.delete_inline_tag(t))

            layout.addWidget(edit_btn)
            layout.addWidget(del_btn)

            item.setSizeHint(QSize(0, 50))
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tags_list.addItem(item)
            self.tags_list.setItemWidget(item, widget)

        self.cancel_edit()

    def cancel_edit(self):
        self.name_input.clear()
        self.delete_btn.setEnabled(False)
        self.editing_tag_id = None
        self.form_title.setText("Create New Tag")
        self.save_btn.setText("Save Tag")
        self.cancel_edit_btn.hide()
        if self.color_buttons:
            self.select_color(PRESET_COLORS[0][0], self.color_buttons[0])

    def on_selection_changed(self):
        selected_items = self.tags_list.selectedItems()
        if not selected_items:
            self.delete_btn.hide()
            self.cancel_edit()
            return

        self.delete_btn.show()
        self.delete_btn.setEnabled(True)
        if len(selected_items) == 1:
            self.delete_btn.setText("🗑️ Delete Selected Tag")
            tag = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.edit_inline_tag(tag)
        else:
            self.delete_btn.setText(f"🗑️ Delete {len(selected_items)} Tags")
            self.name_input.clear()
            self.editing_tag_id = None
            self.form_title.setText("Create New Tag")
            self.save_btn.setText("Save Tag")
            self.cancel_edit_btn.hide()
            if self.color_buttons:
                self.select_color(PRESET_COLORS[0][0], self.color_buttons[0])

    def edit_inline_tag(self, tag):
        self.editing_tag_id = tag.id
        self.name_input.setText(tag.name)
        self.form_title.setText("Update Tag")
        self.save_btn.setText("Update Tag")
        self.cancel_edit_btn.show()

        for btn in self.color_buttons:
            if btn.property("hex_code").lower() == tag.color.lower():
                self.select_color(tag.color, btn)
                break

    def delete_inline_tag(self, tag):
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the tag '{tag.name}'?\nThis will remove it from all associated tasks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.task_manager.delete_tag(tag.id)
            self.refresh()

    def delete_selected_tags_bulk(self):
        selected_items = self.tags_list.selectedItems()
        if not selected_items:
            return

        if len(selected_items) == 1:
            tag = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.delete_inline_tag(tag)
            return

        msg = f"Are you sure you want to delete {len(selected_items)} tags?"
        confirm = QMessageBox.question(
            self,
            "Confirm Bulk Delete",
            msg + "\nThis will remove them from all associated tasks.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                tag = item.data(Qt.ItemDataRole.UserRole)
                self.task_manager.delete_tag(tag.id)
            self.refresh()

    def save_tag(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Tag name cannot be empty.")
            return

        if self.editing_tag_id is not None:
            updated_tag = Tag(
                id=self.editing_tag_id, name=name, color=self.selected_color
            )
            self.task_manager.update_tag(updated_tag)
            self.refresh()
            self.cancel_edit()
        else:
            new_tag = Tag(id=None, name=name, color=self.selected_color)
            result = self.task_manager.add_tag(new_tag)

            if result == -1:
                QMessageBox.warning(
                    self, "Error", f"A tag with the name '{name}' already exists."
                )
            else:
                self.refresh()
