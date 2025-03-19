import streamlit as st
import requests

def get_health_status(api_base_url, function_key):
    """Obtiene el estado de salud de la API"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": function_key}
        response = requests.get(f"{api_base_url}/dumprestore/api%2Fhealth", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado de salud: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def get_workflow_status(api_base_url, function_key, run_id=None):
    """Obtiene el estado actual del workflow"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": function_key}
        params = {}
        if run_id:
            params["run_id"] = run_id
            
        response = requests.get(
            f"{api_base_url}/dumprestore/api%2Fworkflow%2Fstatus",
            headers=headers,
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado del workflow: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def execute_workflow(api_base_url, function_key, workflow_data):
    """Ejecuta un workflow de backup/restore"""
    try:
        headers = {
            "Ocp-Apim-Subscription-Key": function_key,
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{api_base_url}/dumprestore/api%2Fworkflow%2Fdump-restore",
            headers=headers,
            json=workflow_data,
            timeout=30
        )
        if response.status_code == 202:
            return response.json()
        else:
            st.error(f"Error al ejecutar workflow: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def get_config(api_base_url, function_key):
    """Obtiene la configuración actual de la API"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": function_key}
        response = requests.get(
            f"{api_base_url}/dumprestore/api%2Fconfig",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener configuración: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def get_server_info(subscription_id, resource_group, server_name, api_version, token):
    """Get information about the PostgreSQL server, including available upgrade paths"""
    try:
        # Server info endpoint
        server_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version={api_version}"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            server_url,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener información del servidor: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error al consultar información del servidor: {str(e)}")
        return None
