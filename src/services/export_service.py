import os
from pathlib import Path
from typing import List
import fitz  # PyMuPDF

from models.pdf_page import ExportJob


class ExportService:
    """Handles PDF page extraction and export operations"""

    @staticmethod
    def export_page(job: ExportJob) -> bool:
        """Export a single page to a new PDF file"""
        try:
            # Create output directory if it doesn't exist
            output_path = Path(job.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Open source PDF
            doc = fitz.open(job.source_path)

            # Create new document with just the target page
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=job.page_number, to_page=job.page_number)

            # Save the new document
            new_doc.save(job.output_path)

            # Clean up
            new_doc.close()
            doc.close()

            return True

        except Exception as e:
            print(f"Error exporting page {job.page_number} from {job.source_path}: {e}")
            return False

    @staticmethod
    def export_pages_batch(jobs: List[ExportJob]) -> List[dict]:
        """Export multiple pages and return results"""
        results = []

        for job in jobs:
            success = ExportService.export_page(job)

            result = {
                'job': job,
                'success': success,
                'output_file': Path(job.output_path).name if success else None,
                'error': None if success else f"Failed to export {job.output_path}"
            }

            results.append(result)

        return results

    @staticmethod
    def validate_export_jobs(jobs: List[ExportJob]) -> List[str]:
        """Validate export jobs and return any error messages"""
        errors = []

        for i, job in enumerate(jobs):
            # Check if source file exists
            if not Path(job.source_path).exists():
                errors.append(f"Job {i + 1}: Source file not found: {job.source_path}")

            # Check if output directory can be created
            try:
                output_path = Path(job.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Job {i + 1}: Cannot create output directory: {e}")

            # Check if output file already exists (warning, not error)
            if Path(job.output_path).exists():
                # This is just a warning - we'll overwrite
                pass

        return errors

    @staticmethod
    def get_output_preview(jobs: List[ExportJob]) -> dict:
        """Get a preview of what will be exported"""
        if not jobs:
            return {'folders': {}, 'total_files': 0}

        folders = {}

        for job in jobs:
            output_path = Path(job.output_path)
            folder_name = output_path.parent.name
            file_name = output_path.name

            if folder_name not in folders:
                folders[folder_name] = []

            folders[folder_name].append(file_name)

        return {
            'folders': folders,
            'total_files': len(jobs)
        }