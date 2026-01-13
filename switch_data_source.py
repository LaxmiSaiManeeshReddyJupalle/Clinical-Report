"""
Data Source Switcher

Quick utility to toggle between mock data and real UICFS connection.

Usage:
    python switch_data_source.py mock    # Use mock data (for testing)
    python switch_data_source.py real    # Use real UICFS connection
    python switch_data_source.py status  # Check current setting
"""

import sys
import re
from pathlib import Path

APP_FILE = Path(__file__).parent / 'src' / 'ui' / 'app.py'

def get_current_setting():
    """Check current data source setting."""
    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Find the using_mock setting in init_session_state
    match = re.search(r"'using_mock':\s*(True|False)", content)
    if match:
        return match.group(1) == 'True'
    return None

def set_data_source(use_mock):
    """Update data source setting in app.py."""
    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Replace the using_mock value
    new_value = 'True' if use_mock else 'False'
    pattern = r"('using_mock':\s*)(True|False)"
    replacement = r'\g<1>' + new_value

    new_content = re.sub(pattern, replacement, content)

    # Write back
    with open(APP_FILE, 'w') as f:
        f.write(new_content)

    return True

def print_status():
    """Print current data source status."""
    using_mock = get_current_setting()

    if using_mock is None:
        print("❓ Could not determine current setting")
        return

    print("\n" + "="*60)
    print("  DATA SOURCE STATUS")
    print("="*60 + "\n")

    if using_mock:
        print("  📦 Currently using: MOCK DATA")
        print("     Location: src/ingestion/mock_data/")
        print("     Patients: Synthetic test data")
        print("\n  To switch to real data:")
        print("     python switch_data_source.py real")
    else:
        print("  🌐 Currently using: REAL UICFS CONNECTION")
        print("     Server: uicfs.server.uic.edu")
        print("     Share: AHS-ATUSharedUIC")
        print("\n  To switch to mock data:")
        print("     python switch_data_source.py mock")

    print()

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python switch_data_source.py [mock|real|status]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'status':
        print_status()
        sys.exit(0)

    if command not in ['mock', 'real']:
        print(f"Error: Unknown command '{command}'")
        print("Usage: python switch_data_source.py [mock|real|status]")
        sys.exit(1)

    use_mock = (command == 'mock')
    current_is_mock = get_current_setting()

    # Check if already set
    if current_is_mock == use_mock:
        source = "MOCK DATA" if use_mock else "REAL UICFS"
        print(f"\n✓ Already using {source}")
        print_status()
        sys.exit(0)

    # Update setting
    print(f"\nSwitching to {'MOCK DATA' if use_mock else 'REAL UICFS'}...")

    if set_data_source(use_mock):
        print("✓ Setting updated successfully!\n")

        if use_mock:
            print("  Now using: MOCK DATA")
            print("  Location: src/ingestion/mock_data/")
            print("\n  Next steps:")
            print("    streamlit run src/ui/app.py")
        else:
            print("  Now using: REAL UICFS CONNECTION")
            print("\n  ⚠️  IMPORTANT:")
            print("    1. Ensure UIC VPN is connected")
            print("    2. Verify .env file has correct credentials")
            print("    3. Test connection first:")
            print("       python test_smb_connection.py")
            print("\n  If connection test passes:")
            print("    streamlit run src/ui/app.py")

        print()
    else:
        print("✗ Failed to update setting")
        sys.exit(1)

if __name__ == '__main__':
    main()
