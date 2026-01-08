"""
Streamlit Frontend for UIC ATU Clinical Report Generator

HIPAA-compliant UI with drill-down navigation for patient files.
Patient names are displayed ONLY in secure UI elements, never logged.

Usage:
    streamlit run src/ui/app.py
"""

import streamlit as st
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ingestion.smb_explorer import SMBExplorer, SMBConfig, create_explorer_from_env
from src.ingestion.scrubber import PIIScrubber


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="UIC ATU Clinical Report Generator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        # Navigation state
        'current_step': 1,  # 1=Select Year, 2=Select Patient, 3=Generate Report
        'selected_year': None,
        'selected_patient': None,

        # Cached data (to avoid repeated SMB calls)
        'years_list': None,
        'patients_list': None,
        'patient_files': None,

        # Connection state
        'smb_connected': False,
        'explorer': None,

        # Report state
        'report_generated': False,
        'report_content': None,

        # Error handling
        'error_message': None
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_to_step(step: int):
    """Reset session state to a specific step, clearing dependent data."""
    st.session_state.current_step = step

    if step <= 1:
        st.session_state.selected_year = None
        st.session_state.patients_list = None

    if step <= 2:
        st.session_state.selected_patient = None
        st.session_state.patient_files = None

    st.session_state.report_generated = False
    st.session_state.report_content = None
    st.session_state.error_message = None


# =============================================================================
# SMB Connection Management
# =============================================================================

@st.cache_resource
def get_smb_explorer() -> SMBExplorer:
    """
    Get or create SMB Explorer instance.
    Uses Streamlit's cache to maintain connection across reruns.
    """
    try:
        explorer = create_explorer_from_env()
        return explorer
    except EnvironmentError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please ensure .env file is configured with SMB credentials.")
        return None


def ensure_connection() -> bool:
    """Ensure SMB connection is established."""
    if st.session_state.explorer is None:
        st.session_state.explorer = get_smb_explorer()

    if st.session_state.explorer is None:
        return False

    if not st.session_state.smb_connected:
        try:
            success = st.session_state.explorer.connect()
            st.session_state.smb_connected = success
            return success
        except Exception as e:
            st.session_state.error_message = f"Connection failed: {type(e).__name__}"
            return False

    return True


# =============================================================================
# Data Loading Functions
# =============================================================================

def load_years():
    """Load fiscal year folders from SMB share."""
    if not ensure_connection():
        return []

    try:
        years = st.session_state.explorer.list_years()
        st.session_state.years_list = years
        return years
    except Exception as e:
        st.session_state.error_message = f"Failed to load years: {type(e).__name__}"
        return []


def load_patients(year: str):
    """
    Load patient folders for selected year.
    SECURITY: Patient names displayed in UI only, never logged.
    """
    if not ensure_connection():
        return []

    try:
        patients = st.session_state.explorer.list_patients(year)
        st.session_state.patients_list = patients
        return patients
    except Exception as e:
        st.session_state.error_message = f"Failed to load patient list: {type(e).__name__}"
        return []


