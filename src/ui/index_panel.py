from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QComboBox, QPushButton, QLabel, QLineEdit,
                               QTextEdit, QCheckBox, QScrollArea, QGroupBox,
                               QFormLayout, QMessageBox, QDialog, QDialogButtonBox,
                               QListWidget, QListWidgetItem, QSplitter, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from typing import List, Optional

from src.models.index_profile import IndexProfile, IndexField, ProfileManager


class FieldEditor(QWidget):
    """Widget for editing a single index field"""

    field_changed = Signal()

    def __init__(self, field: IndexField):
        super().__init__()
        self.field = field
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        # Field name label
        name_label = QLabel(self.field.name + ("*" if self.field.required else ""))
        name_label.setMinimumWidth(120)
        layout.addWidget(name_label)

        # Field input based on type
        if self.field.field_type == "dropdown":
            self.input = QComboBox()
            self.input.setEditable(True)
            self.input.addItems(self.field.options)
            self.input.setCurrentText(self.field.value)
            self.input.currentTextChanged.connect(self.on_value_changed)
        else:
            self.input = QLineEdit(self.field.value)
            self.input.setPlaceholderText(self.field.placeholder)
            self.input.textChanged.connect(self.on_value_changed)

        layout.addWidget(self.input)
        self.setLayout(layout)

    def on_value_changed(self, value: str):
        """Handle input value changes"""
        self.field.value = value
        self.field_changed.emit()

    def get_value(self) -> str:
        """Get current field value"""
        if isinstance(self.input, QComboBox):
            return self.input.currentText()
        return self.input.text()


class ProfileEditor(QDialog):
    """Dialog for creating/editing index profiles"""

    def __init__(self, profile: Optional[IndexProfile] = None, parent=None):
        super().__init__(parent)
        self.profile = profile.clone() if profile else IndexProfile("New Profile")
        self.field_editors = []
        self.setup_ui()
        self.set_window_icon()

    def set_window_icon(self):
        """Set the window icon"""
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    def setup_ui(self):
        self.setWindowTitle("Edit Index Profile")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()

        # Profile basic info
        info_group = QGroupBox("Profile Information")
        info_layout = QFormLayout()

        self.name_input = QLineEdit(self.profile.name)
        info_layout.addRow("Name:", self.name_input)

        self.description_input = QTextEdit(self.profile.description)
        self.description_input.setMaximumHeight(60)
        info_layout.addRow("Description:", self.description_input)

        self.pattern_input = QLineEdit(self.profile.output_pattern)
        self.pattern_input.setPlaceholderText("{field_name}/{another_field}")
        info_layout.addRow("Output Pattern:", self.pattern_input)

        # Input folder
        self.input_folder_input = QLineEdit(self.profile.input_folder)
        self.input_folder_btn = QPushButton("Browse...")
        self.input_folder_btn.clicked.connect(self.browse_input_folder)
        input_folder_layout = QHBoxLayout()
        input_folder_layout.addWidget(self.input_folder_input)
        input_folder_layout.addWidget(self.input_folder_btn)
        info_layout.addRow("Input Folder:", input_folder_layout)

        # Output folder
        self.output_folder_input = QLineEdit(self.profile.output_folder)
        self.output_folder_btn = QPushButton("Browse...")
        self.output_folder_btn.clicked.connect(self.browse_output_folder)
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_input)
        output_folder_layout.addWidget(self.output_folder_btn)
        info_layout.addRow("Output Folder:", output_folder_layout)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Fields section
        fields_group = QGroupBox("Index Fields")
        fields_layout = QVBoxLayout()

        # Add field button
        add_field_btn = QPushButton("Add Field")
        add_field_btn.clicked.connect(self.add_field)
        fields_layout.addWidget(add_field_btn)

        # Fields list
        self.fields_area = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_area.setWidget(self.fields_widget)
        self.fields_area.setWidgetResizable(True)
        fields_layout.addWidget(self.fields_area)

        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.refresh_fields()

    def browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_folder_input.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_input.setText(folder)

    def add_field(self):
        """Add a new field to the profile"""
        from PySide6.QtWidgets import QInputDialog
        field_name, ok = QInputDialog.getText(self, "Add Field", "Field name:")
        if ok and field_name.strip():
            new_field = IndexField(field_name.strip())
            self.profile.add_field(new_field)
            self.refresh_fields()

    def remove_field(self, field_name: str):
        """Remove a field from the profile"""
        self.profile.remove_field(field_name)
        self.refresh_fields()

    def refresh_fields(self):
        """Refresh the fields display"""
        # Clear existing widgets
        for i in reversed(range(self.fields_layout.count())):
            child = self.fields_layout.takeAt(i).widget()
            if child:
                child.deleteLater()

        # Add field widgets
        for field in self.profile.fields:
            field_widget = QWidget()
            field_layout = QHBoxLayout()

            # Field name
            name_input = QLineEdit(field.name)
            name_input.textChanged.connect(lambda text, f=field: setattr(f, 'name', text))
            field_layout.addWidget(QLabel("Name:"))
            field_layout.addWidget(name_input)

            # Field placeholder
            placeholder_input = QLineEdit(field.placeholder)
            placeholder_input.textChanged.connect(lambda text, f=field: setattr(f, 'placeholder', text))
            field_layout.addWidget(QLabel("Placeholder:"))
            field_layout.addWidget(placeholder_input)

            # Required checkbox
            required_cb = QCheckBox("Required")
            required_cb.setChecked(field.required)
            required_cb.toggled.connect(lambda checked, f=field: setattr(f, 'required', checked))
            field_layout.addWidget(required_cb)

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, name=field.name: self.remove_field(name))
            field_layout.addWidget(remove_btn)

            field_widget.setLayout(field_layout)
            self.fields_layout.addWidget(field_widget)

    def accept(self):
        """Handle dialog acceptance"""
        # Update profile info
        self.profile.name = self.name_input.text().strip()
        self.profile.description = self.description_input.toPlainText().strip()
        self.profile.output_pattern = self.pattern_input.text().strip()
        self.profile.input_folder = self.input_folder_input.text().strip()
        self.profile.output_folder = self.output_folder_input.text().strip()

        if not self.profile.name:
            QMessageBox.warning(self, "Invalid Input", "Profile name is required.")
            return

        super().accept()

    def get_profile(self) -> IndexProfile:
        """Get the edited profile"""
        return self.profile


