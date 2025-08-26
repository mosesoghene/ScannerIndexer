import os
import re
from pathlib import Path
from typing import List, Optional


class FileUtils:
    """Utility functions for file and path operations"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters from filename"""
        # Remove invalid characters for Windows/Unix
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename)

        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip('. ')

        # Ensure filename isn't empty
        if not sanitized:
            sanitized = "untitled"

        # Limit length to reasonable size
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized

    @staticmethod
    def ensure_unique_filename(filepath: str) -> str:
        """Ensure filename is unique by adding numbers if needed"""
        path = Path(filepath)

        if not path.exists():
            return filepath

        counter = 1
        while True:
            stem = path.stem
            suffix = path.suffix
            parent = path.parent

            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name

            if not new_path.exists():
                return str(new_path)

            counter += 1

    @staticmethod
    def get_relative_path(file_path: str, base_path: str) -> str:
        """Get relative path from base path"""
        try:
            return str(Path(file_path).relative_to(Path(base_path)))
        except ValueError:
            return str(Path(file_path).name)

    @staticmethod
    def create_directory_structure(path: str) -> bool:
        """Create directory structure if it doesn't exist"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory structure for {path}: {e}")
            return False

    @staticmethod
    def get_file_size_mb(filepath: str) -> float:
        """Get file size in MB"""
        try:
            size_bytes = Path(filepath).stat().st_size
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0

    @staticmethod
    def validate_output_path(output_path: str) -> tuple[bool, Optional[str]]:
        """Validate if output path is writable and valid"""
        try:
            path = Path(output_path)

            # Check if parent directory can be created
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check if we can write to the location
            test_file = path.parent / "test_write.tmp"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                return False, "Cannot write to output directory"

            return True, None

        except Exception as e:
            return False, f"Invalid output path: {str(e)}"

    @staticmethod
    def get_available_space_gb(path: str) -> float:
        """Get available disk space in GB"""
        try:
            stat = os.statvfs(str(Path(path).parent))
            # Available space = fragment size * available fragments
            available_bytes = stat.f_frsize * stat.f_bavail
            return available_bytes / (1024 * 1024 * 1024)
        except Exception:
            return 0.0