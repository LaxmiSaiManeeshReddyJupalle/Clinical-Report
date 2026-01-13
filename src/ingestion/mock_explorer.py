"""
Mock SMB Explorer for Local Development

Provides identical interface to SMBExplorer but reads from local filesystem.
Enables development and testing without SMB credentials.

Usage:
    from src.ingestion.mock_explorer import MockSMBExplorer, create_mock_explorer

    explorer = create_mock_explorer()
    with explorer.session():
        years = explorer.list_years()
        patients = explorer.list_patients("FY 25")

HIPAA NOTICE: Even mock data should use synthetic names only.
Never use real patient data in mock folders.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

# Configure logging (same as production)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MockConfig:
    """Configuration for mock file explorer."""
    base_path: str  # Local directory containing mock data

    @property
    def base_dir(self) -> Path:
        """Returns Path object for base directory."""
        return Path(self.base_path)


class MockSMBExplorer:
    """
    Mock SMB explorer that reads from local filesystem.

    Provides identical interface to SMBExplorer for seamless switching
    between development (local files) and production (SMB share).

    Structure expected:
        base_path/
        ├── FY 25/
        │   ├── Patient_Test_001/
        │   │   ├── document1.pdf
        │   │   └── document2.docx
        │   └── Patient_Test_002/
        └── FY 24/
    """

    # Supported document extensions (same as SMBExplorer)
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}

    def __init__(self, config: MockConfig):
        """
        Initialize Mock Explorer with local directory.

        Args:
            config: MockConfig with local directory path
        """
        self._config = config
        self._connected = False

        # Verify base path exists
        if not self._config.base_dir.exists():
            logger.warning(f"Mock data directory does not exist. Creating: {self._config.base_path}")
            self._config.base_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """
        Simulate connection (always succeeds for local filesystem).

        Returns:
            True (always succeeds for mock)
        """
        if not self._config.base_dir.exists():
            logger.error("Mock data directory does not exist")
            self._connected = False
            return False

        self._connected = True
        logger.info("Mock SMB connection established (local filesystem)")
        return True

    def disconnect(self) -> None:
        """Simulate disconnection."""
        self._connected = False
        logger.info("Mock SMB connection closed")

    @contextmanager
    def session(self):
        """
        Context manager for mock session handling.

        Usage:
            with explorer.session():
                years = explorer.list_years()
        """
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def _build_path(self, *parts: str) -> Path:
        """
        Build path from components.

        Args:
            *parts: Path components to join

        Returns:
            Path object for the full path
        """
        return self._config.base_dir.joinpath(*parts)

    def list_years(self) -> List[str]:
        """
        List all fiscal year folders in the mock data directory.

        Returns:
            List of fiscal year folder names (e.g., ["FY 25", "FY 24"])
            Sorted in descending order (most recent first)
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")

        years = []
        base_path = self._config.base_dir

        try:
            logger.info("Listing fiscal year directories (mock)")

            for entry in base_path.iterdir():
                if entry.is_dir():
                    folder_name = entry.name
                    # Filter for fiscal year folders (pattern: "FY XX")
                    if folder_name.upper().startswith("FY "):
                        years.append(folder_name)

            # Sort descending (most recent first)
            years.sort(reverse=True)
            logger.info(f"Found {len(years)} fiscal year directories")
            return years

        except PermissionError:
            logger.error("Permission denied accessing base directory")
            raise
        except Exception as e:
            logger.error(f"Error listing years: {type(e).__name__}")
            raise

    def list_patients(self, year_folder: str) -> List[str]:
        """
        List all patient folders within a specific fiscal year.

        SECURITY NOTE: Even mock patient names should be synthetic.

        Args:
            year_folder: Fiscal year folder name (e.g., "FY 25")

        Returns:
            List of patient folder names, sorted alphabetically
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")

        if not year_folder or not year_folder.strip():
            raise ValueError("Year folder cannot be empty")

        patients = []
        year_path = self._build_path(year_folder)

        if not year_path.exists():
            raise FileNotFoundError(f"Year folder '{year_folder}' does not exist")

        try:
            logger.info("Listing patient directories for selected fiscal year (mock)")

            for entry in year_path.iterdir():
                if entry.is_dir():
                    patients.append(entry.name)

            # Sort alphabetically
            patients.sort(key=str.lower)
            logger.info(f"Found {len(patients)} patient directories")
            return patients

        except PermissionError:
            logger.error("Permission denied accessing year directory")
            raise
        except Exception as e:
            logger.error(f"Error listing patients: {type(e).__name__}")
            raise

    def get_patient_files(
        self,
        year: str,
        patient_name: str,
        extensions: Optional[set] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all document files for a specific patient.

        Args:
            year: Fiscal year folder name (e.g., "FY 25")
            patient_name: Patient folder name
            extensions: Optional set of allowed extensions

        Returns:
            List of file info dictionaries with keys:
                - name: File name
                - path: Full path to file (local filesystem path)
                - size: File size in bytes
                - extension: File extension (lowercase)
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")

        if not year or not year.strip():
            raise ValueError("Year cannot be empty")
        if not patient_name or not patient_name.strip():
            raise ValueError("Patient name cannot be empty")

        allowed_ext = extensions or self.SUPPORTED_EXTENSIONS
        files = []
        patient_path = self._build_path(year, patient_name)

        if not patient_path.exists():
            raise FileNotFoundError("Patient folder does not exist")

        try:
            logger.info("Retrieving patient documents (mock)")

            for entry in patient_path.iterdir():
                if entry.is_file():
                    file_name = entry.name
                    ext_lower = entry.suffix.lower()

                    if ext_lower in allowed_ext:
                        file_info = {
                            'name': file_name,
                            'path': str(entry.absolute()),
                            'size': entry.stat().st_size,
                            'extension': ext_lower
                        }
                        files.append(file_info)

            # Sort by name
            files.sort(key=lambda x: x['name'].lower())
            logger.info(f"Found {len(files)} documents")
            return files

        except PermissionError:
            logger.error("Permission denied accessing patient directory")
            raise
        except Exception as e:
            logger.error(f"Error retrieving patient files: {type(e).__name__}")
            raise

    def read_file(self, file_path: str) -> bytes:
        """
        Read file contents from local filesystem.

        Args:
            file_path: Full path to the file

        Returns:
            File contents as bytes
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")

        path = Path(file_path)

        try:
            logger.info("Reading document from local filesystem")
            content = path.read_bytes()
            logger.info("Document read successfully")
            return content
        except FileNotFoundError:
            logger.error("File not found")
            raise
        except PermissionError:
            logger.error("Permission denied reading file")
            raise
        except Exception as e:
            logger.error(f"Error reading file: {type(e).__name__}")
            raise

    def get_file_count(self, year: str, patient_name: str) -> int:
        """
        Get count of supported documents for a patient.

        Args:
            year: Fiscal year folder name
            patient_name: Patient folder name

        Returns:
            Number of supported document files
        """
        files = self.get_patient_files(year, patient_name)
        return len(files)


def create_mock_explorer(base_path: Optional[str] = None) -> MockSMBExplorer:
    """
    Factory function to create MockSMBExplorer.

    Args:
        base_path: Local directory path. Defaults to ./mock_data

    Returns:
        Configured MockSMBExplorer instance
    """
    if base_path is None:
        # Default to mock_data in project root
        project_root = Path(__file__).parent.parent.parent
        base_path = str(project_root / "mock_data")

    config = MockConfig(base_path=base_path)
    return MockSMBExplorer(config)


def get_explorer(use_mock: bool = True):
    """
    Factory function that returns appropriate explorer based on environment.

    Args:
        use_mock: If True, return MockSMBExplorer. If False, return SMBExplorer.

    Returns:
        Explorer instance (Mock or Real SMB)
    """
    if use_mock:
        return create_mock_explorer()
    else:
        from src.ingestion.smb_explorer import create_explorer_from_env
        return create_explorer_from_env()