class IndexPanel(QWidget):
    """Panel for managing index profiles and assigning them to pages"""

    profile_applied = Signal(str, IndexProfile)  # profile_name, profile
    batch_assignment_requested = Signal(str)  # profile_name
    profile_folders_changed = Signal(str, str)  # input_folder, output_folder for auto-loading

    def __init__(self):
        super().__init__()
        self.profile_manager = ProfileManager()
        self.current_profile: Optional[IndexProfile] = None
        self.field_editors: List[FieldEditor] = []
        self.setup_ui()
        self.refresh_profiles()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Profile management section
        profile_group = QGroupBox("Index Profiles")
        profile_layout = QVBoxLayout()

        # Profile selector and buttons
        selector_layout = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        selector_layout.addWidget(QLabel("Profile:"))
        selector_layout.addWidget(self.profile_combo)

        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_profile)
        selector_layout.addWidget(new_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_profile)
        selector_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_profile)
        selector_layout.addWidget(delete_btn)

        # Load from profile button
        load_btn = QPushButton("Load PDFs from Profile Input")
        load_btn.clicked.connect(self.load_from_profile_input)
        load_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        selector_layout.addWidget(load_btn)

        profile_layout.addLayout(selector_layout)

        # Profile description and folder info
        self.profile_description = QLabel("Select a profile to see description")
        self.profile_description.setWordWrap(True)
        self.profile_description.setStyleSheet("color: #666; font-style: italic;")
        profile_layout.addWidget(self.profile_description)

        # Folder info display
        self.folder_info = QLabel("")
        self.folder_info.setWordWrap(True)
        self.folder_info.setStyleSheet("background: #f0f0f0; padding: 4px; border-radius: 3px; font-size: 10px;")
        profile_layout.addWidget(self.folder_info)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        # Fields section
        fields_group = QGroupBox("Index Fields")
        fields_layout = QVBoxLayout()

        # Fields scroll area
        self.fields_scroll = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_scroll.setWidget(self.fields_widget)
        self.fields_scroll.setWidgetResizable(True)
        fields_layout.addWidget(self.fields_scroll)

        # Action buttons
        actions_layout = QHBoxLayout()

        apply_btn = QPushButton("Apply to Selected Pages")
        apply_btn.clicked.connect(self.apply_to_selected)
        actions_layout.addWidget(apply_btn)

        batch_btn = QPushButton("Batch Assign")
        batch_btn.clicked.connect(self.batch_assign)
        actions_layout.addWidget(batch_btn)

        fields_layout.addLayout(actions_layout)

        # Output preview
        self.output_preview = QLabel("Output: Not configured")
        self.output_preview.setStyleSheet("background: #f0f0f0; padding: 8px; border-radius: 4px;")
        fields_layout.addWidget(self.output_preview)

        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)

        self.setLayout(layout)

    def refresh_profiles(self):
        """Refresh the profiles dropdown"""
        current_text = self.profile_combo.currentText()
        self.profile_combo.clear()

        profile_names = [p.name for p in self.profile_manager.profiles]
        self.profile_combo.addItems(profile_names)

        # Restore selection if possible
        if current_text in profile_names:
            self.profile_combo.setCurrentText(current_text)
        elif profile_names:
            self.profile_combo.setCurrentIndex(0)

    def on_profile_selected(self, profile_name: str):
        """Handle profile selection"""
        self.current_profile = self.profile_manager.get_profile(profile_name)

        if self.current_profile:
            self.profile_description.setText(
                self.current_profile.description or "No description available"
            )

            # Show folder information
            folder_info_parts = []
            if self.current_profile.input_folder:
                folder_info_parts.append(f"Input: {self.current_profile.input_folder}")
            if self.current_profile.output_folder:
                folder_info_parts.append(f"Output: {self.current_profile.output_folder}")

            if folder_info_parts:
                self.folder_info.setText(" | ".join(folder_info_parts))
            else:
                self.folder_info.setText("No folders configured")

            self.setup_field_editors()
        else:
            self.profile_description.setText("Select a profile to see description")
            self.folder_info.setText("")
            self.clear_field_editors()

    def load_from_profile_input(self):
        """Load PDFs from the current profile's input folder"""
        if not self.current_profile:
            QMessageBox.information(self, "No Profile", "Please select a profile first.")
            return

        if not self.current_profile.input_folder:
            QMessageBox.information(self, "No Input Folder",
                                    "Please set an input folder in the profile first (Edit button).")
            return

        # Emit signal to main window to load PDFs
        self.profile_folders_changed.emit(self.current_profile.input_folder,
                                          self.current_profile.output_folder or "")

    def setup_field_editors(self):
        """Setup field editors for current profile"""
        self.clear_field_editors()

        if not self.current_profile:
            return

        for field in self.current_profile.fields:
            editor = FieldEditor(field)
            editor.field_changed.connect(self.update_output_preview)
            editor.field_changed.connect(self.auto_save_profile)  # Auto-save on changes
            self.field_editors.append(editor)
            self.fields_layout.addWidget(editor)

        self.update_output_preview()

    def clear_field_editors(self):
        """Clear all field editors"""
        for editor in self.field_editors:
            editor.deleteLater()
        self.field_editors.clear()

        # Clear the layout
        for i in reversed(range(self.fields_layout.count())):
            child = self.fields_layout.takeAt(i).widget()
            if child:
                child.deleteLater()

    def update_output_preview(self):
        """Update the output path preview"""
        if not self.current_profile:
            self.output_preview.setText("Output: No profile selected")
            return

        try:
            # Use profile's output folder if set, otherwise show generic path
            base_path = self.current_profile.output_folder or "/output"
            output_path = self.current_profile.generate_output_path(base_path)
            relative_path = output_path.replace(base_path + "/", "")
            self.output_preview.setText(f"Output: {relative_path}")
        except Exception:
            self.output_preview.setText("Output: Invalid pattern or missing fields")

    def auto_save_profile(self):
        """Auto-save the current profile when fields change"""
        if self.current_profile:
            self.profile_manager.save_profiles()

    def new_profile(self):
        """Create a new profile"""
        dialog = ProfileEditor()
        if dialog.exec() == QDialog.Accepted:
            new_profile = dialog.get_profile()
            self.profile_manager.add_profile(new_profile)
            self.refresh_profiles()
            self.profile_combo.setCurrentText(new_profile.name)

    def edit_profile(self):
        """Edit the current profile"""
        if not self.current_profile:
            QMessageBox.information(self, "No Profile", "Please select a profile to edit.")
            return

        dialog = ProfileEditor(self.current_profile)
        if dialog.exec() == QDialog.Accepted:
            edited_profile = dialog.get_profile()

            # Replace in manager
            for i, profile in enumerate(self.profile_manager.profiles):
                if profile.name == self.current_profile.name:
                    self.profile_manager.profiles[i] = edited_profile
                    break

            self.profile_manager.save_profiles()
            self.refresh_profiles()
            self.profile_combo.setCurrentText(edited_profile.name)

    def delete_profile(self):
        """Delete the current profile"""
        if not self.current_profile:
            QMessageBox.information(self, "No Profile", "Please select a profile to delete.")
            return

        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Are you sure you want to delete '{self.current_profile.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.profile_manager.remove_profile(self.current_profile.name)
            self.refresh_profiles()

    def apply_to_selected(self):
        """Apply current profile to selected pages"""
        if not self.current_profile:
            QMessageBox.information(self, "No Profile", "Please select a profile first.")
            return

        # Validate fields
        valid, errors = self.current_profile.validate_all_fields()
        if not valid:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        self.profile_applied.emit(self.current_profile.name, self.current_profile)

    def batch_assign(self):
        """Request batch assignment of current profile"""
        if not self.current_profile:
            QMessageBox.information(self, "No Profile", "Please select a profile first.")
            return

        self.batch_assignment_requested.emit(self.current_profile.name)

    def get_current_profile(self) -> Optional[IndexProfile]:
        """Get the currently selected profile"""
        return self.current_profile