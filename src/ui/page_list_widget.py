from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QListWidget, QListWidgetItem, QPushButton,
                               QLabel, QCheckBox, QLineEdit, QGroupBox,
                               QScrollArea, QGridLayout)
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
        layout.setContentsMargins(4, 4, 4, 4)

        # Selection checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.page_data.selected)
        self.checkbox.toggled.connect(self.on_selection_changed)
        layout.addWidget(self.checkbox)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(80, 100)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumbnail_label)

        # Page info
        info_label = QLabel(f"Pg {self.page_data.page_number + 1}")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(info_label)

        # Source filename (truncated)
        filename = self.page_data.source_filename
        if len(filename) > 15:
            filename = filename[:12] + "..."
        filename_label = QLabel(filename)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet("font-size: 9px; color: #666;")
        layout.addWidget(filename_label)

        # Profile assignment status
        self.profile_label = QLabel("No profile assigned")
        self.profile_label.setAlignment(Qt.AlignCenter)
        self.profile_label.setWordWrap(True)
        layout.addWidget(self.profile_label)
        self.update_profile_label()

        self.setLayout(layout)
        self.setFixedSize(100, 180)

        # Set initial styling
        self.update_selection_style()

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
            pixmap = pixmap.scaled(78, 98, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText(f"{self.page_data.page_number + 1}")

    def on_selection_changed(self, checked: bool):
        """Handle selection state change"""
        self.page_data.selected = checked
        self.update_selection_style()
        self.selection_changed.emit(checked)

    def update_selection_style(self):
        """Update widget styling based on selection and assignment state"""
        if self.page_data.assigned_profile:
            # Green for assigned
            self.setStyleSheet("""
                PageListItem {
                    background-color: #e8f5e8;
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                }
            """)
        elif self.checkbox.isChecked():
            # Blue for selected
            self.setStyleSheet("""
                PageListItem {
                    background-color: #e3f2fd;
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
            """)
        else:
            # Default styling
            self.setStyleSheet("""
                PageListItem {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            """)

    def set_selected(self, selected: bool):
        """Programmatically set selection"""
        self.checkbox.setChecked(selected)
        self.update_selection_style()

    def assign_profile(self, profile_name: str):
        """Assign a profile to this page"""
        self.page_data.assigned_profile = profile_name
        self.update_profile_label()
        self.set_assigned_state(True)
        self.update_selection_style()

    def set_assigned_state(self, assigned: bool):
        """Set the assigned state and disable selection if assigned"""
        if assigned:
            self.checkbox.setEnabled(False)
            self.checkbox.setChecked(False)
            self.update_selection_style()
        else:
            self.checkbox.setEnabled(True)
            self.update_selection_style()

    def update_selection_style(self):
        """Update widget styling based on selection and assignment state"""
        if self.page_data.assigned_profile:
            # Green for assigned
            self.setStyleSheet("""
                PageListItem {
                    background-color: #e8f5e8;
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                }
            """)
        elif self.checkbox.isChecked():
            # Blue for selected
            self.setStyleSheet("""
                PageListItem {
                    background-color: #e3f2fd;
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
            """)
        else:
            # Default styling
            self.setStyleSheet("""
                PageListItem {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            """)

    def set_selected(self, selected: bool):
        """Programmatically set selection"""
        self.checkbox.setChecked(selected)
        self.update_selection_style()

    def assign_profile(self, profile_name: str):
        """Assign a profile to this page"""
        self.page_data.assigned_profile = profile_name
        self.update_profile_label()
        self.set_assigned_state(True)
        self.update_selection_style()

    def set_assigned_state(self, assigned: bool):
        """Set the assigned state and disable selection if assigned"""
        if assigned:
            self.checkbox.setEnabled(False)
            self.checkbox.setChecked(False)
            self.update_selection_style()
        else:
            self.checkbox.setEnabled(True)
            self.update_selection_style()

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
            self.profile_label.setText(f"✓ {self.page_data.assigned_profile}")
            self.profile_label.setStyleSheet("color: #2196F3; font-size: 9px; font-weight: bold;")
        else:
            self.profile_label.setText("No profile assigned")
            self.profile_label.setStyleSheet("color: #999; font-size: 9px;")

    def set_assigned_state(self, assigned: bool):
        """Set the assigned state and disable selection if assigned"""
        if assigned:
            self.checkbox.setEnabled(False)
            self.checkbox.setChecked(False)
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                    background-color: #f8fff8;
                }
            """)
        else:
            self.checkbox.setEnabled(True)
            self.setStyleSheet("""
                QWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
                QWidget:hover {
                    border-color: #2196F3;
                }
            """)


class PageListWidget(QWidget):
    """Widget for displaying pages in a grid format with bulk selection"""

    selection_changed = Signal()  # Emitted when selection changes

    def __init__(self):
        super().__init__()
        self.page_items: List[PageListItem] = []
        self.setup_ui()

    def get_page_item_by_data(self, page_data: PDFPageData) -> 'PageListItem':
        """Get the PageListItem widget for given page data"""
        for item in self.page_items:
            if item.page_data == page_data:
                return item
        return None

    def setup_ui(self):
        layout = QVBoxLayout()

        # Selection controls
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

        # Pages grid
        pages_group = QGroupBox("Pages")
        pages_layout = QVBoxLayout()

        # Create scroll area with grid widget
        self.pages_scroll = QScrollArea()
        self.pages_widget = QWidget()
        self.pages_grid = QGridLayout(self.pages_widget)
        self.pages_grid.setSpacing(5)  # Add some spacing between items

        self.pages_scroll.setWidget(self.pages_widget)
        self.pages_scroll.setWidgetResizable(True)

        pages_layout.addWidget(self.pages_scroll)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        self.setLayout(layout)

    def load_pages(self, pages: List[PDFPageData]):
        """Load pages into the grid"""
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
        """Clear all pages from the grid"""
        # Clear the grid layout
        for i in reversed(range(self.pages_grid.count())):
            child = self.pages_grid.takeAt(i).widget()
            if child:
                child.deleteLater()

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
        processed_sources = set()  # Track which sources we've already processed

        for item in self.page_items:
            if item.is_selected():
                item.assign_profile(profile_name)
                selected_count += 1

                # Only mark source as processed once, and only if ALL pages from
                # that source have been assigned profiles
                source_path = item.page_data.source_path
                if source_path not in processed_sources:
                    processed_sources.add(source_path)
                    # Check if all pages from this source now have profiles assigned
                    all_assigned = all(
                        page_item.page_data.assigned_profile is not None
                        for page_item in self.page_items
                        if page_item.page_data.source_path == source_path
                    )
                    if all_assigned:
                        self.mark_source_as_processed(source_path)

        return selected_count

    def mark_source_as_processed(self, source_path: str):
        """Mark source PDF as processed by adding 'done-' prefix"""
        from pathlib import Path
        import os

        path = Path(source_path)
        if not path.name.startswith("done-"):
            new_name = f"done-{path.name}"
            new_path = path.parent / new_name
            try:
                os.rename(str(path), str(new_path))
                # Update all page items with this source path
                for item in self.page_items:
                    if item.page_data.source_path == source_path:
                        item.page_data.source_path = str(new_path)
            except OSError:
                pass  # Handle file in use or permission errors silently

    def apply_filter(self, filter_text: str):
        """Filter pages based on search text"""
        filter_text = filter_text.lower().strip()

        for item in self.page_items:
            if not filter_text:
                # Show all if no filter
                item.show()
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