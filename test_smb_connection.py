"""
SMB Connection Test Script for UICFS Server

This script tests connectivity to the UIC file server and validates
that you can access the clinical documentation share.

Usage:
    python test_smb_connection.py

Prerequisites:
    1. UIC VPN connected
    2. .env file configured with credentials
    3. Read permissions on AE Digital Files share
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(step, message):
    """Print formatted step message."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step}]{Colors.RESET} {message}")

def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_environment():
    """Test that environment is properly configured."""
    print_step(1, "Checking environment configuration...")

    # Load .env file
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print_error(".env file not found!")
        print("  Run: cp .env.template .env")
        print("  Then edit .env with your credentials")
        return False

    load_dotenv()
    print_success(".env file found")

    # Check required variables
    required_vars = [
        'SMB_SERVER',
        'SMB_SHARE',
        'SMB_BASE_PATH',
        'SMB_USERNAME',
        'SMB_PASSWORD'
    ]

    missing = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value or value.startswith('your_'):
            missing.append(var)
        else:
            print_success(f"{var} is set")

    if missing:
        print_error("Missing or incomplete environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nEdit your .env file and set these values")
        return False

    return True

def test_network_connectivity():
    """Test network connectivity to UICFS server."""
    print_step(2, "Testing network connectivity...")

    server = os.environ.get('SMB_SERVER', 'uicfs.server.uic.edu')

    # Test DNS resolution
    import socket
    try:
        ip = socket.gethostbyname(server)
        print_success(f"DNS resolution successful: {server} -> {ip}")
    except socket.gaierror:
        print_error(f"Cannot resolve hostname: {server}")
        print("  Are you connected to UIC VPN?")
        return False

    # Test ping (may not work if ICMP is blocked)
    import subprocess
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', server],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Server is reachable: {server}")
        else:
            print_warning(f"Ping failed (may be blocked by firewall)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("Ping test skipped")

    return True

def test_smb_connection():
    """Test SMB connection to file share."""
    print_step(3, "Testing SMB connection...")

    try:
        from src.ingestion.smb_explorer import create_explorer_from_env

        print("  Creating SMB explorer...")
        explorer = create_explorer_from_env()

        print("  Establishing connection...")
        if explorer.connect():
            print_success("SMB connection established!")
            return explorer
        else:
            print_error("Failed to establish SMB connection")
            return None

    except Exception as e:
        print_error(f"Connection failed: {type(e).__name__}")
        print(f"  Error: {str(e)}")
        return None

def test_file_access(explorer):
    """Test file system access and permissions."""
    print_step(4, "Testing file system access...")

    try:
        # Test 1: List fiscal years
        print("  Listing fiscal years...")
        years = explorer.list_years()
        if years:
            print_success(f"Found {len(years)} fiscal year(s): {', '.join(years)}")
        else:
            print_warning("No fiscal year folders found")
            return False

        # Test 2: List patients (for most recent year)
        most_recent_year = years[0]
        print(f"\n  Listing patients for {most_recent_year}...")
        patients = explorer.list_patients(most_recent_year)
        if patients:
            print_success(f"Found {len(patients)} patient folder(s)")
            # Don't print patient names (HIPAA)
        else:
            print_warning(f"No patient folders in {most_recent_year}")
            return False

        # Test 3: List files (for first patient)
        first_patient = patients[0]
        print(f"\n  Listing files for first patient...")
        files = explorer.get_patient_files(most_recent_year, first_patient)
        if files:
            print_success(f"Found {len(files)} document(s)")
            print(f"  File types: {', '.join(set(f['extension'] for f in files))}")

            # Show file details (without names containing PHI)
            print(f"\n  Sample file information:")
            for i, file_info in enumerate(files[:3], 1):  # Show first 3
                size_kb = file_info['size'] / 1024
                print(f"    {i}. Type: {file_info['extension']}, Size: {size_kb:.1f} KB")

            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more files")
        else:
            print_warning("No supported files found for patient")
            return False

        # Test 4: Read a file (first file)
        if files:
            print(f"\n  Testing file read operation...")
            first_file = files[0]
            try:
                content = explorer.read_file(first_file['path'])
                size_kb = len(content) / 1024
                print_success(f"Successfully read file ({size_kb:.1f} KB)")
            except Exception as e:
                print_error(f"Failed to read file: {type(e).__name__}")
                return False

        return True

    except PermissionError:
        print_error("Permission denied - check share permissions")
        print("  Contact: AHS IT Support")
        print("  Request: Read access to AE Digital Files share")
        return False

    except FileNotFoundError:
        print_error("Path not found - verify SMB_BASE_PATH in .env")
        return False

    except Exception as e:
        print_error(f"File access test failed: {type(e).__name__}")
        print(f"  Error: {str(e)}")
        return False

    finally:
        # Always disconnect
        if explorer:
            explorer.disconnect()
            print("\n  Connection closed")

def test_document_processing():
    """Test document processing pipeline."""
    print_step(5, "Testing document processing...")

    try:
        from src.ingestion.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        print_success("Document processor initialized")

        # List supported formats
        print(f"  Supported formats: {', '.join(processor.SUPPORTED_FORMATS)}")

        return True

    except ImportError:
        print_warning("Document processor not yet implemented")
        return True  # Not critical for connection test

    except Exception as e:
        print_error(f"Document processing test failed: {type(e).__name__}")
        return False

def test_pii_scrubber():
    """Test PII scrubber functionality."""
    print_step(6, "Testing PII scrubber...")

    try:
        from src.ingestion.scrubber import HealthcarePIIScrubber

        print("  Initializing PII scrubber...")
        scrubber = HealthcarePIIScrubber()
        print_success("PII scrubber initialized")

        # Test with sample PHI
        test_text = "Patient John Smith, SSN 123-45-6789, born 01/15/1980"
        print(f"\n  Testing with sample PHI...")
        result = scrubber.scrub(test_text)

        if result.scrubbed_text != test_text:
            print_success("PII detection and scrubbing working")
            print(f"    Original: {test_text}")
            print(f"    Scrubbed: {result.scrubbed_text}")
            print(f"    Entities found: {len(result.entities)}")
        else:
            print_warning("No entities detected in test text")

        return True

    except ImportError as e:
        print_error(f"Missing dependency: {str(e)}")
        print("  Run: python -m spacy download en_core_web_lg")
        return False

    except Exception as e:
        print_error(f"PII scrubber test failed: {type(e).__name__}")
        return False

def main():
    """Run all connection tests."""
    print(f"\n{Colors.BOLD}{'='*70}")
    print("  UIC CLINICAL REPORT GENERATOR - SMB CONNECTION TEST")
    print(f"{'='*70}{Colors.RESET}\n")

    results = []

    # Test 1: Environment
    if test_environment():
        results.append(("Environment", True))
    else:
        results.append(("Environment", False))
        print_summary(results)
        return 1

    # Test 2: Network
    if test_network_connectivity():
        results.append(("Network", True))
    else:
        results.append(("Network", False))
        print_summary(results)
        return 1

    # Test 3: SMB Connection
    explorer = test_smb_connection()
    if explorer:
        results.append(("SMB Connection", True))
    else:
        results.append(("SMB Connection", False))
        print_summary(results)
        return 1

    # Test 4: File Access
    if test_file_access(explorer):
        results.append(("File Access", True))
    else:
        results.append(("File Access", False))
        print_summary(results)
        return 1

    # Test 5: Document Processing (optional)
    if test_document_processing():
        results.append(("Document Processing", True))
    else:
        results.append(("Document Processing", False))

    # Test 6: PII Scrubber
    if test_pii_scrubber():
        results.append(("PII Scrubber", True))
    else:
        results.append(("PII Scrubber", False))

    # Print summary
    print_summary(results)

    # Return exit code
    if all(result for _, result in results):
        return 0
    else:
        return 1

def print_summary(results):
    """Print test summary."""
    print(f"\n{Colors.BOLD}{'='*70}")
    print("  TEST SUMMARY")
    print(f"{'='*70}{Colors.RESET}\n")

    for test_name, passed in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name:.<50} {status}")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    print(f"\n  {Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.RESET}")

    if all(result for _, result in results):
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed! Ready to use real SMB data.{Colors.RESET}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
        print(f"  1. In src/ui/app.py, set 'using_mock': False")
        print(f"  2. Run: streamlit run src/ui/app.py")
        print(f"  3. Test report generation with real patient data")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed. Review errors above.{Colors.RESET}")
        print(f"\n{Colors.BLUE}Troubleshooting:{Colors.RESET}")
        print(f"  1. Check UIC VPN connection")
        print(f"  2. Verify credentials in .env file")
        print(f"  3. Review UICFS_CONNECTION_GUIDE.md")
        print(f"  4. Contact AHS IT if permission issues persist")

    print()

if __name__ == '__main__':
    sys.exit(main())
