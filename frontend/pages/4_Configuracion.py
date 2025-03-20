import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api import get_config

# Título de la página
st.title("⚙️ Configuración")

# Recuperar configuración de la API de la sesión
api_base_url = st.session_state.get("api_base_url", "")
function_key = st.session_state.get("function_key", "")

# Verificar credenciales
if not function_key and api_base_url.startswith("https://"):
    st.warning("⚠️ Se requiere la API Key para obtener información de configuración. Configúrela en la página principal.")
else:
    with st.spinner("Cargando configuración..."):
        config_data = get_config(api_base_url, function_key)
    
    if config_data:
        st.subheader("Configuración de GitHub Actions")
        
        # Mostrar información de configuración en una tabla
        config_items = {
            "Propietario del Repositorio": config_data["github_owner"],
            "Nombre del Repositorio": config_data["github_repo"],
            "ID del Workflow": config_data["github_workflow_id"],
            "Token de GitHub": "Configurado" if config_data["token_loaded"] else "No configurado"
        }
        
        for key, value in config_items.items():
            st.info(f"**{key}**: {value}")
        
        st.markdown("---")
        
        st.subheader("Información de la API")
        # Crear URLs para documentación
        api_docs_url = f"{api_base_url}/dumprestore/api%2Fdocs"
        openapi_url = f"{api_base_url}/dumprestore/api%2Fopenapi.json"
        
        st.markdown(f"""
        - **URL Base de la API**: {api_base_url}
        - **URL de Documentación Swagger**: [{api_docs_url}]({api_docs_url})
        - **URL de OpenAPI**: [{openapi_url}]({openapi_url})
        """)
        
        st.markdown("---")
        
        st.subheader("Endpoints Disponibles")
        endpoints = [
            {"Endpoint": "/dumprestore/api/health", "Método": "GET", "Descripción": "Verificar estado de salud de la API"},
            {"Endpoint": "/dumprestore/api/config", "Método": "GET", "Descripción": "Obtener configuración actual"},
            {"Endpoint": "/dumprestore/api/workflow/dump-restore", "Método": "POST", "Descripción": "Iniciar workflow de backup/restore"},
            {"Endpoint": "/dumprestore/api/workflow/status", "Método": "GET", "Descripción": "Obtener estado de workflows"},
            {"Endpoint": "/major/...", "Método": "PATCH", "Descripción": "Major version upgrade de servidor PSSQL flexible server"}
        ]
        
        st.markdown("**Nota**: Todos los endpoints requieren el encabezado `Ocp-Apim-Subscription-Key` con la clave de suscripción de API Management.")
        st.table(pd.DataFrame(endpoints))

        # Agregar información de debug para ayudar a diagnosticar problemas
        with st.expander("Información de Depuración"):
            st.code(f"""
API Base URL: {api_base_url}
Function Key configurada: {"Sí" if function_key else "No"}
Ejemplo de llamada a la API:
    import requests
    headers = {{"Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY"}}
    response = requests.get("{api_base_url}/dumprestore/api%2Fhealth", headers=headers)
            """)
    else:
        st.error("No se pudo obtener la configuración. Verifique la conexión con la API y la Function Key.")

# Mostrar fecha/hora de la última actualización
st.markdown("---")
st.info(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