def load_patient_files(year: str, patient: str):
    """
    Load document files for selected patient.
    SECURITY: File info displayed in UI only, never logged.
    """
    if not ensure_connection():
        return []

    try:
        files = st.session_state.explorer.get_patient_files(year, patient)
        st.session_state.patient_files = files
        return files
    except Exception as e:
        st.session_state.error_message = f"Failed to load patient files: {type(e).__name__}"
        return []


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render application header."""
    st.title("🏥 UIC ATU Clinical Report Generator")
    st.markdown("---")

    # Progress indicator
    steps = ["Select Year", "Select Patient", "Generate Report"]
    cols = st.columns(3)

    for i, (col, step_name) in enumerate(zip(cols, steps), 1):
        with col:
            if i < st.session_state.current_step:
                st.success(f"✅ Step {i}: {step_name}")
            elif i == st.session_state.current_step:
                st.info(f"🔵 Step {i}: {step_name}")
            else:
                st.markdown(f"⚪ Step {i}: {step_name}")


def render_error():
    """Display any error messages."""
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        if st.button("Dismiss Error"):
            st.session_state.error_message = None
            st.rerun()


def render_step_1():
    """Step 1: Select Fiscal Year."""
    st.subheader("📅 Step 1: Select Fiscal Year")

    # Load years if not cached
    if st.session_state.years_list is None:
        with st.spinner("Loading fiscal years..."):
            load_years()

    years = st.session_state.years_list or []

    if not years:
        st.warning("No fiscal year folders found. Please check SMB connection.")
        if st.button("Retry Connection"):
            st.session_state.smb_connected = False
            st.session_state.years_list = None
            st.rerun()
        return

    # Year selection dropdown
    selected = st.selectbox(
        "Select Fiscal Year",
        options=[""] + years,
        index=0 if st.session_state.selected_year is None else years.index(st.session_state.selected_year) + 1,
        help="Choose the fiscal year containing the patient records"
    )

    if selected and selected != st.session_state.selected_year:
        st.session_state.selected_year = selected
        st.session_state.patients_list = None  # Clear cached patients
        st.session_state.selected_patient = None
        st.session_state.patient_files = None

    # Navigation button
    if st.session_state.selected_year:
        if st.button("Next: Select Patient →", type="primary"):
            st.session_state.current_step = 2
            st.rerun()


def render_step_2():
    """
    Step 2: Select Patient.
    SECURITY: Patient names displayed in dropdown only, never logged to console.
    """
    st.subheader("👤 Step 2: Select Patient")

    # Show current selection
    st.caption(f"Fiscal Year: **{st.session_state.selected_year}**")

    # Back button
    if st.button("← Back to Year Selection"):
        reset_to_step(1)
        st.rerun()

    # Load patients if not cached
    if st.session_state.patients_list is None:
        with st.spinner("Loading patient records..."):
            load_patients(st.session_state.selected_year)

    patients = st.session_state.patients_list or []

    if not patients:
        st.warning("No patient folders found in selected fiscal year.")
        return

    st.info(f"📁 Found {len(patients)} patient records")

    # Patient selection dropdown
    # SECURITY: Patient names displayed in secure UI element only
    selected = st.selectbox(
        "Select Patient",
        options=[""] + patients,
        index=0 if st.session_state.selected_patient is None else (
            patients.index(st.session_state.selected_patient) + 1
            if st.session_state.selected_patient in patients else 0
        ),
        help="Select the patient to generate a report for"
    )

    if selected and selected != st.session_state.selected_patient:
        st.session_state.selected_patient = selected
        st.session_state.patient_files = None  # Clear cached files

    # Navigation button
    if st.session_state.selected_patient:
        if st.button("Next: Review Files & Generate Report →", type="primary"):
            st.session_state.current_step = 3
            st.rerun()


def render_step_3():
    """
    Step 3: Review files and generate report.
    SECURITY: All PHI displayed in secure UI elements only.
    """
    st.subheader("📄 Step 3: Generate Clinical Report")

    # Show current selections
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Fiscal Year: **{st.session_state.selected_year}**")
    with col2:
        # SECURITY: Patient name in UI element only
        st.caption(f"Patient: **{st.session_state.selected_patient}**")

    # Back button
    if st.button("← Back to Patient Selection"):
        reset_to_step(2)
        st.rerun()

    # Load patient files
    if st.session_state.patient_files is None:
        with st.spinner("Loading patient documents..."):
            load_patient_files(
                st.session_state.selected_year,
                st.session_state.selected_patient
            )

    files = st.session_state.patient_files or []

    if not files:
        st.warning("No supported documents found for this patient.")
        return

    # Display files in expandable section
    with st.expander(f"📁 Patient Documents ({len(files)} files)", expanded=True):
        for file in files:
            file_size_kb = file['size'] / 1024
            icon = "📄" if file['extension'] == '.pdf' else "📝"
            st.markdown(f"{icon} **{file['name']}** ({file_size_kb:.1f} KB)")

    st.markdown("---")

    # Report generation options
    st.subheader("Report Options")

    report_type = st.selectbox(
        "Report Type",
        options=["Full Clinical Summary", "Progress Notes Summary", "Assessment Summary"],
        help="Select the type of report to generate"
    )

    include_scrubbed = st.checkbox(
        "Apply PII Scrubbing to Output",
        value=True,
        help="Redact names and SSNs from the generated report"
    )

    # Generate button
    if st.button("🚀 Generate Report", type="primary"):
        generate_report(files, report_type, include_scrubbed)


def generate_report(files: list, report_type: str, scrub_pii: bool):
    """
    Generate the clinical report from patient files.

    This is a placeholder that will integrate with the RAG pipeline.
    """
    with st.spinner("Generating report... This may take a moment."):
        # Placeholder for actual report generation
        # TODO: Integrate with RAG pipeline

        st.session_state.report_generated = True

        # Mock report content for UI demonstration
        report_content = f"""
# Clinical Report

**Report Type:** {report_type}
**Documents Analyzed:** {len(files)}
**PII Scrubbing:** {'Enabled' if scrub_pii else 'Disabled'}

---

## Summary

This is a placeholder for the generated clinical report.
The actual implementation will:

1. Read documents from the SMB share
2. Extract text content from PDFs and DOCX files
3. Apply PII scrubbing if enabled
4. Generate embeddings and store in ChromaDB
5. Use RAG to generate comprehensive clinical summary
6. Return formatted report

---

## Documents Processed

"""
        for file in files:
            report_content += f"- {file['name']}\n"

        st.session_state.report_content = report_content

    # Display generated report
    if st.session_state.report_generated:
        st.success("✅ Report generated successfully!")

        st.markdown("---")
        st.subheader("Generated Report")

        # Display in a container with copy capability
        st.markdown(st.session_state.report_content)

        # Download button
        st.download_button(
            label="📥 Download Report",
            data=st.session_state.report_content,
            file_name="clinical_report.md",
            mime="text/markdown"
        )

        # Reset button
        if st.button("Generate Another Report"):
            reset_to_step(1)
            st.rerun()


def render_sidebar():
    """Render sidebar with connection status and info."""
    with st.sidebar:
        st.header("System Status")

        # Connection status
        if st.session_state.smb_connected:
            st.success("🟢 Connected to SMB Share")
        else:
            st.warning("🟡 Not Connected")

        st.markdown("---")

        # Quick actions
        st.header("Quick Actions")

        if st.button("🔄 Refresh Connection"):
            st.session_state.smb_connected = False
            st.session_state.years_list = None
            st.session_state.patients_list = None
            st.session_state.patient_files = None
            st.rerun()

        if st.button("🏠 Start Over"):
            reset_to_step(1)
            st.rerun()

        st.markdown("---")

        # Info section
        st.header("About")
        st.markdown("""
        **UIC ATU Clinical Report Generator**

        HIPAA-compliant RAG system for generating
        clinical reports from patient documents.

        *All patient data is handled securely.*
        """)


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Render UI components
    render_header()
    render_sidebar()
    render_error()

    # Route to current step
    if st.session_state.current_step == 1:
        render_step_1()
    elif st.session_state.current_step == 2:
        render_step_2()
    elif st.session_state.current_step == 3:
        render_step_3()


if __name__ == "__main__":
    main()
