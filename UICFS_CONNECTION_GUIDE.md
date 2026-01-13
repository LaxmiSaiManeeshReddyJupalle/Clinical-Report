# UICFS Server Connection Guide

## Overview

This guide explains how to connect the Clinical Report Generator to the UIC file servers (`uicfs.server.uic.edu`) to access real patient clinical documentation.

## Architecture: SMB/CIFS File Share Access

The application uses the **SMB (Server Message Block)** protocol to securely connect to UIC's Windows file servers. This is the same protocol used when you access network drives on Windows/Mac.

### Current File Structure on UICFS

```
\\uicfs.server.uic.edu\AHS-ATUSharedUIC\Services\CA\AE Digital Files\
├── FY 25/
│   ├── Patient_Name_001/
│   │   ├── admission_note.pdf
│   │   ├── progress_note_2024-11-15.docx
│   │   ├── discharge_summary.pdf
│   │   └── ...
│   ├── Patient_Name_002/
│   └── ...
├── FY 24/
│   ├── Patient_Name_001/
│   └── ...
└── ...
```

## Prerequisites

### 1. Network Access

**You MUST have one of the following:**

- **UIC Campus Network**: Physical connection to UIC network
- **UIC VPN**: Remote access via UIC VPN client
  - Download: https://techservices.uic.edu/services/virtual-private-networking-vpn/
  - Install Cisco AnyConnect VPN client
  - Connect before running the application

**Test connectivity:**
```bash
# Test if you can reach the server
ping uicfs.server.uic.edu

# Expected output:
# Reply from <IP>: bytes=32 time=XX ms TTL=XX
```

### 2. Credentials

