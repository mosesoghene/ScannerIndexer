from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF

from models.pdf_page import PDFPageData


class PDFService:
    """Handles PDF file operations and page extraction"""

    @staticmethod
    def find_pdf_files(folder_path: str) -> List[Path]:
        """Find all PDF files in a folder"""
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return []

        return list(folder.glob("*.pdf"))

    @staticmethod
    def load_pages_from_folder(folder_path: str) -> List[PDFPageData]:
        """Load all pages from all PDFs in a folder"""
        pdf_files = PDFService.find_pdf_files(folder_path)
        pages = []

        for pdf_file in pdf_files:
            try:
                file_pages = PDFService.load_pages_from_file(str(pdf_file))
                pages.extend(file_pages)
            except Exception as e:
                print(f"Error loading {pdf_file}: {e}")
                continue

        return pages

    @staticmethod
    def load_pages_from_file(pdf_path: str) -> List[PDFPageData]:
        """Load all pages from a single PDF file"""
        pages = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(doc.page_count):
                page_data = PDFPageData(
                    source_path=pdf_path,
                    page_number=page_num
                )
                pages.append(page_data)

            doc.close()

        except Exception as e:
            print(f"Error loading pages from {pdf_path}: {e}")
            return []

        return pages

    @staticmethod
    def get_page_thumbnail(pdf_path: str, page_number: int, scale: float = 0.3) -> Optional[bytes]:
        """Generate a thumbnail image for a specific page"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_number]

            # Generate thumbnail
            matrix = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=matrix)
            img_data = pix.tobytes("png")

            doc.close()
            return img_data

        except Exception as e:
            print(f"Error generating thumbnail for {pdf_path} page {page_number}: {e}")
            return None

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """Get the number of pages in a PDF"""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception:
            return 0

    @staticmethod
    def validate_pdf_file(pdf_path: str) -> bool:
        """Check if a file is a valid PDF"""
        try:
            doc = fitz.open(pdf_path)
            doc.close()
            return True
        except Exception:
            return False