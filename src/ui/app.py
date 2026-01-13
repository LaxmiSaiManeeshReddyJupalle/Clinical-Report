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
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ingestion.mock_explorer import MockSMBExplorer, create_mock_explorer, get_explorer
from src.ingestion.scrubber import PIIScrubber


# =============================================================================
# Page Configuration & Custom Styling
# =============================================================================

st.set_page_config(
    page_title="Clinical Report Generator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern, clean UI
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }

    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Step indicator styling */
    .step-container {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1.5rem 0 2rem 0;
    }

    .step-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        border-radius: 50px;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }

    .step-active {
        background: #2d5a87;
        color: white;
        box-shadow: 0 2px 10px rgba(45, 90, 135, 0.3);
    }

    .step-complete {
        background: #10b981;
        color: white;
    }

    .step-pending {
        background: #f1f5f9;
        color: #64748b;
    }

    .step-connector {
        width: 40px;
        height: 2px;
        background: #e2e8f0;
        align-self: center;
    }

    .step-connector-active {
        background: #10b981;
    }

    /* Card styling */
    .custom-card {
        background: white;
        border-radius: 16px;
        padding: 1.75rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }

    .card-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Selection card */
    .selection-card {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .selection-card:hover {
        border-color: #2d5a87;
        background: #f0f7ff;
    }

    .selection-card-selected {
        border-color: #2d5a87;
        background: #eff6ff;
    }

    /* File list styling */
    .file-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        background: #f8fafc;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #2d5a87;
    }

    .file-icon {
        font-size: 1.25rem;
        margin-right: 0.75rem;
    }

    .file-name {
        font-weight: 500;
        color: #1e293b;
    }

    .file-size {
        color: #64748b;
        font-size: 0.85rem;
        margin-left: auto;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(45, 90, 135, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 12px rgba(45, 90, 135, 0.4);
        transform: translateY(-1px);
    }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.75rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .status-success {
        background: #dcfce7;
        color: #166534;
    }

    .status-warning {
        background: #fef3c7;
        color: #92400e;
    }

    .status-info {
        background: #dbeafe;
        color: #1e40af;
    }

    /* Report preview styling */
    .report-preview {
        background: #fafafa;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
    }

    /* Info box styling */
    .info-box {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-left: 4px solid #2d5a87;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }

    .info-box-title {
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.25rem;
    }

    .info-box-text {
        color: #475569;
        font-size: 0.9rem;
    }

    /* Metric card styling */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2d5a87;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2d5a87 0%, #10b981 100%);
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1e293b;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: #f8fafc;
    }

    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .loading-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'current_step': 1,
        'selected_year': None,
        'selected_patient': None,
        'years_list': None,
        'patients_list': None,
        'patient_files': None,
        'smb_connected': False,
        'explorer': None,
        'using_mock': True,
        'report_generated': False,
        'report_content': None,
        'generation_timing': {},  # Timing info for report generation
        'ollama_client': None,
        'ollama_available': False,
        'ollama_checked': False,
        'use_llm': False,
        'error_message': None
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_to_step(step: int):
    """Reset session state to a specific step."""
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
# LLM Management (Ollama)
# =============================================================================

def check_and_init_ollama():
    """Check if Ollama is available and initialize client with warmup."""
    if st.session_state.ollama_checked:
        return st.session_state.ollama_available

    try:
        from src.rag.ollama_client import create_ollama_client, OllamaLLMAdapter
        ollama = create_ollama_client(model="llama3.1:8b", temperature=0.3)

        if ollama:
            st.session_state.ollama_client = OllamaLLMAdapter(ollama)
            st.session_state.ollama_available = True

            # Warmup: Send a tiny request to pre-load the model into memory
            # This avoids cold-start latency on the first real request
            if not st.session_state.get('ollama_warmed_up', False):
                try:
                    ollama.generate(prompt="Hi", max_tokens=1)
                    st.session_state.ollama_warmed_up = True
                except Exception:
                    pass  # Warmup failed, not critical
        else:
            st.session_state.ollama_client = None
            st.session_state.ollama_available = False
    except Exception:
        st.session_state.ollama_client = None
        st.session_state.ollama_available = False

    st.session_state.ollama_checked = True
    return st.session_state.ollama_available


# =============================================================================
# Connection Management
# =============================================================================

def check_mock_data_exists() -> bool:
    """Check if mock data directory exists."""
    project_root = Path(__file__).parent.parent.parent
    mock_data_path = project_root / "mock_data"
    if mock_data_path.exists():
        fy_folders = [f for f in mock_data_path.iterdir() if f.is_dir() and f.name.upper().startswith("FY")]
        return len(fy_folders) > 0
    return False


def check_smb_credentials_available() -> bool:
    """Check if SMB credentials are configured."""
    required_vars = ['SMB_SERVER', 'SMB_SHARE', 'SMB_USERNAME', 'SMB_PASSWORD']
    return all(os.environ.get(var) for var in required_vars)


@st.cache_resource
def get_file_explorer(use_mock: bool = True):
    """Get or create file explorer instance."""
    if use_mock:
        return create_mock_explorer()
    else:
        try:
            from src.ingestion.smb_explorer import create_explorer_from_env
            return create_explorer_from_env()
        except EnvironmentError:
            return None


def ensure_connection() -> bool:
    """Ensure connection is established."""
    use_mock = not check_smb_credentials_available() or st.session_state.get('force_mock', False)
    st.session_state.using_mock = use_mock

    if st.session_state.explorer is None:
        st.session_state.explorer = get_file_explorer(use_mock=use_mock)

    if st.session_state.explorer is None:
        return False

    if not st.session_state.smb_connected:
        try:
            success = st.session_state.explorer.connect()
            st.session_state.smb_connected = success
            return success
        except Exception:
            return False

    return True


# =============================================================================
# Data Loading Functions
# =============================================================================

def load_years():
    """Load fiscal year folders."""
    if not ensure_connection():
        return []
    try:
        years = st.session_state.explorer.list_years()
        st.session_state.years_list = years
        return years
    except Exception:
        return []


def load_patients(year: str):
    """Load patient folders for selected year."""
    if not ensure_connection():
        return []
    try:
        patients = st.session_state.explorer.list_patients(year)
        st.session_state.patients_list = patients
        return patients
    except Exception:
        return []


def load_patient_files(year: str, patient: str):
    """Load document files for selected patient."""
    if not ensure_connection():
        return []
    try:
        files = st.session_state.explorer.get_patient_files(year, patient)
        st.session_state.patient_files = files
        return files
    except Exception:
        return []


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render modern application header."""
    st.markdown("""
    <div class="main-header">
        <h1>Clinical Report Generator</h1>
        <p>HIPAA-Compliant RAG System for Clinical Documentation</p>
    </div>
    """, unsafe_allow_html=True)


def render_step_indicator():
    """Render the step progress indicator."""
    current = st.session_state.current_step

    steps = [
        ("1", "Select Year", current >= 1),
        ("2", "Select Patient", current >= 2),
        ("3", "Generate Report", current >= 3)
    ]

    cols = st.columns([1, 0.3, 1, 0.3, 1])

    for i, (num, label, active) in enumerate(steps):
        col_idx = i * 2
        with cols[col_idx]:
            if current > int(num):
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #10b981; color: white; width: 40px; height: 40px;
                         border-radius: 50%; display: inline-flex; align-items: center;
                         justify-content: center; font-weight: 600; margin-bottom: 0.5rem;">
                        ✓
                    </div>
                    <div style="color: #10b981; font-weight: 500; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            elif current == int(num):
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #2d5a87; color: white; width: 40px; height: 40px;
                         border-radius: 50%; display: inline-flex; align-items: center;
                         justify-content: center; font-weight: 600; margin-bottom: 0.5rem;
                         box-shadow: 0 2px 10px rgba(45, 90, 135, 0.3);">
                        {num}
                    </div>
                    <div style="color: #2d5a87; font-weight: 600; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="background: #e2e8f0; color: #94a3b8; width: 40px; height: 40px;
                         border-radius: 50%; display: inline-flex; align-items: center;
                         justify-content: center; font-weight: 600; margin-bottom: 0.5rem;">
                        {num}
                    </div>
                    <div style="color: #94a3b8; font-weight: 500; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # Add connector line between steps
        if i < len(steps) - 1:
            with cols[col_idx + 1]:
                color = "#10b981" if current > int(num) else "#e2e8f0"
                st.markdown(f"""
                <div style="display: flex; align-items: center; height: 40px; margin-top: 0;">
                    <div style="width: 100%; height: 3px; background: {color}; border-radius: 2px;"></div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


def render_step_1():
    """Step 1: Select Fiscal Year."""
    # Load years if not cached
    if st.session_state.years_list is None:
        with st.spinner("Loading fiscal years..."):
            load_years()

    years = st.session_state.years_list or []

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span>📅</span> Select Fiscal Year
            </div>
        """, unsafe_allow_html=True)

        if not years:
            st.warning("No fiscal year folders found.")
            if st.button("🔄 Retry Connection", use_container_width=True):
                st.session_state.smb_connected = False
                st.session_state.years_list = None
                st.rerun()
        else:
            st.markdown(f"""
            <div class="info-box">
                <div class="info-box-title">Available Records</div>
                <div class="info-box-text">Found {len(years)} fiscal year(s) with patient records</div>
            </div>
            """, unsafe_allow_html=True)

            selected = st.selectbox(
                "Choose a fiscal year to browse",
                options=["Select a fiscal year..."] + years,
                index=0 if st.session_state.selected_year is None else years.index(st.session_state.selected_year) + 1,
                label_visibility="collapsed"
            )

            if selected and selected != "Select a fiscal year..." and selected != st.session_state.selected_year:
                st.session_state.selected_year = selected
                st.session_state.patients_list = None
                st.session_state.selected_patient = None
                st.session_state.patient_files = None

            st.markdown("<br>", unsafe_allow_html=True)

            if st.session_state.selected_year:
                if st.button("Continue to Patient Selection →", type="primary", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_step_2():
    """Step 2: Select Patient."""
    if st.session_state.patients_list is None:
        with st.spinner("Loading patient records..."):
            load_patients(st.session_state.selected_year)

    patients = st.session_state.patients_list or []

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Back button
        if st.button("← Back to Year Selection"):
            reset_to_step(1)
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="custom-card">
            <div class="card-header">
                <span>👤</span> Select Patient
            </div>
            <div style="margin-bottom: 1rem;">
                <span class="status-badge status-info">📅 {st.session_state.selected_year}</span>
            </div>
        """, unsafe_allow_html=True)

        if not patients:
            st.warning("No patient folders found in selected fiscal year.")
        else:
            st.markdown(f"""
            <div class="info-box">
                <div class="info-box-title">Patient Records</div>
                <div class="info-box-text">Found {len(patients)} patient record(s) in {st.session_state.selected_year}</div>
            </div>
            """, unsafe_allow_html=True)

            selected = st.selectbox(
                "Choose a patient",
                options=["Select a patient..."] + patients,
                index=0 if st.session_state.selected_patient is None else (
                    patients.index(st.session_state.selected_patient) + 1
                    if st.session_state.selected_patient in patients else 0
                ),
                label_visibility="collapsed"
            )

            if selected and selected != "Select a patient..." and selected != st.session_state.selected_patient:
                st.session_state.selected_patient = selected
                st.session_state.patient_files = None

            st.markdown("<br>", unsafe_allow_html=True)

            if st.session_state.selected_patient:
                if st.button("Continue to Report Generation →", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_step_3():
    """Step 3: Generate Report."""
    if st.session_state.patient_files is None:
        with st.spinner("Loading patient documents..."):
            load_patient_files(
                st.session_state.selected_year,
                st.session_state.selected_patient
            )

    files = st.session_state.patient_files or []

    # Back button
    col_back, col_spacer = st.columns([1, 3])
    with col_back:
        if st.button("← Back to Patient Selection"):
            reset_to_step(2)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content area
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span>📋</span> Report Configuration
            </div>
        """, unsafe_allow_html=True)

        # Current selection badges
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <span class="status-badge status-info" style="margin-right: 0.5rem;">📅 {st.session_state.selected_year}</span>
            <span class="status-badge status-success">👤 {st.session_state.selected_patient}</span>
        </div>
        """, unsafe_allow_html=True)

        # Report type selection
        st.markdown("**Report Type**")
        report_type = st.selectbox(
            "Report Type",
            options=[
                "Full Clinical Summary",
                "Progress Notes Summary",
                "Assessment Summary",
                "Medication Review",
                "Discharge Summary"
            ],
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # PII Scrubbing option
        include_scrubbed = st.checkbox(
            "🔒 Apply PII Scrubbing",
            value=True,
            help="Redact patient names and identifiers from output"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # LLM Options
        st.markdown("**AI Synthesis**")
        ollama_available = check_and_init_ollama()

        if ollama_available:
            st.session_state.use_llm = st.checkbox(
                "🤖 Use Local AI for Report Generation",
                value=st.session_state.use_llm,
                help="Generate narrative summaries using local Ollama LLM"
            )

            if st.session_state.use_llm:
                # Model selection for speed vs quality
                try:
                    from src.rag.ollama_client import create_ollama_client, OllamaLLMAdapter
                    temp_client = create_ollama_client()
                    if temp_client:
                        available_models = temp_client.list_models()
                        if available_models:
                            # Define model options with speed info
                            model_info = {
                                'llama3.2:3b': '⚡ Fast (~30-45s)',
                                'llama3.1:8b': '⚖️ Balanced (~60-90s)',
                                'llama3.2:1b': '🚀 Fastest (~15-20s)',
                            }

                            current_model = st.session_state.get('selected_model', 'llama3.1:8b')
                            if current_model not in available_models and available_models:
                                current_model = available_models[0]

                            # Create display names
                            model_options = []
                            for m in available_models:
                                speed_info = model_info.get(m, '')
                                display = f"{m} {speed_info}" if speed_info else m
                                model_options.append((m, display))

                            selected_idx = next((i for i, (m, _) in enumerate(model_options) if m == current_model), 0)

                            selected_display = st.selectbox(
                                "Select Model",
                                options=[d for _, d in model_options],
                                index=selected_idx,
                                help="Smaller models are faster but may produce less detailed reports"
                            )

                            # Extract actual model name from display
                            selected_model = next((m for m, d in model_options if d == selected_display), available_models[0])

                            if selected_model != st.session_state.get('selected_model'):
                                new_client = create_ollama_client(model=selected_model)
                                if new_client:
                                    st.session_state.ollama_client = OllamaLLMAdapter(new_client)
                                    st.session_state.selected_model = selected_model

                            st.markdown(f"""
                            <div style="background: #dcfce7; padding: 0.75rem 1rem; border-radius: 8px; margin-top: 0.5rem;">
                                <span style="color: #166534; font-weight: 500;">✓ Using {selected_model}</span>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception:
                    st.markdown("""
                    <div style="background: #dcfce7; padding: 0.75rem 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        <span style="color: #166534; font-weight: 500;">✓ AI synthesis enabled</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #fef3c7; padding: 0.75rem 1rem; border-radius: 8px;">
                <span style="color: #92400e; font-weight: 500;">⚠️ Local AI not available</span>
                <p style="color: #92400e; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                    Install Ollama and pull llama3.1:8b to enable AI synthesis
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Generate button
        st.markdown("<br>", unsafe_allow_html=True)

        if files:
            if st.button("🚀 Generate Report", type="primary", use_container_width=True):
                generate_report(files, report_type, include_scrubbed)

    with col_right:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span>📁</span> Patient Documents
            </div>
        """, unsafe_allow_html=True)

        if not files:
            st.warning("No documents found for this patient.")
        else:
            st.markdown(f"""
            <div style="background: #f0f7ff; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <span style="color: #1e3a5f; font-weight: 500;">{len(files)} documents available</span>
            </div>
            """, unsafe_allow_html=True)

            for file in files:
                file_size_kb = file['size'] / 1024
                icon = "📄" if file['extension'] == '.pdf' else "📝"
                st.markdown(f"""
                <div class="file-item">
                    <span class="file-icon">{icon}</span>
                    <span class="file-name">{file['name']}</span>
                    <span class="file-size">{file_size_kb:.1f} KB</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Display generated report
    if st.session_state.report_generated and st.session_state.report_content:
        st.markdown("<br>", unsafe_allow_html=True)
        render_report_display()


def render_report_display():
    """Render the generated report in a nice format."""
    # Get timing info if available
    timing = st.session_state.get('generation_timing', {})
    total_time = timing.get('total_time', 0)
    ingestion_time = timing.get('ingestion_time', 0)
    llm_time = timing.get('llm_time', 0)

    # Success banner with scroll notification
    st.markdown(f"""
    <div style="background: #dcfce7; padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <span style="color: #166534; font-weight: 600; font-size: 1.1rem;">✓ Report Generated Successfully</span>
            <span style="color: #166534; font-size: 0.9rem;">⏱️ Total time: {total_time:.1f}s</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scroll notification - prominent alert
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center; animation: pulse 2s infinite;">
        <span style="color: white; font-weight: 600; font-size: 1rem;">
            👇 Scroll down to view the full report and download options 👇
        </span>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.85; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Timing breakdown in expandable section
    if total_time > 0:
        with st.expander("⏱️ Generation Time Breakdown", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="background: #f0f7ff; padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #2d5a87;">{ingestion_time:.1f}s</div>
                    <div style="font-size: 0.85rem; color: #64748b;">Document Processing</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">(PII scrubbing, chunking)</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #92400e;">{llm_time:.1f}s</div>
                    <div style="font-size: 0.85rem; color: #64748b;">LLM Generation</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">(llama3.1:8b)</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="background: #dcfce7; padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #166534;">{total_time:.1f}s</div>
                    <div style="font-size: 0.85rem; color: #64748b;">Total Time</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">(end-to-end)</div>
                </div>
                """, unsafe_allow_html=True)

            # Speed suggestions
            st.markdown("---")
            st.markdown("**💡 Tips to Reduce Generation Time:**")
            st.markdown("""
            1. **Use a smaller model**: Try `llama3.2:3b` for faster inference (~2-3x speedup)
            2. **GPU acceleration**: If you have an NVIDIA GPU, Ollama will use it automatically
            3. **Reduce context**: Currently using 5 chunks - could reduce to 3 for faster generation
            4. **Use quantized models**: `llama3.1:8b-q4_0` is faster than the default quantization
            5. **Disable PII scrubbing**: Presidio analysis adds ~5-10s (not recommended for production)
            """)

            # Quick model switch suggestion
            if llm_time > 30:
                st.warning(f"""
                ⚠️ LLM generation took {llm_time:.0f}s. Consider switching to a faster model:
                ```bash
                ollama pull llama3.2:3b
                ```
                Then update the model in the code or add a model selector in the UI.
                """)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        st.download_button(
            label="📥 Download Report",
            data=st.session_state.report_content,
            file_name=f"clinical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with col3:
        if st.button("🔄 Generate New Report", use_container_width=True):
            reset_to_step(1)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Report preview
    st.markdown("""
    <div class="custom-card">
        <div class="card-header">
            <span>📋</span> Report Preview
        </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state.report_content)

    st.markdown("</div>", unsafe_allow_html=True)


def generate_report(files: list, report_type: str, scrub_pii: bool):
    """Generate the clinical report using RAG pipeline."""
    import time
    from src.rag.vector_store import ClinicalVectorStore, DocumentIngestionPipeline
    from src.rag.retriever import ReportGenerator, ClinicalRetriever, ReportType

    report_type_map = {
        "Full Clinical Summary": ReportType.FULL_SUMMARY,
        "Progress Notes Summary": ReportType.PROGRESS_SUMMARY,
        "Assessment Summary": ReportType.ASSESSMENT_SUMMARY,
        "Medication Review": ReportType.MEDICATION_REVIEW,
        "Discharge Summary": ReportType.DISCHARGE_SUMMARY
    }

    rag_report_type = report_type_map.get(report_type, ReportType.FULL_SUMMARY)

    # Timing dictionary to track each phase
    timing = {
        'total_start': time.time(),
        'ingestion_time': 0,
        'retrieval_time': 0,
        'llm_time': 0,
        'total_time': 0
    }

    # Progress container
    progress_container = st.empty()
    timer_container = st.empty()

    try:
        with progress_container.container():
            st.markdown("""
            <div style="background: #eff6ff; padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚙️</div>
                <div style="color: #1e3a5f; font-weight: 600;">Processing Documents...</div>
            </div>
            """, unsafe_allow_html=True)

        # Phase 1: Document Ingestion
        ingestion_start = time.time()

        # Create vector store
        vector_store = ClinicalVectorStore(
            persist_dir=None,
            collection_name="patient_session"
        )

        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            vector_store=vector_store,
            scrub_pii=scrub_pii,
            chunk_size=800,
            chunk_overlap=100
        )

        # Ingest documents
        progress_bar = st.progress(0, text="Processing documents...")
        total_files = len(files)
        chunks_ingested = 0

        for i, file_info in enumerate(files):
            file_path = file_info['path']
            result = pipeline.ingest_document(
                file_path,
                additional_metadata={
                    'patient_id': st.session_state.selected_patient,
                    'fiscal_year': st.session_state.selected_year
                }
            )
            if result['success']:
                chunks_ingested += result['chunks_added']

            progress_bar.progress(
                (i + 1) / total_files,
                text=f"Processed {i + 1}/{total_files} documents..."
            )

        timing['ingestion_time'] = time.time() - ingestion_start

        # Phase 2: Retrieval & LLM Generation
        progress_bar.progress(1.0, text="Generating report with AI... (this may take 1-2 minutes)")

        # Update status with elapsed time
        with timer_container.container():
            st.markdown(f"""
            <div style="background: #fef3c7; padding: 1rem; border-radius: 8px; text-align: center; margin-top: 1rem;">
                <span style="color: #92400e; font-weight: 500;">⏱️ Document processing: {timing['ingestion_time']:.1f}s | Now generating with AI...</span>
            </div>
            """, unsafe_allow_html=True)

        retrieval_start = time.time()

        # Create RAG system
        retriever = ClinicalRetriever(vector_store)

        llm_client = None
        if st.session_state.use_llm and st.session_state.ollama_client:
            llm_client = st.session_state.ollama_client

        generator = ReportGenerator(retriever, llm_client=llm_client)

        # Generate report (this is where most time is spent)
        llm_start = time.time()
        report = generator.generate_report(
            query="comprehensive clinical summary including diagnosis treatment progress medications",
            report_type=rag_report_type,
            patient_id=st.session_state.selected_patient
        )
        timing['llm_time'] = time.time() - llm_start
        timing['retrieval_time'] = time.time() - retrieval_start - timing['llm_time']

        # Calculate total time
        timing['total_time'] = time.time() - timing['total_start']

        # Build report content with timing info
        report_content = f"""# Clinical Report

**Report Type:** {report_type}
**Patient:** {st.session_state.selected_patient}
**Fiscal Year:** {st.session_state.selected_year}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Documents Analyzed:** {len(files)}
**Document Chunks Used:** {report.context_used}
**PII Scrubbing:** {'Enabled' if scrub_pii else 'Disabled'}

---

{report.content}

---

## Source Documents

"""
        for source in report.sources:
            report_content += f"- {source}\n"

        report_content += f"""
---

*Report generated using RAG pipeline with {chunks_ingested} document chunks.*
"""

        st.session_state.report_generated = True
        st.session_state.report_content = report_content
        st.session_state.generation_timing = timing

        # Clear progress indicators
        progress_container.empty()
        progress_bar.empty()
        timer_container.empty()

        st.rerun()

    except Exception as e:
        import traceback
        progress_container.empty()
        timer_container.empty()
        st.error(f"Error generating report: {type(e).__name__}")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        st.session_state.report_generated = False


def render_sidebar():
    """Render minimal sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem;">
            <h3 style="color: #1e3a5f; margin-bottom: 1rem;">System Status</h3>
        </div>
        """, unsafe_allow_html=True)

        # Connection status
        if st.session_state.smb_connected:
            if st.session_state.using_mock:
                st.info("🔵 Development Mode")
            else:
                st.success("🟢 Connected to SMB")
        else:
            st.warning("🟡 Not Connected")

        st.markdown("---")

        # Quick actions
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.smb_connected = False
            st.session_state.years_list = None
            st.session_state.patients_list = None
            st.cache_resource.clear()
            st.rerun()

        if st.button("🏠 Start Over", use_container_width=True):
            reset_to_step(1)
            st.rerun()

        # Generate mock data if needed
        if st.session_state.using_mock and not check_mock_data_exists():
            st.markdown("---")
            if st.button("📦 Generate Test Data", use_container_width=True):
                with st.spinner("Generating..."):
                    from src.ingestion.mock_data_generator import create_mock_data
                    create_mock_data()
                    st.session_state.smb_connected = False
                    st.session_state.years_list = None
                    st.rerun()

        st.markdown("---")

        st.markdown("""
        <div style="padding: 0.5rem; font-size: 0.8rem; color: #64748b;">
            <strong>UIC ATU Clinical Report Generator</strong><br>
            HIPAA-Compliant RAG System
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    init_session_state()

    render_header()
    render_step_indicator()
    render_sidebar()

    # Show any errors
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    # Route to current step
    if st.session_state.current_step == 1:
        render_step_1()
    elif st.session_state.current_step == 2:
        render_step_2()
    elif st.session_state.current_step == 3:
        render_step_3()


if __name__ == "__main__":
    main()
