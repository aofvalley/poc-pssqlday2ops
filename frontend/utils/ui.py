import streamlit as st
from datetime import datetime

def setup_page_config():
    """Configurar opciones de página de Streamlit"""
    st.set_page_config(
        page_title="PostgreSQL Backup & Restore",
        page_icon="🐘",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    """Aplicar estilos CSS personalizados"""
    st.markdown("""
    <style>
        .status-healthy {
            background-color: #14452f;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #27AE60;
            color: #FFFFFF;
        }
        .status-degraded {
            background-color: #5D4037;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #F39C12;
            color: #FFFFFF;
        }
        .status-error {
            background-color: #641E16;
            padding: 10px;
            border-radius: 5px;
            border-left: 5px solid #E74C3C;
            color: #FFFFFF;
        }
        .job-success {
            color: #27AE60;
            font-weight: bold;
        }
        .job-failure {
            color: #E74C3C;
            font-weight: bold;
        }
        .job-in-progress {
            color: #3498DB;
            font-weight: bold;
        }
        .metric-card {
            background-color: #424242;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            color: #FFFFFF;
        }
        .monitoring-card {
            padding: 15px;
            margin-bottom: 20px;
            background-color: #2C3E50;
            border-radius: 5px;
            color: #FFFFFF;
        }
        .operation-selection {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 5px;
            background-color: #2C3E50;
        }
        .operation-description {
            padding: 10px;
            background-color: rgba(39, 174, 96, 0.1);
            border-radius: 5px;
            margin-top: 5px;
            border-left: 3px solid #27AE60;
        }
        
        /* Specific styles for Day-2 operation buttons only */
        div[data-testid="element-container"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] > button {
            font-size: 1.5rem !important;
            font-weight: bold !important;
        }
        
        /* Green styling for primary button */
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #27AE60 !important;
            border-color: #27AE60 !important;
        }
        
        /* Hover effect for primary button */
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #2ECC71 !important;
            border-color: #2ECC71 !important;
            box-shadow: 0 4px 8px rgba(46, 204, 113, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

def format_status_class(status):
    """Devuelve la clase CSS según el estado"""
    if status == "healthy":
        return "status-healthy"
    elif status == "degraded":
        return "status-degraded"
    else:
        return "status-error"

def format_job_status(status, conclusion):
    """Formatea el estado del trabajo para mostrar con el estilo adecuado"""
    if conclusion == "success":
        return f'<span class="job-success">✓ {conclusion.upper()}</span>'
    elif conclusion in ["failure", "cancelled", "timed_out"]:
        return f'<span class="job-failure">✗ {conclusion.upper()}</span>'
    elif status == "in_progress":
        return f'<span class="job-in-progress">⟳ IN PROGRESS</span>'
    else:
        return f"{status.upper()} - {conclusion or 'N/A'}"
