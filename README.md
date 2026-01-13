# UIC ATU Clinical Report Generator

A HIPAA-compliant Retrieval Augmented Generation (RAG) system for automatically generating clinical reports from patient documentation at the UIC Assistive Technology Unit.

## 🏥 Overview

This application provides a secure, user-friendly interface for healthcare professionals to generate comprehensive clinical reports from patient files stored on the UIC network share. It uses AI-powered document analysis while maintaining strict HIPAA compliance through automated PII scrubbing and secure data handling.

### Key Features

- **🔒 HIPAA-Compliant**: Automated PII detection and redaction using Microsoft Presidio
- **📁 Drill-Down Navigation**: Intuitive year → patient → files selection workflow
- **🤖 AI-Powered**: RAG-based report generation using Azure OpenAI
- **🔐 Secure SMB Access**: Direct integration with UIC file shares
- **📊 Interactive UI**: Clean Streamlit interface with session management
- **🔍 Semantic Search**: ChromaDB vector store for intelligent document retrieval

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│              (src/ui/app.py - User Interface)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SMB File Explorer                          │
│         (src/ingestion/smb_explorer.py - File Access)       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ list_years() │→ │list_patients()│→ │get_patient_  │     │
│  │              │  │               │  │    files()   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PII Scrubber                              │
│       (src/ingestion/scrubber.py - HIPAA Compliance)        │
│                                                              │
│  Presidio Analyzer → Entity Detection → Anonymization       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Vector Store                               │
│        (src/rag/vector_store.py - Document Embeddings)      │
│                                                              │
│  ChromaDB → Semantic Search → Context Retrieval             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Azure OpenAI                                │
│              (Report Generation - Coming Soon)               │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python**: 3.9 or higher
- **Network Access**: UIC VPN connection to access `uicfs.server.uic.edu`
- **Credentials**: UIC domain username and password
- **Azure OpenAI**: API key and endpoint (for report generation)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Clinical report"
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Language Model

The PII scrubber requires spaCy's English language model:

```bash
python -m spacy download en_core_web_lg
```

### 5. Configure Environment Variables

Copy the template and add your credentials:

```bash
cp .env.template .env
```

Edit `.env` with your credentials:

```bash
# SMB Connection
SMB_SERVER=uicfs.server.uic.edu
SMB_SHARE=AHS-ATUSharedUIC
SMB_BASE_PATH=Services/CA/AE Digital Files
SMB_USERNAME=your_uic_username
SMB_PASSWORD=your_uic_password
SMB_DOMAIN=uic

# Azure OpenAI (for report generation)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

**⚠️ SECURITY WARNING**: Never commit the `.env` file to version control! It's already in `.gitignore`.

## 🎯 Usage

### Starting the Application

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Run the Streamlit app
streamlit run src/ui/app.py
```

The application will open in your browser at `http://localhost:8501`

### User Workflow

1. **Select Fiscal Year**
   - Choose from available fiscal years (e.g., "FY 25", "FY 24")
   - Click "Next: Select Patient"

2. **Select Patient**
   - Choose patient from dropdown list
   - System displays count of available documents
   - Click "Next: Review Files & Generate Report"

3. **Generate Report**
   - Review list of patient documents (PDFs, DOCX files)
   - Select report type:
     - Full Clinical Summary
     - Progress Notes Summary
     - Assessment Summary
   - Enable/disable PII scrubbing (enabled by default)
   - Click "Generate Report"

4. **Download Report**
   - View generated report in browser
   - Download as Markdown file
   - Generate another report or start over

## 📁 Project Structure

```
Clinical report/
├── src/
│   ├── ingestion/              # Data ingestion and processing
│   │   ├── smb_explorer.py     # SMB file navigation with drill-down
│   │   └── scrubber.py         # PII detection and redaction
│   ├── ui/                     # User interface
│   │   └── app.py              # Streamlit frontend application
│   └── rag/                    # RAG pipeline components
│       └── vector_store.py     # ChromaDB integration
├── config/                     # Configuration files
├── .env.template               # Environment variables template
├── .gitignore                  # Git ignore rules (excludes PHI)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── CLAUDE.md                   # AI assistant guidelines (HIPAA rules)
```

## 🔒 HIPAA Compliance & Security

### PHI Protection

This application handles Protected Health Information (PHI) and implements multiple security layers:

1. **Access Control**
   - SMB authentication using UIC domain credentials
   - No local storage of patient files
   - Session-based access management

2. **PII Scrubbing**
   - Automated detection of 18 HIPAA Safe Harbor identifiers:
     - Names, SSN, Phone numbers, Email addresses
     - Dates (except year), Addresses, Medical record numbers
     - And more...
   - Configurable redaction format: `[PHI-ENTITY_TYPE]`

3. **Secure Logging**
   - Patient names NEVER logged to console or files
   - Only counts and non-identifying metadata in logs
   - All file operations audited without exposing PHI

