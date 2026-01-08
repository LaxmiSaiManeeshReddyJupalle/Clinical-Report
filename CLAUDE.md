# Claude Code Guidelines for UIC ATU Clinical Report Generator

## CRITICAL HIPAA COMPLIANCE RULES

### Patient Data Handling

1. **NEVER output raw patient names in the CLI**
   - Patient folder names contain real patient names
   - Only display patient names in Streamlit UI elements (dropdowns, text displays)
   - Never use `print()`, `logging.info()`, or any console output with patient names
   - Never include patient names in error messages or debug output

2. **NEVER log Protected Health Information (PHI)**
   - File names may contain patient identifiers
   - Document contents contain clinical PHI
   - Log only counts, types, and non-identifying metadata
   - Example - WRONG: `logger.info(f"Processing patient: {patient_name}")`
   - Example - RIGHT: `logger.info("Processing patient record")`

3. **PII Scrubbing Requirements**
   - All text output from documents must pass through `PIIScrubber`
   - Use `HealthcarePIIScrubber` for clinical documents (HIPAA Safe Harbor)
   - Never display unscrubbed document content outside the secure UI

## Project Structure

```
Clinical report/
├── src/
│   ├── ingestion/      # SMB access and document processing
│   │   ├── smb_explorer.py   # Drill-down file navigation
│   │   └── scrubber.py       # PII detection and redaction
│   ├── ui/             # Streamlit frontend
│   │   └── app.py            # Main application
│   └── rag/            # Vector DB and retrieval
├── config/             # Configuration files
├── .env                # Environment variables (DO NOT COMMIT)
├── .env.template       # Template for environment setup
└── requirements.txt    # Python dependencies
```

## SMB Explorer Usage

The `SMBExplorer` class provides drill-down navigation:

```python
from src.ingestion.smb_explorer import create_explorer_from_env

explorer = create_explorer_from_env()
with explorer.session():
    years = explorer.list_years()           # ["FY 25", "FY 24", ...]
    patients = explorer.list_patients("FY 25")  # [patient names - UI ONLY]
    files = explorer.get_patient_files("FY 25", patient_name)
```

## Streamlit Session State

The app uses session state for navigation:
- `current_step`: 1 (year) → 2 (patient) → 3 (report)
- `selected_year`: Current fiscal year selection
- `selected_patient`: Current patient selection (PHI - UI ONLY)
- `patient_files`: List of documents for selected patient

## Development Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model for Presidio
python -m spacy download en_core_web_lg

# Run the application
streamlit run src/ui/app.py

# Run with specific port
streamlit run src/ui/app.py --server.port 8502
```

## Security Checklist

Before committing any code, verify:

- [ ] No patient names in any `print()` statements
- [ ] No patient names in any `logging.*()` calls
- [ ] No PHI in error messages or exceptions
- [ ] All document text passes through PII scrubber before display
- [ ] `.env` file is in `.gitignore`
- [ ] No hardcoded credentials in source files

## Error Handling

When catching exceptions that might contain PHI:

```python
# WRONG - may expose PHI in error message
except Exception as e:
    logger.error(f"Error: {e}")

# RIGHT - log type only
except Exception as e:
    logger.error(f"Error processing document: {type(e).__name__}")
```

## Testing Notes

- Use mock data that does NOT contain real patient information
- Create test fixtures with synthetic names and data
- Never use production SMB share for testing
