from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QListWidget, QListWidgetItem, QPushButton,
                               QLabel, QCheckBox, QLineEdit, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from typing import List

from src.models.pdf_page import PDFPageData
from src.services.pdf_service import PDFService


class PageListItem(QWidget):
    """Compact widget for displaying a page in the list"""

    selection_changed = Signal(bool)  # selected state

    def __init__(self, page_data: PDFPageData):
        super().__init__()
        self.page_data = page_data
        self.setup_ui()
        self.load_thumbnail()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Selection controls (same as before)
        controls_group = QGroupBox("Page Selection")
        controls_layout = QVBoxLayout()

        # Bulk selection buttons
        bulk_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        bulk_layout.addWidget(select_all_btn)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all)
        bulk_layout.addWidget(clear_all_btn)

        invert_btn = QPushButton("Invert Selection")
        invert_btn.clicked.connect(self.invert_selection)
        bulk_layout.addWidget(invert_btn)

        bulk_layout.addStretch()
        controls_layout.addLayout(bulk_layout)

        # Filter/search
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by filename or page number...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)

        controls_layout.addLayout(filter_layout)

        # Selection count
        self.count_label = QLabel("0 of 0 pages selected")
        controls_layout.addWidget(self.count_label)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Pages grid (CHANGED FROM LIST TO SCROLL AREA)
        pages_group = QGroupBox("Pages")
        pages_layout = QVBoxLayout()

        # Create scroll area with grid widget
        self.pages_scroll = QScrollArea()
        self.pages_widget = QWidget()
        from PySide6.QtWidgets import QGridLayout
        self.pages_grid = QGridLayout(self.pages_widget)
        self.pages_scroll.setWidget(self.pages_widget)
        self.pages_scroll.setWidgetResizable(True)

        pages_layout.addWidget(self.pages_scroll)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Handle Ctrl+click for multi-select
            if event.modifiers() == Qt.ControlModifier:
                self.checkbox.setChecked(not self.checkbox.isChecked())
            else:
                self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def load_thumbnail(self):
        """Load small thumbnail for this page"""
        img_data = PDFService.get_page_thumbnail(
            self.page_data.source_path,
            self.page_data.page_number,
            scale=0.2  # Smaller scale for list view
        )

        if img_data:
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            pixmap = pixmap.scaled(60, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText(f"{self.page_data.page_number + 1}")

    def on_selection_changed(self, checked: bool):
        """Handle selection state change"""
        self.page_data.selected = checked
        self.selection_changed.emit(checked)

    def set_selected(self, selected: bool):
        """Programmatically set selection"""
        self.checkbox.setChecked(selected)

    def is_selected(self) -> bool:
        """Check if this page is selected"""
        return self.checkbox.isChecked()

    def assign_profile(self, profile_name: str):
        """Assign a profile to this page"""
        self.page_data.assigned_profile = profile_name
        self.update_profile_label()
        self.set_assigned_state(True)

    def update_profile_label(self):
        """Update the profile assignment label"""
        if self.page_data.assigned_profile:
            self.profile_label.setText(f"Profile: {self.page_data.assigned_profile}")
            self.profile_label.setStyleSheet("color: #2196F3; font-size: 10px; font-weight: bold;")
        else:
            self.profile_label.setText("No profile assigned")
            self.profile_label.setStyleSheet("color: #999; font-size: 10px;")

    def set_assigned_state(self, assigned: bool):
        """Set the assigned state and disable selection if assigned"""
        if assigned:
            self.checkbox.setEnabled(False)
            self.checkbox.setChecked(False)
            self.setStyleSheet("QWidget { background-color: #f0f0f0; }")
            self.profile_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        else:
            self.checkbox.setEnabled(True)
            self.setStyleSheet("")


class PageListWidget(QWidget):
    """Widget for displaying pages in a list format with bulk selection"""

    selection_changed = Signal()  # Emitted when selection changes

    def __init__(self):
        super().__init__()
        self.page_items: List[PageListItem] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Selection controls (same as before)
        controls_group = QGroupBox("Page Selection")
        controls_layout = QVBoxLayout()

        # Bulk selection buttons
        bulk_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        bulk_layout.addWidget(select_all_btn)

        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all)
        bulk_layout.addWidget(clear_all_btn)

        invert_btn = QPushButton("Invert Selection")
        invert_btn.clicked.connect(self.invert_selection)
        bulk_layout.addWidget(invert_btn)

        bulk_layout.addStretch()
        controls_layout.addLayout(bulk_layout)

        # Filter/search
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by filename or page number...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)

        controls_layout.addLayout(filter_layout)

        # Selection count
        self.count_label = QLabel("0 of 0 pages selected")
        controls_layout.addWidget(self.count_label)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Pages grid (CHANGED FROM LIST TO SCROLL AREA)
        pages_group = QGroupBox("Pages")
        pages_layout = QVBoxLayout()

        # Create scroll area with grid widget
        self.pages_scroll = QScrollArea()
        self.pages_widget = QWidget()
        from PySide6.QtWidgets import QGridLayout
        self.pages_grid = QGridLayout(self.pages_widget)
        self.pages_scroll.setWidget(self.pages_widget)
        self.pages_scroll.setWidgetResizable(True)

        pages_layout.addWidget(self.pages_scroll)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        self.setLayout(layout)

    def load_pages(self, pages: List[PDFPageData]):
        """Load pages into the list"""
        self.clear_pages()

        for page_data in pages:
            self.add_page(page_data)

        self.update_count_label()

    def add_page(self, page_data: PDFPageData):
        """Add a single page to the grid"""
        page_item_widget = PageListItem(page_data)
        page_item_widget.selection_changed.connect(self.on_selection_changed)

        # Calculate grid position (4 columns)
        row = len(self.page_items) // 4
        col = len(self.page_items) % 4

        self.pages_grid.addWidget(page_item_widget, row, col)
        self.page_items.append(page_item_widget)

    def clear_pages(self):
        """Clear all pages from the list"""
        self.pages_list.clear()
        self.page_items.clear()
        self.update_count_label()

    def select_all(self):
        """Select all visible pages"""
        for item in self.page_items:
            if not item.isHidden():
                item.set_selected(True)

    def clear_all(self):
        """Clear all selections"""
        for item in self.page_items:
            item.set_selected(False)

    def invert_selection(self):
        """Invert current selection"""
        for item in self.page_items:
            if not item.isHidden():
                item.set_selected(not item.is_selected())

    def get_selected_pages(self) -> List[PDFPageData]:
        """Get list of selected page data"""
        return [item.page_data for item in self.page_items if item.is_selected()]

    def assign_profile_to_selected(self, profile_name: str):
        """Assign a profile to all selected pages"""
        selected_count = 0
        for item in self.page_items:
            if item.is_selected():
                item.assign_profile(profile_name)
                selected_count += 1

        return selected_count

    def apply_filter(self, filter_text: str):
        """Filter pages based on search text"""
        filter_text = filter_text.lower().strip()

        for i, item in enumerate(self.page_items):
            if not filter_text:
                # Show all if no filter
                item.show()
                self.pages_list.item(i).setHidden(False)
            else:
                # Check if filter matches filename or page number
                page_data = item.page_data
                filename = page_data.source_filename.lower()
                page_num = str(page_data.page_number + 1)

                matches = (filter_text in filename or
                           filter_text in page_num or
                           (page_data.assigned_profile and
                            filter_text in page_data.assigned_profile.lower()))

                item.setVisible(matches)
                self.pages_list.item(i).setHidden(not matches)

        self.update_count_label()

    def on_selection_changed(self):
        """Handle selection change from individual items"""
        self.update_count_label()
        self.selection_changed.emit()

    def update_count_label(self):
        """Update the selection count label"""
        total_visible = sum(1 for item in self.page_items if not item.isHidden())
        selected_visible = sum(1 for item in self.page_items
                               if not item.isHidden() and item.is_selected())

        self.count_label.setText(f"{selected_visible} of {total_visible} pages selected")

    def get_all_pages(self) -> List[PDFPageData]:
        """Get all page data"""
        return [item.page_data for item in self.page_items]