from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PDFPageData:
    """Represents a single PDF page with metadata"""
    source_path: str
    page_number: int
    folder_name: str = ""
    filename: str = ""
    custom_tag: str = ""
    selected: bool = False
    assigned_profile: Optional[str] = None  # Name of assigned index profile
    batch_id: Optional[str] = None  # For grouping pages into single files
    profile_field_values: dict = field(default_factory=dict)  # Store individual field values

    @property
    def source_filename(self) -> str:
        """Get the source PDF filename"""
        return Path(self.source_path).name

    @property
    def display_name(self) -> str:
        """Get display name for this page"""
        return f"Page {self.page_number + 1} - {self.source_filename}"

    def get_output_path(self, base_output_dir: str) -> Optional[str]:
        """Generate the full output path for this page"""
        if not self.selected:
            return None

        # Default values if not set
        folder = self.folder_name.strip() or "extracted"
        filename = self.filename.strip() or f"page_{self.page_number + 1}"

        # Add custom tag to folder if provided
        if self.custom_tag.strip():
            folder = f"{folder}_{self.custom_tag.strip()}"

        output_path = Path(base_output_dir) / folder / f"{filename}.pdf"
        return str(output_path)

    def validate_export_data(self) -> bool:
        """Check if this page has valid data for export"""
        if not self.selected:
            return False

        # Basic validation - could be expanded
        return Path(self.source_path).exists()


@dataclass
class ExportJob:
    """Represents an export job for a single page"""
    source_path: str
    page_number: int
    output_path: str

    @classmethod
    def from_pdf_page(cls, pdf_page: PDFPageData, base_output_dir: str) -> Optional['ExportJob']:
        """Create an ExportJob from a PDFPageData"""
        output_path = pdf_page.get_output_path(base_output_dir)
        if not output_path:
            return None

        return cls(
            source_path=pdf_page.source_path,
            page_number=pdf_page.page_number,
            output_path=output_path
        )