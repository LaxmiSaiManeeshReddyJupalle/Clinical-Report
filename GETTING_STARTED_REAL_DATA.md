# Getting Started with Real UICFS Data

## Quick Start Guide

This guide walks you through connecting your Clinical Report Generator to the real UIC file servers.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **UIC VPN access** - Download and install from [techservices.uic.edu/vpn](https://techservices.uic.edu/services/virtual-private-networking-vpn/)
- [ ] **UIC NetID credentials** - Your standard UIC login
- [ ] **File share permissions** - Read access to `\\uicfs.server.uic.edu\AHS-ATUSharedUIC`
- [ ] **Python environment** - Virtual environment activated with all dependencies installed

## Step-by-Step Setup

### 1. Connect to UIC VPN

```bash
# Start Cisco AnyConnect VPN client
# Connect to: vpn.uic.edu
# Login with: NetID and password
```

Verify connection:
```bash
ping uicfs.server.uic.edu
# Should see: Reply from X.X.X.X: bytes=32 time=XXms
```

### 2. Configure Credentials

Create your `.env` file:

```bash
# Copy template
cp .env.template .env

# Open in editor
nano .env   # or: code .env (VS Code)
```

Update these values:
```bash
SMB_SERVER=uicfs.server.uic.edu
SMB_SHARE=AHS-ATUSharedUIC
SMB_BASE_PATH=Services/CA/AE Digital Files
SMB_USERNAME=your_netid        # Replace with your NetID
SMB_PASSWORD=your_password     # Replace with your password
SMB_DOMAIN=uic
```

**Important:** Never commit `.env` to Git! It's already in `.gitignore`.

### 3. Test Connection

Run the connection test script:

```bash
python test_smb_connection.py
```

**Expected output:**
```
======================================================================
  UIC CLINICAL REPORT GENERATOR - SMB CONNECTION TEST
======================================================================

[Step 1] Checking environment configuration...
✓ .env file found
✓ SMB_SERVER is set
✓ SMB_SHARE is set
✓ SMB_BASE_PATH is set
✓ SMB_USERNAME is set
✓ SMB_PASSWORD is set

[Step 2] Testing network connectivity...
✓ DNS resolution successful: uicfs.server.uic.edu -> X.X.X.X
✓ Server is reachable: uicfs.server.uic.edu

[Step 3] Testing SMB connection...
✓ SMB connection established!

[Step 4] Testing file system access...
✓ Found 3 fiscal year(s): FY 25, FY 24, FY 23
✓ Found 42 patient folder(s)
✓ Found 7 document(s)
  File types: .pdf, .docx, .txt

[Step 5] Testing document processing...
✓ Document processor initialized

[Step 6] Testing PII scrubber...
✓ PII scrubber initialized
✓ PII detection and scrubbing working

======================================================================
  TEST SUMMARY
======================================================================

  Environment.......................................... PASS
  Network.............................................. PASS
  SMB Connection....................................... PASS
  File Access.......................................... PASS
  Document Processing.................................. PASS
  PII Scrubber......................................... PASS

  Results: 6/6 tests passed

✓ All tests passed! Ready to use real SMB data.
```

### 4. Switch to Real Data

```bash
# Switch from mock data to real UICFS
python switch_data_source.py real
```

This updates `src/ui/app.py` to use real SMB connection.

### 5. Launch Application

```bash
streamlit run src/ui/app.py
```

Browser will open to: `http://localhost:8501`

### 6. Generate First Report

1. **Select Fiscal Year** - Choose from dropdown (e.g., "FY 25")
2. **Select Patient** - Choose patient from list
3. **Review Files** - See list of available documents
4. **Configure Report**:
   - Report Type: Full Clinical Summary
   - PII Scrubbing: Enabled (recommended)
   - Model: llama3.1:8b (if using local AI)
5. **Generate Report** - Wait ~150 seconds
6. **Download** - Save as Markdown file

## Troubleshooting

### Connection Test Fails

**Error: "Cannot resolve hostname"**
```
Solution: Check VPN connection
  1. Disconnect and reconnect VPN
  2. Verify you can ping: ping uicfs.server.uic.edu
  3. Check DNS: nslookup uicfs.server.uic.edu
```

**Error: "Authentication failed"**
```
Solution: Verify credentials
  1. Double-check NetID and password in .env
  2. Try these domain variations:
     SMB_DOMAIN=uic
     SMB_DOMAIN=ad.uic.edu
  3. Test manually: Open Finder (Mac) → Go → Connect to Server
     smb://uic;your_netid@uicfs.server.uic.edu/AHS-ATUSharedUIC
```

**Error: "Permission denied"**
```
Solution: Request file share access
  1. Contact: AHS IT Support
  2. Request: Read access to AE Digital Files
  3. Provide: Your NetID and project justification
```

**Error: "Path not found"**
```
Solution: Verify base path
  1. Check SMB_BASE_PATH in .env
  2. Should be: Services/CA/AE Digital Files
  3. Use forward slashes, not backslashes
```

### Application Issues

**Can't see real data in app**
```
Solution: Verify data source setting
  python switch_data_source.py status

If still using mock data:
  python switch_data_source.py real
  streamlit run src/ui/app.py
```

**App shows "Connection error"**
```
Solution: Check session state
  1. In browser, refresh the page
  2. Try "Start Over" button
  3. Restart Streamlit if issue persists
```

**Files not loading**
```
Solution: Check file permissions
  1. Verify you can access files via File Explorer/Finder
  2. Check file extensions are supported (.pdf, .docx, .txt, .rtf)
  3. Review app logs for specific errors
```

## Data Flow Architecture

Understanding how data flows from UICFS to your report:

```
┌─────────────────────────────────────────────────────────────────┐
│  UICFS Server (uicfs.server.uic.edu)                            │
│  \\AHS-ATUSharedUIC\Services\CA\AE Digital Files                │
│                                                                  │
│  FY 25/                                                         │
│    └── Patient_Name/                                            │
│         ├── admission_note.pdf                                  │
│         ├── progress_note_2024-11-15.docx                       │
│         └── discharge_summary.pdf                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ SMB Protocol (Port 445)
                           │ Encrypted, Authenticated
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  SMB Explorer (src/ingestion/smb_explorer.py)                   │
│  - Authenticates with UIC credentials                           │
│  - Lists years, patients, files                                 │
│  - Reads file contents into memory                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Raw file bytes
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  Document Processor (src/ingestion/document_processor.py)       │
│  - Extracts text from PDF/DOCX                                  │
│  - Handles formatting, tables                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Extracted text (contains PHI)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  PII Scrubber (src/ingestion/scrubber.py)                       │
│  - Detects names, SSN, dates, addresses, etc.                   │
│  - Replaces with [PHI-ENTITY_TYPE] tags                         │
│  - HIPAA Safe Harbor compliant                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Scrubbed text
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  Vector Store (src/rag/vector_store.py)                         │
│  - Chunks text into segments                                    │
│  - Generates embeddings                                         │
│  - Stores in ChromaDB                                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Semantic search query
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  RAG Retriever (src/rag/retriever.py)                           │
│  - Retrieves relevant chunks                                    │
│  - Builds context for LLM                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Context + Prompt
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  Ollama LLM (Local - llama3.1:8b)                               │
│  - Synthesizes clinical report                                  │
│  - Organizes findings chronologically                           │
│  - Formats with headers and sections                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Generated report (Markdown)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  Streamlit UI (src/ui/app.py)                                   │
│  - Displays report                                              │
│  - Provides download option                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Security & HIPAA Compliance

### What Gets Logged (Safe)

✅ **These are logged:**
- Number of files found
- File types (.pdf, .docx, etc.)
- Connection success/failure
- Processing times
- Error types (without PHI)

### What Never Gets Logged (PHI)

❌ **These are NEVER logged:**
- Patient names
- File paths containing patient names
- File names (may contain dates/identifiers)
- Document contents
- Credentials or passwords

### Best Practices

1. **Always use PII scrubbing** in production
2. **Never screenshot** patient data
3. **Close browser tab** when done (clears session)
4. **Use VPN** - never connect from public networks
5. **Rotate passwords** regularly
6. **Report incidents** immediately to compliance officer

## Performance Expectations

### Connection Times

- **VPN connection**: ~5-10 seconds
- **SMB authentication**: ~2-3 seconds
- **File listing** (per directory): ~1-2 seconds
- **File read** (per document): ~0.5-1 seconds

### Report Generation Times

With llama3.1:8b model:
- **Document processing**: ~20-30 seconds (7 files)
- **PII scrubbing**: ~10-15 seconds
- **LLM generation**: ~90-120 seconds
- **Total**: ~150 seconds (2.5 minutes)

Faster options:
- Use llama3.2:3b: ~60 seconds total
- Use llama3.2:1b: ~40 seconds total (lower quality)
- Skip PII scrubbing: Save ~10-15s (NOT recommended for production)

## Next Steps

Once you've successfully generated a report:

### 1. Validate Quality

- [ ] Compare generated report to source documents
- [ ] Verify all key information is captured
- [ ] Check that PII scrubbing works correctly
- [ ] Confirm no PHI leaks in output

### 2. Optimize Settings

- [ ] Adjust retrieval config (n_results, context size)
- [ ] Test different LLM models (speed vs. quality)
- [ ] Fine-tune prompts for your use case

### 3. Production Deployment

- [ ] Document access control procedures
- [ ] Create user training materials
- [ ] Set up audit logging
- [ ] Establish incident response plan

### 4. Scale Up

- [ ] Test with multiple patients
- [ ] Measure concurrent user capacity
- [ ] Implement batch processing
- [ ] Add export to PDF/Word

## Support Resources

### Documentation

- **Connection Guide**: `UICFS_CONNECTION_GUIDE.md` - Detailed troubleshooting
- **Ollama Setup**: `OLLAMA_SETUP.md` - Local LLM configuration
- **Model Guide**: `MODEL_GUIDE.md` - Model selection and optimization
- **Main README**: `README.md` - Project overview

### Scripts

- **Connection Test**: `python test_smb_connection.py`
- **Data Source Switch**: `python switch_data_source.py [mock|real|status]`
- **Mock Data Explorer**: `python src/ingestion/mock_explorer.py`

### UIC Contacts

- **Network/VPN**: UIC ACCC - techservices.uic.edu
- **File Permissions**: AHS IT Support
- **HIPAA Compliance**: UIC Privacy Office
- **Technical Issues**: Create issue in repository

## FAQ

**Q: Can I run this without VPN?**
A: No. The UICFS server is only accessible from UIC network or via VPN.

**Q: What if I don't have file share permissions?**
A: Contact AHS IT Support and request read access to AE Digital Files share.

**Q: Can I use this on my personal laptop?**
A: Only if approved by your HIPAA compliance officer. Must follow all security policies.

**Q: What happens if I lose VPN connection during processing?**
A: The operation will fail with a connection error. Simply reconnect and try again.

**Q: How do I know if I'm using mock vs. real data?**
A: Run `python switch_data_source.py status` or check the UI header.

**Q: Can multiple users connect simultaneously?**
A: Yes, SMB supports concurrent connections. Each user needs their own credentials.

**Q: Where are the generated reports stored?**
A: Reports are generated in-memory and downloaded to your browser's download folder. Nothing is stored on the server.

**Q: What file formats are supported?**
A: Currently: `.pdf`, `.docx`, `.doc`, `.txt`, `.rtf`

**Q: How long are files kept in memory?**
A: Only during processing. Memory is cleared after report generation completes.

**Q: Can I customize the report templates?**
A: Yes! Edit the prompts in `src/rag/retriever.py` (PromptBuilder class).

---

**You're all set!** 🎉

If you encounter any issues not covered here, check `UICFS_CONNECTION_GUIDE.md` or create an issue in the repository.
