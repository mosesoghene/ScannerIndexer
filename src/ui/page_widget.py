from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                               QCheckBox, QLabel, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from models.pdf_page import PDFPageData
from services.pdf_service import PDFService


class PageWidget(QWidget):
    """Widget for displaying and editing a single PDF page"""

    data_changed = Signal()  # Emitted when page data changes

    def __init__(self, page_data: PDFPageData):
        super().__init__()
        self.page_data = page_data
        self.setup_ui()
        self.load_thumbnail()
        self.connect_signals()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Selection checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.page_data.selected)
        layout.addWidget(self.checkbox)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 150)
        self.thumbnail_label.setStyleSheet("border: 1px solid gray;")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumbnail_label)

        # Page info and metadata inputs
        info_layout = QVBoxLayout()

        # Page info
        info_layout.addWidget(QLabel(self.page_data.display_name))

        # Metadata inputs
        info_layout.addWidget(QLabel("Output Folder:"))
        self.folder_input = QLineEdit(self.page_data.folder_name)
        self.folder_input.setPlaceholderText("e.g., contracts, invoices")
        info_layout.addWidget(self.folder_input)

        info_layout.addWidget(QLabel("Output Filename:"))
        self.filename_input = QLineEdit(self.page_data.filename)
        self.filename_input.setPlaceholderText("filename (without .pdf)")
        info_layout.addWidget(self.filename_input)

        info_layout.addWidget(QLabel("Custom Tag:"))
        self.tag_input = QLineEdit(self.page_data.custom_tag)
        self.tag_input.setPlaceholderText("Optional tag/category")
        info_layout.addWidget(self.tag_input)

        layout.addLayout(info_layout)
        layout.addStretch()

        self.setLayout(layout)

    def load_thumbnail(self):
        """Load and display the page thumbnail"""
        img_data = PDFService.get_page_thumbnail(
            self.page_data.source_path,
            self.page_data.page_number
        )

        if img_data:
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            pixmap = pixmap.scaled(120, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        else:
            self.thumbnail_label.setText(f"Page {self.page_data.page_number + 1}")

    def connect_signals(self):
        """Connect UI signals to update the data model"""
        self.checkbox.toggled.connect(self.update_data)
        self.folder_input.textChanged.connect(self.update_data)
        self.filename_input.textChanged.connect(self.update_data)
        self.tag_input.textChanged.connect(self.update_data)

    def update_data(self):
        """Update the underlying data model with current UI values"""
        self.page_data.selected = self.checkbox.isChecked()
        self.page_data.folder_name = self.folder_input.text()
        self.page_data.filename = self.filename_input.text()
        self.page_data.custom_tag = self.tag_input.text()

        self.data_changed.emit()

    def set_selected(self, selected: bool):
        """Programmatically set the selection state"""
        self.checkbox.setChecked(selected)

    def is_selected(self) -> bool:
        """Check if this page is selected for export"""
        return self.checkbox.isChecked()

    def get_page_data(self) -> PDFPageData:
        """Get the current page data"""
        self.update_data()  # Ensure data is current
        return self.page_data