You need your **UIC NetID credentials**:
- **Username**: Your UIC NetID (e.g., `jsmith`)
- **Password**: Your UIC password
- **Domain**: `uic` or `ad.uic.edu` (try both if one doesn't work)

### 3. Permissions

You need **read access** to the AE Digital Files share:
- Contact: UIC AHS IT Support
- Request: Access to `\\uicfs.server.uic.edu\AHS-ATUSharedUIC\Services\CA\AE Digital Files`
- Justification: Clinical report generation project

## Setup Steps

### Step 1: Create Environment Configuration

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Edit `.env` file** with your credentials:
   ```bash
   # SMB Connection Settings
   SMB_SERVER=uicfs.server.uic.edu
   SMB_SHARE=AHS-ATUSharedUIC
   SMB_BASE_PATH=Services/CA/AE Digital Files
   SMB_USERNAME=your_netid_here
   SMB_PASSWORD=your_password_here
   SMB_DOMAIN=uic
   ```

3. **Secure the file:**
   ```bash
   chmod 600 .env  # Make file readable only by you
   ```

### Step 2: Test Connection

Create a simple test script to verify connectivity:

```python
# test_smb_connection.py
import os
from dotenv import load_dotenv
from src.ingestion.smb_explorer import create_explorer_from_env

# Load credentials
load_dotenv()

# Create explorer
explorer = create_explorer_from_env()

# Test connection
print("Testing SMB connection to UICFS...")
with explorer.session():
    print("✓ Connection successful!")

    # List fiscal years
    years = explorer.list_years()
    print(f"✓ Found {len(years)} fiscal years: {years}")

    # List patients for most recent year
    if years:
        year = years[0]  # Most recent year
        patients = explorer.list_patients(year)
        print(f"✓ Found {len(patients)} patients in {year}")

        # Get files for first patient
        if patients:
            patient = patients[0]
            files = explorer.get_patient_files(year, patient)
            print(f"✓ Found {len(files)} files for patient")
            print(f"  File types: {set(f['extension'] for f in files)}")

print("\n✓ SMB connection test complete!")
```

Run the test:
```bash
python test_smb_connection.py
```

### Step 3: Switch from Mock to Real Data

Update `src/ui/app.py` to use real SMB connection instead of mock data:

**Find this section in app.py:**
```python
def init_session_state():
    # ... existing code ...
    'using_mock': True,  # Change this to False
```

**Change to:**
```python
def init_session_state():
    # ... existing code ...
    'using_mock': False,  # Use real SMB connection
```

### Step 4: Initialize Explorer in App

The app already has logic to initialize either mock or real explorer. Verify this section exists:

```python
def get_explorer():
    """Get or create SMB explorer (real or mock based on config)."""
    if st.session_state.explorer is None:
        if st.session_state.using_mock:
            st.session_state.explorer = create_mock_explorer()
        else:
            # Real SMB connection
            from src.ingestion.smb_explorer import create_explorer_from_env
            st.session_state.explorer = create_explorer_from_env()

    return st.session_state.explorer
```

## Connection Methods & Techniques

### Method 1: SMB Protocol (Current Implementation)

**Advantages:**
- ✓ Native Windows file sharing protocol
- ✓ Widely supported across platforms
- ✓ Handles authentication and permissions
- ✓ Python library: `smbprotocol`

**Current Implementation:**
```python
import smbclient

# Register session with credentials
smbclient.register_session(
    server="uicfs.server.uic.edu",
    username="netid",
    password="password",
    connection_timeout=30
)

# Access files using UNC paths
with smbclient.open_file(r"\\uicfs.server.uic.edu\share\file.txt", 'rb') as f:
    content = f.read()
```

### Method 2: Mount Network Drive (Alternative)

**For macOS/Linux development:**

1. **Mount the share:**
   ```bash
   # macOS
   open smb://uicfs.server.uic.edu/AHS-ATUSharedUIC

   # Or via Finder: Cmd+K, enter smb://uicfs.server.uic.edu/AHS-ATUSharedUIC

   # Linux (CIFS mount)
   sudo mount -t cifs //uicfs.server.uic.edu/AHS-ATUSharedUIC /mnt/uicfs \
        -o username=netid,domain=uic,vers=3.0
   ```

2. **Access as local filesystem:**
   ```python
   # Files appear at /Volumes/AHS-ATUSharedUIC (macOS)
   base_path = "/Volumes/AHS-ATUSharedUIC/Services/CA/AE Digital Files"

   # Or /mnt/uicfs (Linux)
   base_path = "/mnt/uicfs/Services/CA/AE Digital Files"
   ```

**Advantages:**
- Simple file system access
- Works with any Python file operation
- Good for development/testing

**Disadvantages:**
- Requires OS-level mount
- Manual connection management
- Not suitable for production deployment

### Method 3: WebDAV (If Available)

Some Windows file servers also expose WebDAV:

```python
from webdav3.client import Client

client = Client({
    'webdav_hostname': "https://uicfs.server.uic.edu/webdav",
    'webdav_login': "uic\\netid",
    'webdav_password': "password"
})

files = client.list("/AE Digital Files/FY 25")
```

**Check if enabled:**
```bash
curl -I https://uicfs.server.uic.edu/webdav
```

### Method 4: SFTP/SSH (Unlikely for Windows Servers)

Windows servers typically don't have SFTP unless specifically configured.

## Troubleshooting

### Issue 1: Connection Timeout

**Error:** `Connection timed out` or `Cannot reach server`

**Solutions:**
1. **Check VPN connection:**
   ```bash
   # Verify you're on VPN
   ipconfig getifaddr utun1  # macOS
   ip addr show tun0         # Linux
   ```

2. **Test network connectivity:**
   ```bash
   ping uicfs.server.uic.edu
   nslookup uicfs.server.uic.edu
   traceroute uicfs.server.uic.edu
   ```

3. **Check firewall settings:**
   - SMB uses ports 445 (SMB), 139 (NetBIOS)
   - Ensure not blocked by local firewall

### Issue 2: Authentication Failed

**Error:** `Invalid credentials` or `Access denied`

**Solutions:**
1. **Verify credentials:**
   ```bash
   # Try connecting manually first
   # macOS: Finder > Go > Connect to Server
   smb://uic;netid@uicfs.server.uic.edu/AHS-ATUSharedUIC
   ```

2. **Try different domain formats:**
   ```python
   # Try these variations
   SMB_DOMAIN=uic
   SMB_DOMAIN=ad.uic.edu
   SMB_DOMAIN=ad

   # Or include domain in username
   SMB_USERNAME=uic\\netid
   SMB_USERNAME=netid@uic.edu
   ```

3. **Check password special characters:**
   - Ensure password is properly escaped in .env
   - Use single quotes if password has special chars

### Issue 3: Permission Denied

**Error:** `Access denied` to specific folders/files

**Solutions:**
1. **Verify share permissions:**
   - Contact: AHS IT Support
   - Request: Read access to AE Digital Files

2. **Test with different paths:**
   ```python
   # Try listing just the share root first
   listdir(r"\\uicfs.server.uic.edu\AHS-ATUSharedUIC")

   # Then drill down
   listdir(r"\\uicfs.server.uic.edu\AHS-ATUSharedUIC\Services")
   ```

### Issue 4: Path Not Found

**Error:** `FileNotFoundError` or `Path does not exist`

**Solutions:**
1. **Verify exact path structure:**
   ```python
   # Log the full UNC path being used
   print(explorer._build_path("FY 25", "Patient Name"))
   ```

2. **Check for spaces in folder names:**
   - Ensure spaces are handled correctly
   - UNC paths use backslashes: `\`

3. **Case sensitivity:**
   - Windows is case-insensitive but preserve case
   - Use exact folder names as they appear

## Security Best Practices

### 1. Credential Management

**DO:**
- ✓ Store credentials in `.env` file (excluded from Git)
- ✓ Use environment variables
- ✓ Rotate passwords regularly
- ✓ Use read-only accounts when possible

**DON'T:**
- ✗ Hardcode credentials in source code
- ✗ Commit `.env` to version control
- ✗ Share credentials via email/chat
- ✗ Use admin accounts unnecessarily

### 2. Connection Security

**DO:**
- ✓ Use SMB3 protocol (encrypted by default)
- ✓ Connect only via VPN
- ✓ Use connection timeouts
- ✓ Close connections when done

**DON'T:**
- ✗ Store files locally
- ✗ Leave connections open indefinitely
- ✗ Connect from unsecured networks
- ✗ Cache credentials in memory

### 3. HIPAA Compliance

**DO:**
- ✓ Use context managers for connections
- ✓ Log only counts, never patient names
- ✓ Process files in memory when possible
- ✓ Scrub PII before any output

**DON'T:**
- ✗ Log patient names or file paths with PHI
- ✗ Store PHI in logs or temporary files
- ✗ Display PHI in error messages
- ✗ Print debugging info with patient data

## Performance Optimization

### 1. Connection Pooling

Keep connection alive for multiple operations:

```python
# Good: Single session for multiple operations
with explorer.session():
    years = explorer.list_years()
    for year in years:
        patients = explorer.list_patients(year)
        # Process patients...

# Bad: Multiple connections
for year in years:
    with explorer.session():
        patients = explorer.list_patients(year)
```

### 2. Batch Operations

Process files in batches:

```python
# Efficient: Get all files at once
files = explorer.get_patient_files(year, patient)
for file_info in files:
    content = explorer.read_file(file_info['path'])
    process(content)
```

### 3. Caching

Cache directory listings (but not file contents with PHI):

```python
# Cache fiscal years (changes infrequently)
if 'cached_years' not in st.session_state:
    st.session_state.cached_years = explorer.list_years()
```

## Next Steps

Once connected to real data:

1. **Test with single patient:**
   - Select one patient
   - Verify files are retrieved
   - Check PII scrubbing works

2. **Validate report generation:**
   - Generate test report
   - Compare to manually reviewed documents
   - Verify no PHI leakage

3. **Performance testing:**
   - Measure file retrieval time
   - Optimize if needed
   - Test with multiple users

4. **Production deployment:**
   - Document access requirements
   - Create user guide
   - Train end users

## Support Contacts

- **Network Access**: UIC ACCC (techservices.uic.edu)
- **File Share Permissions**: AHS IT Support
- **VPN Issues**: UIC Technology Solutions Center
- **HIPAA Compliance**: UIC Privacy Office

## References

- SMB Protocol: https://en.wikipedia.org/wiki/Server_Message_Block
- smbprotocol Python library: https://github.com/jborean93/smbprotocol
- UIC VPN Setup: https://techservices.uic.edu/services/virtual-private-networking-vpn/
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
