from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QPushButton, QLabel, QTextEdit,
                               QFileDialog, QMessageBox, QSplitter,
                               QGroupBox)
from PySide6.QtCore import Qt
from typing import List

from src.models.pdf_page import PDFPageData, ExportJob
from src.models.index_profile import IndexProfile
from src.ui.page_list_widget import PageListWidget
from src.ui.index_panel import IndexPanel
from src.ui.workers import PDFLoader, PDFExporter
from src.utils.file_utils import FileUtils


class PDFExtractorApp(QMainWindow):
    """Main application window with split-panel interface"""

    def __init__(self):
        super().__init__()
        self.output_folder = None
        self.setup_ui()
        self.auto_load_from_profiles()

    def setup_ui(self):
        self.setWindowTitle("PDF Page Extractor - Index & Extract")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.browse_btn = QPushButton("Browse PDF Folder")
        self.browse_btn.clicked.connect(self.browse_folder)
        toolbar_layout.addWidget(self.browse_btn)

        # ADD MISSING OUTPUT FOLDER BUTTON
        self.output_btn = QPushButton("Set Output Folder")
        self.output_btn.clicked.connect(self.set_output_folder)
        toolbar_layout.addWidget(self.output_btn)

        self.output_label = QLabel("Output: Not set")
        toolbar_layout.addWidget(self.output_label)

        toolbar_layout.addStretch()

        self.export_btn = QPushButton("Export All Assigned Pages")
        self.export_btn.clicked.connect(self.export_all_assigned)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        toolbar_layout.addWidget(self.export_btn)

        main_layout.addLayout(toolbar_layout)

        # Main content splitter
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Page list
        self.page_list = PageListWidget()
        self.page_list.selection_changed.connect(self.on_page_selection_changed)
        self.main_splitter.addWidget(self.page_list)

        # Right panel - Index assignment
        self.index_panel = IndexPanel()
        self.index_panel.profile_applied.connect(self.apply_profile_to_selected)
        self.index_panel.batch_assignment_requested.connect(self.batch_assign_profile)
        self.index_panel.profile_folders_changed.connect(self.load_from_profile_folders)
        self.main_splitter.addWidget(self.index_panel)

        # Set initial splitter sizes (60% left, 40% right)
        self.main_splitter.setSizes([800, 600])

        main_layout.addWidget(self.main_splitter)

        # Bottom status area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        status_layout.addWidget(self.status_text)

        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        central_widget.setLayout(main_layout)

        # Initialize with welcome message
        self.status_text.append("Welcome to PDF Page Extractor!")
        self.status_text.append("1. Browse for PDF folder to load pages")
        self.status_text.append("2. Select pages on the left")
        self.status_text.append("3. Configure index profile on the right")
        self.status_text.append("4. Apply profile to selected pages")
        self.status_text.append("5. Set output folder and export")

    def load_from_profile_folders(self, input_folder: str, output_folder: str):
        """Load PDFs from profile input folder and set output folder"""
        if input_folder:
            self.status_text.append(f"Loading PDFs from profile input folder: {input_folder}")
            self.load_pdfs(input_folder)

        if output_folder:
            self.output_folder = output_folder
            self.output_label.setText(f"Output: {output_folder}")
            self.update_export_button_state()

    def auto_load_from_profiles(self):
        """Auto-load PDFs from profile input folders if available"""
        profile_manager = self.index_panel.profile_manager

        # Check if any profile has an input folder set
        for profile in profile_manager.profiles:
            if profile.input_folder and profile.input_folder.strip():
                self.status_text.append(f"Auto-loading from profile '{profile.name}' input folder...")
                self.load_pdfs(profile.input_folder)
                break

    def browse_folder(self):
        """Open folder dialog and load PDFs"""
        folder = QFileDialog.getExistingDirectory(self, "Select PDF Folder")
        if folder:
            self.load_pdfs(folder)

    def set_output_folder(self):
        """Set the output folder for exports"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_label.setText(f"Output: {folder}")
            self.update_export_button_state()

    def load_pdfs(self, folder_path: str):
        """Load PDFs from folder in background thread"""
        self.page_list.clear_pages()
        self.status_text.clear()
        self.status_text.append("Loading PDFs from folder...")
        self.status_text.append(f"Scanning: {folder_path}")

        # Disable buttons during loading
        self.set_buttons_enabled(False)

        # Start loading thread
        self.loader = PDFLoader(folder_path)
        self.loader.progress.connect(self.status_text.append)
        self.loader.pages_loaded.connect(self.on_pages_loaded)
        self.loader.error.connect(self.on_load_error)
        self.loader.finished.connect(lambda: self.set_buttons_enabled(True))
        self.loader.start()

    def on_pages_loaded(self, pages: List[PDFPageData]):
        """Handle successful page loading"""
        self.page_list.load_pages(pages)
        self.status_text.append(f"✓ Loaded {len(pages)} pages successfully!")
        self.status_text.append("Select pages and assign index profiles to continue.")

        self.update_export_button_state()

    def on_load_error(self, error_message: str):
        """Handle loading errors"""
        self.status_text.append(f"❌ Error: {error_message}")
        QMessageBox.warning(self, "Loading Error", error_message)

    def on_page_selection_changed(self):
        """Handle page selection changes"""
        self.update_export_button_state()

    def apply_profile_to_selected(self, profile_name: str, profile: IndexProfile):
        """Apply index profile to selected pages"""
        selected_pages = self.page_list.get_selected_pages()

        if not selected_pages:
            QMessageBox.information(self, "No Selection", "Please select some pages first.")
            return

        # Assign profile to selected pages
        count = self.page_list.assign_profile_to_selected(profile_name)

        self.status_text.append(f"✓ Applied profile '{profile_name}' to {count} pages")
        self.update_export_button_state()

    def batch_assign_profile(self, profile_name: str):
        """Show batch assignment dialog for profile"""
        # For now, just apply to all selected pages
        self.apply_profile_to_selected(profile_name, self.index_panel.get_current_profile())

    def export_all_assigned(self):
        """Export all pages that have assigned profiles"""
        # Get all pages with assigned profiles
        all_pages = self.page_list.get_all_pages()
        pages_to_export = [p for p in all_pages if p.assigned_profile]

        if not pages_to_export:
            QMessageBox.information(self, "No Assigned Pages",
                                    "No pages have been assigned index profiles yet.")
            return

        # Create export jobs using assigned profiles
        export_jobs = []
        profile_manager = self.index_panel.profile_manager

        for page_data in pages_to_export:
            profile = profile_manager.get_profile(page_data.assigned_profile)
            if profile:
                # Use profile's output folder if set, otherwise use app's output folder
                output_base = profile.output_folder or self.output_folder

                if not output_base:
                    QMessageBox.warning(self, "No Output Folder",
                                        "Please set an output folder in the profile or use 'Set Output Folder' button.")
                    return

                # Generate output path using profile
                output_path = profile.generate_output_path(output_base)

                # Sanitize the filename
                sanitized_filename = FileUtils.sanitize_filename(
                    f"{output_path}_page_{page_data.page_number + 1}"
                )

                if not sanitized_filename.endswith('.pdf'):
                    sanitized_filename += '.pdf'

                # Ensure unique filename
                final_output_path = FileUtils.ensure_unique_filename(sanitized_filename)

                job = ExportJob(
                    source_path=page_data.source_path,
                    page_number=page_data.page_number,
                    output_path=final_output_path
                )
                export_jobs.append(job)

        if not export_jobs:
            QMessageBox.information(self, "No Valid Jobs",
                                    "No valid export jobs could be created.")
            return

        # Start export
        self.status_text.append(f"Starting export of {len(export_jobs)} pages...")
        self.set_buttons_enabled(False)

        self.exporter = PDFExporter(export_jobs)
        self.exporter.progress.connect(self.status_text.append)
        self.exporter.export_complete.connect(self.on_export_complete)
        self.exporter.error.connect(self.on_export_error)
        self.exporter.finished.connect(lambda: self.set_buttons_enabled(True))
        self.exporter.start()

    def on_export_complete(self, results):
        """Handle successful export completion"""
        successful = sum(1 for r in results if r['success'])
        total = len(results)

        self.status_text.append(f"--- Export Complete: {successful}/{total} successful ---")

        if successful == total:
            QMessageBox.information(self, "Export Complete",
                                    f"Successfully exported all {total} pages!")
        else:
            QMessageBox.warning(self, "Export Partial",
                                f"Exported {successful} of {total} pages. Check status for details.")

    def on_export_error(self, error_message: str):
        """Handle export errors"""
        self.status_text.append(f"❌ Export Error: {error_message}")
        QMessageBox.critical(self, "Export Error", error_message)

    def update_export_button_state(self):
        """Enable/disable export button based on current state"""
        has_assigned_pages = any(p.assigned_profile for p in self.page_list.get_all_pages())

        # Check if assigned profiles have output folders OR app has output folder
        all_pages = self.page_list.get_all_pages()
        profile_manager = self.index_panel.profile_manager
        has_valid_outputs = bool(self.output_folder)  # App has output folder

        if not has_valid_outputs:
            # Check if assigned profiles have output folders
            for page in all_pages:
                if page.assigned_profile:
                    profile = profile_manager.get_profile(page.assigned_profile)
                    if profile and profile.output_folder:
                        has_valid_outputs = True
                        break

        self.export_btn.setEnabled(has_assigned_pages and has_valid_outputs)

        if has_assigned_pages:
            assigned_count = sum(1 for p in all_pages if p.assigned_profile)
            self.export_btn.setText(f"Export {assigned_count} Assigned Pages")
        else:
            self.export_btn.setText("Export All Assigned Pages")

    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable all buttons during processing"""
        self.browse_btn.setEnabled(enabled)
        self.output_btn.setEnabled(enabled)

        # Export button has additional conditions
        if enabled:
            self.update_export_button_state()
        else:
            self.export_btn.setEnabled(False)