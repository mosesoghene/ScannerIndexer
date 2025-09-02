from PySide6.QtCore import QThread, Signal
from typing import List

from src.models.pdf_page import PDFPageData, ExportJob
from src.services.pdf_service import PDFService
from src.services.export_service import ExportService


class PDFLoader(QThread):
    """Background thread for loading PDF files and pages"""

    progress = Signal(str)  # Progress message
    pages_loaded = Signal(list)  # List of PDFPageData
    finished = Signal()
    error = Signal(str)

    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
        self._stop_requested = False

    def stop(self):
        """Request thread to stop"""
        self._stop_requested = True

    def run(self):
        try:
            if self._stop_requested:
                return

            self.progress.emit(f"Scanning folder: {self.folder_path}")

            # Find PDF files
            pdf_files = PDFService.find_pdf_files(self.folder_path)

            if not pdf_files:
                self.error.emit("No PDF files found in the selected folder.")
                return

            if self._stop_requested:
                return

            self.progress.emit(f"Found {len(pdf_files)} PDF files. Loading pages...")

            # Load pages from all PDFs
            all_pages = []

            for i, pdf_file in enumerate(pdf_files):
                if self._stop_requested:
                    return

                self.progress.emit(f"Processing {pdf_file.name} ({i + 1}/{len(pdf_files)})")

                try:
                    pages = PDFService.load_pages_from_file(str(pdf_file))
                    all_pages.extend(pages)
                    self.progress.emit(f"  Loaded {len(pages)} pages from {pdf_file.name}")
                except Exception as e:
                    self.progress.emit(f"  Error loading {pdf_file.name}: {str(e)}")
                    continue

            if self._stop_requested:
                return

            if all_pages:
                self.progress.emit(f"Successfully loaded {len(all_pages)} pages total.")
                self.pages_loaded.emit(all_pages)
            else:
                self.error.emit("No valid pages found in PDF files.")

        except Exception as e:
            if not self._stop_requested:
                self.error.emit(f"Error loading PDFs: {str(e)}")
        finally:
            self.finished.emit()


class PDFExporter(QThread):
    """Background thread for exporting PDF pages"""

    progress = Signal(str)  # Progress message
    export_complete = Signal(list)  # Export results
    finished = Signal()
    error = Signal(str)

    def __init__(self, export_jobs: List[ExportJob]):
        super().__init__()
        self.export_jobs = export_jobs
        self._stop_requested = False

    def stop(self):
        """Request thread to stop"""
        self._stop_requested = True

    def run(self):
        try:
            if self._stop_requested:
                return

            self.progress.emit(f"Starting export of {len(self.export_jobs)} pages...")

            # Validate jobs first
            errors = ExportService.validate_export_jobs(self.export_jobs)
            if errors:
                self.error.emit("Export validation failed:\n" + "\n".join(errors))
                return

            if self._stop_requested:
                return

            # Show preview
            preview = ExportService.get_output_preview(self.export_jobs)
            self.progress.emit(f"Will create {preview['total_files']} files in {len(preview['folders'])} folders")

            # Export pages
            results = []

            for i, job in enumerate(self.export_jobs):
                if self._stop_requested:
                    return

                self.progress.emit(f"Exporting page {i + 1}/{len(self.export_jobs)}: {job.output_path}")

                success = ExportService.export_page(job)

                result = {
                    'job': job,
                    'success': success,
                    'message': f"✓ Exported: {job.output_path}" if success else f"✗ Failed: {job.output_path}"
                }

                results.append(result)
                self.progress.emit(result['message'])

            if self._stop_requested:
                return

            # Summary
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful

            self.progress.emit(f"\n=== Export Summary ===")
            self.progress.emit(f"✓ Successful: {successful}")
            self.progress.emit(f"✗ Failed: {failed}")
            self.progress.emit(f"Total: {len(results)}")

            self.export_complete.emit(results)

        except Exception as e:
            if not self._stop_requested:
                self.error.emit(f"Export error: {str(e)}")
        finally:
            self.finished.emit()