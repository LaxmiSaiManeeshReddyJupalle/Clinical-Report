"""
SMB Explorer Module for UIC ATU Clinical Report Generator

Provides secure "drill-down" file exploration for the AE Digital Files share.
Handles SMB connections with proper path handling for spaces in folder names.

HIPAA NOTICE: This module accesses PHI. Patient folder names must NEVER be
logged to console/terminal. Display only in secure Streamlit UI elements.
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from contextlib import contextmanager

import smbclient
from smbclient import listdir, scandir
from smbclient.path import isdir, isfile

# Configure logging to exclude PHI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SMBConfig:
    """Configuration for SMB connection."""
    server: str
    share: str
    base_path: str
    username: str
    password: str
    domain: str = ""

    @property
    def share_root(self) -> str:
        """Returns the full UNC path to the share root."""
        return f"\\\\{self.server}\\{self.share}"

    @property
    def base_unc_path(self) -> str:
        """Returns the full UNC path including base directory."""
        return f"{self.share_root}\\{self.base_path}"


class SMBExplorer:
    """
    Secure SMB file explorer with drill-down navigation.

    Provides hierarchical access to patient files organized by fiscal year.
    Structure: /AE Digital Files/FY XX/Patient Name/documents...

    SECURITY: All patient-identifying information is handled securely.
    Folder names (which contain patient names) are NEVER logged.
    """

    # Supported document extensions
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}

    def __init__(self, config: SMBConfig):
        """
        Initialize SMB Explorer with connection configuration.

        Args:
            config: SMBConfig object with connection details
        """
        self._config = config
        self._connected = False

    def connect(self) -> bool:
        """
        Establish SMB connection using provided credentials.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            smbclient.register_session(
                server=self._config.server,
                username=self._config.username,
                password=self._config.password,
                connection_timeout=30
            )
            self._connected = True
            logger.info("SMB connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to establish SMB connection: {type(e).__name__}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close SMB connection and cleanup resources."""
        try:
            smbclient.reset_connection_cache()
            self._connected = False
            logger.info("SMB connection closed")
        except Exception as e:
            logger.warning(f"Error during disconnect: {type(e).__name__}")

    @contextmanager
    def session(self):
        """
        Context manager for SMB session handling.

        Usage:
            with explorer.session():
                years = explorer.list_years()
        """
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def _build_path(self, *parts: str) -> str:
        """
        Build a proper UNC path handling spaces correctly.

        Args:
            *parts: Path components to join

        Returns:
            Properly formatted UNC path string
        """
        # Start with the base UNC path
        base = self._config.base_unc_path

        # Join additional parts using backslash (UNC standard)
        if parts:
            additional = "\\".join(parts)
            return f"{base}\\{additional}"
        return base

    def list_years(self) -> List[str]:
        """
        List all fiscal year folders in the root AE Digital Files directory.

        Returns:
            List of fiscal year folder names (e.g., ["FY 24", "FY 25"])
            Sorted in descending order (most recent first)

        Raises:
            ConnectionError: If not connected to SMB share
            PermissionError: If access denied to directory
        """
        if not self._connected:
            raise ConnectionError("Not connected to SMB share. Call connect() first.")

        years = []
        base_path = self._config.base_unc_path

        try:
            # Log action without revealing path details that might contain PHI
            logger.info("Listing fiscal year directories")

            for entry in scandir(base_path):
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

        SECURITY NOTE: Patient names are returned but NEVER logged.
        Display only in secure Streamlit UI elements.

        Args:
            year_folder: Fiscal year folder name (e.g., "FY 25")

        Returns:
            List of patient folder names, sorted alphabetically

        Raises:
            ConnectionError: If not connected to SMB share
            ValueError: If year_folder is invalid
            FileNotFoundError: If year folder doesn't exist
        """
        if not self._connected:
            raise ConnectionError("Not connected to SMB share. Call connect() first.")

        if not year_folder or not year_folder.strip():
            raise ValueError("Year folder cannot be empty")

        patients = []
        year_path = self._build_path(year_folder)

        try:
            # Log action WITHOUT patient names (HIPAA compliance)
            logger.info("Listing patient directories for selected fiscal year")

            for entry in scandir(year_path):
                if entry.is_dir():
                    # Add patient folder name (DO NOT LOG THIS)
                    patients.append(entry.name)

            # Sort alphabetically for easier navigation
            patients.sort(key=str.lower)

            # Log count only, never names (HIPAA)
            logger.info(f"Found {len(patients)} patient directories")
            return patients

        except FileNotFoundError:
            logger.error("Specified year folder not found")
            raise FileNotFoundError(f"Year folder '{year_folder}' does not exist")
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
    ) -> List[dict]:
        """
        Get all document files for a specific patient.

        SECURITY NOTE: Patient names and file details are returned but NEVER logged.
        Display only in secure Streamlit UI elements.

        Args:
            year: Fiscal year folder name (e.g., "FY 25")
            patient_name: Patient folder name
            extensions: Optional set of allowed extensions.
                       Defaults to SUPPORTED_EXTENSIONS

        Returns:
            List of file info dictionaries with keys:
                - name: File name
                - path: Full UNC path to file
                - size: File size in bytes
                - extension: File extension (lowercase)

        Raises:
            ConnectionError: If not connected to SMB share
            ValueError: If year or patient_name is invalid
            FileNotFoundError: If patient folder doesn't exist
        """
        if not self._connected:
            raise ConnectionError("Not connected to SMB share. Call connect() first.")

        if not year or not year.strip():
            raise ValueError("Year cannot be empty")
        if not patient_name or not patient_name.strip():
            raise ValueError("Patient name cannot be empty")

        allowed_ext = extensions or self.SUPPORTED_EXTENSIONS
        files = []
        patient_path = self._build_path(year, patient_name)

        try:
            # Log action WITHOUT patient-identifying info (HIPAA compliance)
            logger.info("Retrieving patient documents")

            for entry in scandir(patient_path):
                if entry.is_file():
                    file_name = entry.name
                    _, ext = os.path.splitext(file_name)
                    ext_lower = ext.lower()

                    if ext_lower in allowed_ext:
                        file_info = {
                            'name': file_name,
                            'path': f"{patient_path}\\{file_name}",
                            'size': entry.stat().st_size,
                            'extension': ext_lower
                        }
                        files.append(file_info)

            # Sort by name
            files.sort(key=lambda x: x['name'].lower())

            # Log count only, never file names (may contain PHI)
            logger.info(f"Found {len(files)} documents")
            return files

        except FileNotFoundError:
            logger.error("Specified patient folder not found")
            raise FileNotFoundError("Patient folder does not exist")
        except PermissionError:
            logger.error("Permission denied accessing patient directory")
            raise
        except Exception as e:
            logger.error(f"Error retrieving patient files: {type(e).__name__}")
            raise

    def read_file(self, file_path: str) -> bytes:
        """
        Read file contents from SMB share.

        Args:
            file_path: Full UNC path to the file

        Returns:
            File contents as bytes

        Raises:
            ConnectionError: If not connected
            FileNotFoundError: If file doesn't exist
            PermissionError: If access denied
        """
        if not self._connected:
            raise ConnectionError("Not connected to SMB share. Call connect() first.")

        try:
            logger.info("Reading document from share")
            with smbclient.open_file(file_path, mode='rb') as f:
                content = f.read()
            logger.info("Document read successfully")
            return content
        except FileNotFoundError:
            logger.error("File not found on share")
            raise
        except PermissionError:
            logger.error("Permission denied reading file")
            raise
        except Exception as e:
            logger.error(f"Error reading file: {type(e).__name__}")
            raise

    def get_file_count(self, year: str, patient_name: str) -> int:
        """
        Get count of supported documents for a patient without retrieving details.

        Useful for UI display without loading full file list.

        Args:
            year: Fiscal year folder name
            patient_name: Patient folder name

        Returns:
            Number of supported document files
        """
        files = self.get_patient_files(year, patient_name)
        return len(files)


def create_explorer_from_env() -> SMBExplorer:
    """
    Factory function to create SMBExplorer from environment variables.

    Required environment variables:
        - SMB_SERVER: Server hostname (e.g., "uicfs.server.uic.edu")
        - SMB_SHARE: Share name (e.g., "AHS-ATUSharedUIC")
        - SMB_BASE_PATH: Base directory path (e.g., "Services/CA/AE Digital Files")
        - SMB_USERNAME: Domain username
        - SMB_PASSWORD: Domain password
        - SMB_DOMAIN: Optional domain name

    Returns:
        Configured SMBExplorer instance

    Raises:
        EnvironmentError: If required variables are missing
    """
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ['SMB_SERVER', 'SMB_SHARE', 'SMB_BASE_PATH', 'SMB_USERNAME', 'SMB_PASSWORD']
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    config = SMBConfig(
        server=os.environ['SMB_SERVER'],
        share=os.environ['SMB_SHARE'],
        base_path=os.environ['SMB_BASE_PATH'],
        username=os.environ['SMB_USERNAME'],
        password=os.environ['SMB_PASSWORD'],
        domain=os.environ.get('SMB_DOMAIN', '')
    )

    return SMBExplorer(config)