4. **Data Handling**
   - Patient names displayed ONLY in secure UI elements
   - No PHI in error messages or debug output
   - Vector embeddings stored with restricted access

### Security Best Practices

- ✅ Keep `.env` file secure and never commit to Git
- ✅ Use HIPAA-compliant Azure OpenAI configuration
- ✅ Run application on secure, authorized workstations
- ✅ Close browser tab when finished to clear session
- ✅ Review logs regularly for security issues
- ❌ Never screenshot or share patient information
- ❌ Never run on unsecured networks
- ❌ Never disable PII scrubbing for production reports

## 🔧 Development

### Running Tests

```bash
# Unit tests (coming soon)
pytest tests/

# PII scrubber tests
pytest tests/test_scrubber.py

# SMB explorer tests (requires mock setup)
pytest tests/test_smb_explorer.py
```

### Code Style

This project follows:
- PEP 8 style guidelines
- Type hints where applicable
- Docstrings for all public functions
- Security-first logging (no PHI in logs)

### AI Assistant Guidelines

If you're using AI assistants (GitHub Copilot, Claude Code, etc.) to work on this codebase:

**📖 Read [CLAUDE.md](CLAUDE.md) FIRST** - It contains critical HIPAA compliance rules that AI assistants must follow.

Key rule: **NEVER output patient names or PHI to console/logs**.

## 🧩 Components Deep Dive

### SMB Explorer (`src/ingestion/smb_explorer.py`)

Handles secure navigation of the UIC file share with drill-down functionality:

```python
from src.ingestion.smb_explorer import create_explorer_from_env

explorer = create_explorer_from_env()
with explorer.session():
    years = explorer.list_years()              # ["FY 25", "FY 24", ...]
    patients = explorer.list_patients("FY 25") # [patient names]
    files = explorer.get_patient_files("FY 25", patient_name)
```

### PII Scrubber (`src/ingestion/scrubber.py`)

HIPAA-compliant text anonymization:

```python
from src.ingestion.scrubber import HealthcarePIIScrubber

scrubber = HealthcarePIIScrubber()
result = scrubber.scrub("John Smith's SSN is 123-45-6789")
print(result.scrubbed_text)
# Output: "[PHI-PERSON]'s SSN is [PHI-US_SSN]"
```

### Vector Store (`src/rag/vector_store.py`)

Document embedding and semantic search:

```python
from src.rag.vector_store import create_vector_store

store = create_vector_store()
store.add_documents(chunks)
results = store.query("assessment findings", n_results=5)
```

## 🐛 Troubleshooting

### Connection Issues

**Problem**: Cannot connect to SMB share

**Solutions**:
- Verify UIC VPN is connected
- Check credentials in `.env` file
- Ensure domain is set to `uic`
- Test network access: `ping uicfs.server.uic.edu`

### Import Errors

**Problem**: `ModuleNotFoundError` for packages

**Solutions**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify spaCy model is installed
python -m spacy download en_core_web_lg
```

### Streamlit Issues

**Problem**: Streamlit won't start or shows errors

**Solutions**:
```bash
# Clear Streamlit cache
streamlit cache clear

# Run on different port
streamlit run src/ui/app.py --server.port 8502

# Check for port conflicts
lsof -i :8501
```

### PII Scrubber Not Working

**Problem**: Presidio not detecting entities

**Solutions**:
```bash
# Ensure spaCy model is downloaded
python -m spacy validate

# Reinstall Presidio packages
pip install --upgrade presidio-analyzer presidio-anonymizer
```

## 📊 Current Status

### ✅ Completed Features

- [x] SMB file exploration with drill-down navigation
- [x] Streamlit UI with 3-step workflow
- [x] Session state management
- [x] HIPAA-compliant PII scrubbing
- [x] Vector store integration (ChromaDB)
- [x] Environment configuration
- [x] Security logging framework

### 🚧 In Progress

- [ ] Document text extraction (PDF, DOCX)
- [ ] Azure OpenAI integration
- [ ] RAG pipeline implementation
- [ ] Report generation templates
- [ ] Unit test suite
- [ ] Integration tests

### 🔮 Future Enhancements

- [ ] Multi-user authentication
- [ ] Audit log dashboard
- [ ] Custom report templates
- [ ] Batch report generation
- [ ] Export to multiple formats (PDF, Word)
- [ ] Document versioning tracking

## 📝 License

[Add your license here]

## 👥 Contributors

- **UIC Assistive Technology Unit** - Project sponsor
- [Add contributor names as appropriate]

## 📞 Support

For issues, questions, or contributions:
- Create an issue in this repository
- Contact: [Add contact information]

## ⚠️ Disclaimer

This application handles Protected Health Information (PHI) and must be used in compliance with HIPAA regulations. Users are responsible for ensuring proper authorization and handling of all patient data accessed through this system.

---

**Built with ❤️ for healthcare professionals at UIC ATU**
