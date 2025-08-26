import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PySide6.QtWidgets import QApplication
from src.ui import PDFExtractorApp


def main():
    app = QApplication(sys.argv)

    window = PDFExtractorApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Application closed by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        print("Exiting application.")
        sys.exit(0)