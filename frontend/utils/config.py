import streamlit as st
import os
import json
from datetime import datetime

@st.cache_resource
def load_secrets():
    """Cargar configuración desde archivo secrets.json"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        parent_parent_dir = os.path.dirname(parent_dir)
        secrets_path = os.path.join(parent_parent_dir, "secrets.json")
        
        with open(secrets_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading secrets: {str(e)}")
        return {}

def get_api_config():
    """Obtener configuración de API desde session_state"""
    return {
        "api_base_url": st.session_state.get("api_base_url", ""),
        "function_key": st.session_state.get("function_key", "")
    }
