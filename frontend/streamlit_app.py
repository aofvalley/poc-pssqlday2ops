import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import os
import msal

# Configuración de la aplicación
st.set_page_config(
    page_title="PostgreSQL Backup & Restore",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Variables de configuración
st.sidebar.title("Configuración de API")
API_BASE_URL = st.sidebar.text_input("API Base URL", "https://alfonsodapi.azure-api.net")
FUNCTION_KEY = st.sidebar.text_input("API Subscription Key", "", type="password")

# Load Azure authentication credentials from secrets.json
@st.cache_resource
def load_secrets():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        secrets_path = os.path.join(parent_dir, "secrets.json")
        
        with open(secrets_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading secrets: {str(e)}")
        return {}

secrets = load_secrets()

# Function to get access token for Azure API
def get_azure_token():
    try:
        app = msal.ConfidentialClientApplication(
            client_id=secrets.get("client_id"),
            client_credential=secrets.get("client_secret"),
            authority=f"https://login.microsoftonline.com/{secrets.get('tenant_id')}"
        )
        
        result = app.acquire_token_for_client(scopes=[secrets.get("scope")])
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error(f"Error getting token: {result.get('error_description', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

# Estilos CSS personalizados ajustados para modo oscuro
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
    
    /* Specific styles for Day-2 operation buttons only */
    div[data-testid="element-container"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] > button {
        font-size: 2rem !important;
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
    
    /* Style for operation descriptions */
    .operation-description {
        padding: 10px;
        background-color: rgba(39, 174, 96, 0.1);
        border-radius: 5px;
        margin-top: 5px;
        border-left: 3px solid #27AE60;
    }
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def get_health_status():
    """Obtiene el estado de salud de la API"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": FUNCTION_KEY}
        response = requests.get(f"{API_BASE_URL}/dumprestore/api%2Fhealth", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado de salud: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def get_workflow_status(run_id=None):
    """Obtiene el estado actual del workflow"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": FUNCTION_KEY}
        params = {}
        if run_id:
            params["run_id"] = run_id
            
        response = requests.get(
            f"{API_BASE_URL}/dumprestore/api%2Fworkflow%2Fstatus",
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

def execute_workflow(workflow_data):
    """Ejecuta un workflow de backup/restore"""
    try:
        headers = {
            "Ocp-Apim-Subscription-Key": FUNCTION_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{API_BASE_URL}/dumprestore/api%2Fworkflow%2Fdump-restore",
            headers=headers,
            json=workflow_data,
            timeout=30  # Aumentar timeout para operaciones de ejecución
        )
        if response.status_code == 202:
            return response.json()
        else:
            st.error(f"Error al ejecutar workflow: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def get_config():
    """Obtiene la configuración actual de la API"""
    try:
        headers = {"Ocp-Apim-Subscription-Key": FUNCTION_KEY}
        response = requests.get(
            f"{API_BASE_URL}/dumprestore/api%2Fconfig",
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
            return None
    except Exception as e:
        st.error(f"Error fetching server info: {str(e)}")
        return None

# Navegación en la barra lateral con botones personalizados
st.sidebar.title("PostgreSQL Backup & Restore")

# Verificar si se ha proporcionado la Function Key
if not FUNCTION_KEY and API_BASE_URL.startswith("https://"):
    st.sidebar.warning("⚠️ Se requiere la Function Key para conectarse a Azure")

# Updated navigation menu
pages = ["Dashboard", "Operaciones Day-2", "Monitoreo", "Configuración"]
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "Dashboard"

# Initialize the operation selection state
if 'selected_operation' not in st.session_state:
    st.session_state.selected_operation = None

for p in pages:
    if st.sidebar.button(p, key=p):
        st.session_state.selected_page = p
        if p != "Operaciones Day-2":
            st.session_state.selected_operation = None

page = st.session_state.get("selected_page", "Dashboard")

# Mostrar la página seleccionada
if page == "Dashboard":
    st.title("🐘 PostgreSQL Backup & Restore Dashboard")
    
    with st.spinner("Cargando estado del sistema..."):
        health_data = get_health_status()
    
    if health_data:
        # Mostrar panel con el estado de salud general
        status_class = format_status_class(health_data["status"])
        st.markdown(f"""
        <div class="{status_class}">
            <h3>Estado del Sistema: {health_data["status"].upper()}</h3>
            <p>Versión: {health_data["version"]} | Última actualización: {health_data["timestamp"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas principales - Fix: create 3 columns and unpack into 3 variables
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>Tiempo de Actividad</h3>
                <p style="font-size: 24px;">{} segundos</p>
            </div>
            """.format(health_data["uptime"]), unsafe_allow_html=True)
            
        with col2:
            api_status = "✅ Operativo" if health_data["github_api_status"] == "ok" else "❌ Error"
            st.markdown("""
            <div class="metric-card">
                <h3>API de GitHub</h3>
                <p style="font-size: 24px;">{}</p>
            </div>
            """.format(api_status), unsafe_allow_html=True)
            
        with col3:
            config_status = "✅ Configurado" if health_data["github_config_status"] == "ok" else "❌ Error"
            st.markdown("""
            <div class="metric-card">
                <h3>Configuración</h3>
                <p style="font-size: 24px;">{}</p>
            </div>
            """.format(config_status), unsafe_allow_html=True)
        
        # Detalles adicionales
        st.subheader("Detalles del Sistema")
        
        if "github_api" in health_data["details"]:
            api_details = health_data["details"]["github_api"]
            if "rate_limit" in api_details:
                rate_data = api_details["rate_limit"]
                
                # Crear una gráfica para el límite de tasa de GitHub
                fig = go.Figure()
                
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=rate_data["remaining"],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "GitHub API Rate Limit Remaining"},
                    gauge={
                        'axis': {'range': [0, rate_data["limit"]]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, rate_data["limit"]/3], 'color': "red"},
                            {'range': [rate_data["limit"]/3, 2*rate_data["limit"]/3], 'color': "orange"},
                            {'range': [2*rate_data["limit"]/3, rate_data["limit"]], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': rate_data["limit"]/10
                        }
                    }
                ))
                
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"Límite de peticiones: {rate_data['limit']}")
                with col2:
                    st.info(f"Reinicia en: {rate_data['reset_at']}")
            
            elif "error" in api_details:
                st.error(f"Error de API de GitHub: {api_details['error']}")
                if "message" in api_details:
                    st.error(api_details["message"])
        
        # Información del entorno
        if "environment" in health_data["details"]:
            env_data = health_data["details"]["environment"]
            st.subheader("Entorno de Ejecución")
            st.code(f"""
Python version: {env_data.get('python_version', 'N/A')}
Function runtime: {env_data.get('function_name', 'N/A')}
            """)

elif page == "Operaciones Day-2":
    st.title("🛠️ Operaciones Day-2 PostgreSQL")

    st.markdown("""
    Seleccione la operación que desea realizar en sus servidores PostgreSQL Flexible. 
    Las operaciones Day-2 son aquellas que se realizan durante el ciclo de vida operativo de las bases de datos.
    """)

    # Operation selection buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresco de Entornos", key="btn_refresh", type="primary" if st.session_state.selected_operation == "refresh" else "secondary", use_container_width=True):
            st.session_state.selected_operation = "refresh" if st.session_state.selected_operation != "refresh" else None
            st.experimental_rerun()

    with col2:
        if st.button("⬆️ Version Upgrade", key="btn_upgrade", type="primary" if st.session_state.selected_operation == "upgrade" else "secondary", use_container_width=True):
            st.session_state.selected_operation = "upgrade" if st.session_state.selected_operation != "upgrade" else None
            st.experimental_rerun()

    # Add descriptive cards below the buttons with green styling
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="operation-description">
            <p>Copia bases de datos entre entornos de producción y desarrollo</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="operation-description">
            <p>Actualización de versiones principales de PostgreSQL</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Only show the form if the corresponding operation is selected
    if st.session_state.selected_operation == "refresh":
        st.subheader("🔄 Refresco de Entornos")

        with st.form("workflow_form"):
            st.subheader("Detalles de la Base de Datos")
            
            col1, col2 = st.columns(2)
            with col1:
                pg_host_prod = st.text_input("Host de Producción", placeholder="prod-postgres")
                pg_database = st.text_input("Nombre de la Base de Datos", placeholder="mydb")
                resource_group = st.text_input("Grupo de Recursos", placeholder="rg-production")
            
            with col2:
                pg_host_dev = st.text_input("Host de Desarrollo", placeholder="dev-postgres")
                pg_user = st.text_input("Usuario PostgreSQL", placeholder="postgres")
            
            st.text("Esta operación hará un backup de la base de datos de producción y la restaurará en el entorno de desarrollo.")
            submit_button = st.form_submit_button("Iniciar Refresco de Entornos")
            
            if submit_button:
                if not all([pg_host_prod, pg_host_dev, pg_database, pg_user, resource_group]):
                    st.error("Por favor complete todos los campos requeridos.")
                else:
                    workflow_data = {
                        "pg_host_prod": pg_host_prod,
                        "pg_host_dev": pg_host_dev,
                        "pg_database": pg_database,
                        "pg_user": pg_user,
                        "resource_group": resource_group
                    }
                    
                    with st.spinner("Iniciando workflow..."):
                        result = execute_workflow(workflow_data)
                    
                    if result:
                        st.success(result["message"])
                        st.markdown(f"[Ver Workflow en GitHub]({result['workflowUrl']})")
                        
                        # Guardar el workflow_id en la sesión para monitoreo automático
                        if "workflow_url" in result:
                            st.session_state["last_workflow_url"] = result["workflowUrl"]
                            st.info("Puede ir a la sección de Monitoreo para seguir el estado del workflow.")
        with st.expander("¿Qué es el refresco de entornos?"):
            st.markdown("""
            El refresco de entornos es una operación común en el ciclo de vida de las bases de datos que consiste en:
            
            1. **Backup** - Realizar una copia de seguridad de la base de datos de producción
            2. **Transferencia** - Mover la copia de seguridad al entorno de desarrollo
            3. **Restauración** - Restaurar la base de datos en el entorno de desarrollo
            
            Esta operación es útil para:
            - Mantener entornos de desarrollo sincronizados con producción
            - Pruebas con datos reales pero en entornos seguros
            - Depuración de problemas que solo ocurren con datos de producción
            """)

    elif st.session_state.selected_operation == "upgrade":
        st.subheader("⬆️ PostgreSQL Major Version Upgrade")

        # Add API connectivity check
        check_api_button = st.button("Verificar disponibilidad de API")
        if check_api_button:
            try:
                # Try to check Azure API connectivity
                token = get_azure_token()
                if token:
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    if FUNCTION_KEY:
                        headers["Ocp-Apim-Subscription-Key"] = FUNCTION_KEY
                    
                    response = requests.options(
                        "https://management.azure.com/",
                        headers=headers,
                        timeout=10
                    )
                    st.success(f"Conexión a Azure API disponible. Token obtenido correctamente.")
                else:
                    st.error("No se pudo obtener el token de autenticación para Azure.")
            except Exception as e:
                st.error(f"Error al contactar la API: {str(e)}")

        with st.form("version_upgrade_form"):
            st.subheader("Detalles del Servidor PostgreSQL")
            
            col1, col2 = st.columns(2)
            with col1:
                subscription_id = st.text_input("Subscription ID", placeholder="00000000-0000-0000-0000-000000000000")
                resource_group = st.text_input("Resource Group", placeholder="my-resource-group")
            
            with col2:
                server_name = st.text_input("Server Name", placeholder="my-postgres-server")
                api_version = st.text_input("API Version", value="2024-11-01-preview")
            
            # Add help text about version limitations
            st.info("""
            **Importante:** Las opciones de actualización de versión están limitadas por la versión actual del servidor.
            Solo se pueden realizar actualizaciones a la siguiente versión principal disponible.
            Por ejemplo, de PostgreSQL 12 solo se puede actualizar a PostgreSQL 13.
            """)
            
            # PostgreSQL version options
            pg_versions = ["11", "12", "13", "14", "15", "16"]
            target_version = st.selectbox(
                "Target PostgreSQL Version", 
                pg_versions, 
                index=3,
                help="Solo se puede actualizar a la siguiente versión principal disponible desde la versión actual del servidor."
            )
            
            # Add version format option
            version_format = st.radio(
                "Formato de versión",
                ["Número (ej: 14)", "String con punto (ej: '14.0')"],
                index=0,
                help="Algunos servidores requieren el formato numérico, otros requieren el formato de string con punto decimal."
            )
            
            if version_format == "String con punto (ej: '14.0')":
                target_version = f"{target_version}.0"
            
            # API endpoint selection
            endpoint_type = st.radio(
                "Endpoint Type", 
                ["Azure Management API", "Custom API Gateway"],
                index=0,
                help="Select whether to use Azure Management API directly or through your custom API Gateway"
            )
            
            st.text("Esta operación realizará un Major Version Upgrade en el servidor PostgreSQL Flexible especificado.")
            submit_button = st.form_submit_button("Iniciar Version Upgrade")
            
            if submit_button:
                if not all([subscription_id, resource_group, server_name, target_version]):
                    st.error("Por favor complete todos los campos requeridos.")
                else:
                    # Get Azure token
                    token = get_azure_token()
                    
                    if token:
                        # First, try to get server information to determine current version
                        with st.spinner("Obteniendo información del servidor..."):
                            server_info = get_server_info(subscription_id, resource_group, server_name, api_version, token)
                            
                            if server_info:
                                try:
                                    current_version = server_info.get("properties", {}).get("version", "Unknown")
                                    st.info(f"Versión actual del servidor: {current_version}")
                                    
                                    # Check if requested version is higher than current version
                                    try:
                                        current_ver_num = int(current_version.split('.')[0]) if '.' in current_version else int(current_version)
                                        target_ver_num = int(target_version.split('.')[0]) if '.' in target_version else int(target_version)
                                        
                                        if target_ver_num <= current_ver_num:
                                            st.warning(f"⚠️ La versión seleccionada ({target_version}) no es mayor que la versión actual ({current_version}). La actualización solo se puede realizar a una versión superior.")
                                        elif target_ver_num > current_ver_num + 1:
                                            st.warning(f"⚠️ Solo se recomienda actualizar a la siguiente versión principal ({current_ver_num + 1}). La actualización a {target_version} podría fallar.")
                                    except ValueError:
                                        # If we can't parse versions as numbers, just continue
                                        pass
                                except:
                                    st.warning("No se pudo determinar la versión actual del servidor.")
                            
                        # Prepare request body
                        upgrade_data = {
                            "properties": {
                                "createMode": "Update",
                                "version": target_version
                            }
                        }
                        
                        # Build the API endpoint based on selected endpoint type
                        if endpoint_type == "Azure Management API":
                            # Direct Azure Management API endpoint
                            upgrade_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version={api_version}"
                        else:
                            # Custom API Gateway endpoint
                            upgrade_url = f"{API_BASE_URL}/major/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version={api_version}"
                        
                        # Prepare headers with Azure token
                        headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
                        
                        # Add API Management subscription key if using custom gateway
                        if endpoint_type == "Custom API Gateway" and FUNCTION_KEY:
                            headers["Ocp-Apim-Subscription-Key"] = FUNCTION_KEY
                        
                        # Debug information before making the request
                        with st.expander("Debug Information"):
                            st.markdown("**API URL:**")
                            st.code(upgrade_url)
                            st.markdown("**Request Headers:**")
                            debug_headers = headers.copy()
                            if "Authorization" in debug_headers:
                                debug_headers["Authorization"] = "Bearer [REDACTED]"
                            if "Ocp-Apim-Subscription-Key" in debug_headers:
                                debug_headers["Ocp-Apim-Subscription-Key"] = "[REDACTED]"
                            st.json(debug_headers)
                            st.markdown("**Request Body:**")
                            st.json(upgrade_data)
                            st.markdown("**HTTP Method: PATCH**")
                        
                        with st.spinner("Iniciando Major Version Upgrade usando PATCH..."):
                            try:
                                # Always use PATCH method
                                response = requests.patch(
                                    upgrade_url,
                                    headers=headers,
                                    json=upgrade_data,
                                    timeout=30
                                )
                                
                                st.markdown("**Response Status Code:**")
                                st.info(f"{response.status_code} - {response.reason}")
                                
                                st.markdown("**Response Headers:**")
                                st.json(dict(response.headers))
                                
                                # Handle response based on status code
                                if response.status_code in [200, 201, 202]:
                                    st.success(f"Solicitud de actualización enviada correctamente.")
                                    
                                    # Display operation details
                                    try:
                                        result = response.json()
                                        st.markdown("**Response Body:**")
                                        st.json(result)
                                        
                                        # If there's an operation URL in the response headers
                                        if 'Azure-AsyncOperation' in response.headers:
                                            st.info(f"Operation URL: {response.headers['Azure-AsyncOperation']}")
                                            st.markdown("La actualización de versión puede tardar varias horas. Puede seguir el estado de la operación usando la URL anterior.")
                                    except Exception as json_err:
                                        st.info("La solicitud fue aceptada pero no devolvió detalles en formato JSON válido.")
                                        st.markdown("**Raw Response:**")
                                        st.text(response.text)
                                elif response.status_code == 400:
                                    # Try to parse the error response
                                    try:
                                        error_details = response.json()
                                        error_code = error_details.get("error", {}).get("code", "")
                                        error_message = error_details.get("error", {}).get("message", "")
                                        
                                        if error_code == "ParameterOutOfRange" and "Version" in error_message:
                                            st.error("Error 400: Versión no válida")
                                            st.markdown(f"""
                                            **Error específico:** {error_message}
                                            
                                            **Posibles soluciones:**
                                            1. **Verifique la versión actual del servidor** - Solo puede actualizar a la siguiente versión principal
                                            2. **Pruebe con un formato diferente** - Algunos servidores requieren "14" y otros "14.0"
                                            3. **Consulte la documentación** - Las rutas de actualización de versiones pueden estar limitadas
                                            
                                            **Versiones típicamente disponibles:**
                                            - PostgreSQL 11 → 12
                                            - PostgreSQL 12 → 13
                                            - PostgreSQL 13 → 14
                                            - PostgreSQL 14 → 15
                                            """)
                                            
                                            # Add retry options with different version format
                                            if "." not in target_version:
                                                st.info(f"Intente con el formato con punto decimal: '{target_version}.0'")
                                            else:
                                                st.info(f"Intente con el formato numérico: {target_version.split('.')[0]}")
                                        else:
                                            st.error(f"Error 400: {error_message}")
                                            st.json(error_details)
                                    except:
                                        st.error("Error 400: Bad Request")
                                        st.text(response.text)
                                elif response.status_code == 401:
                                    st.error("Error de autenticación: No autorizado (401)")
                                    st.markdown("""
                                    **Posibles causas:**
                                    - El token de autenticación es inválido o ha expirado
                                    - La aplicación no tiene permisos suficientes para gestionar recursos de PostgreSQL
                                    
                                    **Recomendaciones:**
                                    - Verifica que el registro de aplicación tenga los permisos correctos
                                    - Asegúrate que el token tenga el scope correcto
                                    """)
                                elif response.status_code == 403:
                                    st.error("Error de autorización: Prohibido (403)")
                                    st.markdown("""
                                    **Posibles causas:**
                                    - La aplicación no tiene el rol necesario en el recurso o grupo de recursos
                                    - La suscripción podría tener restricciones que impiden esta operación
                                    
                                    **Recomendaciones:**
                                    - Asigna el rol "Contributor" a la aplicación en el servidor PostgreSQL
                                    - Verifica las políticas de Azure en tu suscripción
                                    """)
                                elif response.status_code == 404:
                                    st.error("Error 404: Recurso no encontrado")
                                    st.markdown("""
                                    **Posibles causas:**
                                    - El servidor PostgreSQL especificado no existe
                                    - La ruta de la API no es correcta
                                    - El grupo de recursos no existe
                                    
                                    **Recomendaciones:**
                                    - Verifica que los nombres del servidor y grupo de recursos sean correctos
                                    - Asegúrate que estás usando la versión correcta de la API
                                    """)
                                else:
                                    st.error(f"Error {response.status_code}: {response.text}")
                                    
                                    # Try to parse error response
                                    try:
                                        error_details = response.json()
                                        st.json(error_details)
                                    except:
                                        st.text(response.text)
                            except Exception as e:
                                st.error(f"Error al realizar la solicitud: {str(e)}")
                    else:
                        st.error("No se pudo obtener el token de autenticación para Azure.")
                        st.info("Verifique que los datos en secrets.json sean correctos y que la aplicación tenga los permisos necesarios.")

            # API Information section
            with st.expander("Información sobre Major Version Upgrade"):
                st.markdown("""
                ### Acerca de los Major Version Upgrades
                
                La actualización de versión principal de PostgreSQL en Azure implica:
                
                - Cambiar a una versión más reciente del motor de base de datos
                - Este proceso puede tardar varias horas dependiendo del tamaño de la base de datos
                - Durante la actualización, el servidor estará disponible pero podría experimentar períodos breves de inactividad
                - Se recomienda realizar esta operación durante períodos de baja actividad
                - La API utiliza el método HTTP **PATCH** para realizar la actualización
                
                ### Consideraciones importantes
                
                - Realice una copia de seguridad completa antes de actualizar
                - Pruebe la actualización en un entorno de desarrollo antes de aplicarla en producción
                - Verifique la compatibilidad de sus aplicaciones con la nueva versión
                - Solo puede actualizar a la siguiente versión principal disponible (por ejemplo, de 13 a 14)
                """)
    else:
        # If no operation selected, show general information
        st.markdown("---")
        st.markdown("""
        ## Opciones Disponibles
        
        Por favor, seleccione una de las operaciones de arriba para continuar.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🔄 Refresco de Entornos
            
            Esta operación permite copiar bases de datos entre entornos:
            - De producción a desarrollo
            - Actualizar entornos de pruebas con datos reales
            - Mantener entornos synchronizados
            """)
        
        with col2:
            st.markdown("""
            ### ⬆️ Version Upgrade
            
            Esta operación permite actualizar la versión principal de PostgreSQL:
            - Actualizar a versiones más recientes del motor
            - Obtener nuevas características y mejoras de rendimiento
            - Mantener la compatibilidad y el soporte
            """)

elif page == "Monitoreo":
    st.title("📊 Monitoreo de Workflows")
    
    # Opción para refrescar automáticamente
    auto_refresh = st.checkbox("Refrescar automáticamente cada 10 segundos", value=False)
    
    # Obtener último estado o especificar un run_id
    col1, col2 = st.columns([3, 1])
    with col1:
        run_id = st.text_input("ID de ejecución específica (opcional)", "")
    with col2:
        refresh_button = st.button("Refrescar estado")
    
    if refresh_button or (auto_refresh and "last_refresh" not in st.session_state):
        st.session_state["last_refresh"] = time.time()
    
    if auto_refresh and "last_refresh" in st.session_state:
        # Refrescar cada 10 segundos si está activado
        if time.time() - st.session_state["last_refresh"] >= 10:
            st.session_state["last_refresh"] = time.time()
            st.experimental_rerun()
    
    # Obtener estado del workflow
    with st.spinner("Obteniendo información de estado..."):
        workflow_status = get_workflow_status(run_id if run_id else None)
    
    if workflow_status:
        if "message" in workflow_status and workflow_status["message"] == "No workflow runs found":
            st.info("No hay ejecuciones de workflow disponibles.")
        else:
            # Mostrar información del workflow
            st.subheader(f"Workflow: {workflow_status['name']}")
            
            # Estado general con el formato adecuado
            status_class = "job-in-progress" if workflow_status["status"] == "in_progress" else (
                "job-success" if workflow_status["conclusion"] == "success" else "job-failure"
            )
            
            status_text = workflow_status["status"].replace("_", " ").upper()
            conclusion_text = workflow_status["conclusion"].replace("_", " ").upper() if workflow_status["conclusion"] else ""
            status_display = f"{status_text} - {conclusion_text}" if conclusion_text else status_text
            
            st.markdown(f"""
            <div class="monitoring-card">
                <h3 class="{status_class}">{status_display}</h3>
                <p>ID: {workflow_status['id']}</p>
                <p>Iniciado: {workflow_status['created_at']}</p>
                <p>Última actualización: {workflow_status['updated_at']}</p>
                {f"<p>Duración: {workflow_status['duration']['formatted']}</p>" if 'duration' in workflow_status else ""}
                <a href="{workflow_status['html_url']}" target="_blank">Ver en GitHub</a>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar detalles de los trabajos
            if "jobs" in workflow_status and workflow_status["jobs"]:
                st.subheader("Trabajos")
                
                for job in workflow_status["jobs"]:
                    with st.expander(f"{job['name']} - {job['status'].replace('_', ' ').upper()}", expanded=True):
                        st.markdown(f"""
                        **Estado**: {format_job_status(job['status'], job['conclusion'])}  
                        **Iniciado**: {job['started_at'] or 'No iniciado'}  
                        **Completado**: {job['completed_at'] or 'No completado'}  
                        **Duración**: {job['duration'] or 'N/A'}
                        """, unsafe_allow_html=True)
                        
                        # Mostrar los pasos como una tabla
                        if "steps" in job and job["steps"]:
                            step_data = []
                            for step in job["steps"]: 
                                step_data.append({ 
                                    "Paso": step["name"], 
                                    "Estado": step["status"].replace("_", " ").upper(), 
                                    "Resultado": step["conclusion"].replace("_", " ").upper() if step["conclusion"] else "N/A", 
                                    "Duración": step["duration"] or "N/A" 
                                }) 
                            
                            st.dataframe(pd.DataFrame(step_data), use_container_width=True)

                            # Crear gráfico de progresión de los pasos
                            fig = px.timeline(
                                pd.DataFrame([{
                                    'Paso': step['name'], 
                                    'Inicio': pd.to_datetime(step['started_at']) if step['started_at'] else None,
                                    'Fin': pd.to_datetime(step['completed_at']) if step['completed_at'] else None
                                } for step in job["steps"] if step['started_at']]),
                                x_start="Inicio", 
                                x_end="Fin", 
                                y="Paso",
                                color_discrete_sequence=["#3498DB"]
                            )
                            
                            fig.update_layout(
                                title="Línea de Tiempo de Ejecución",
                                xaxis_title="",
                                yaxis_title="",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)

elif page == "Configuración":
    st.title("⚙️ Configuración")
    
    # Verificar si falta la Function Key para Azure
    if not FUNCTION_KEY and API_BASE_URL.startswith("https://"):
        st.warning("⚠️ Se requiere la Function Key para conectarse a Azure. Por favor, ingrésela en la barra lateral.")
    
    with st.spinner("Cargando configuración..."):
        config_data = get_config()
    
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
        api_docs_url = f"{API_BASE_URL}/dumprestore/api%2Fdocs"
        openapi_url = f"{API_BASE_URL}/dumprestore/api%2Fopenapi.json"
        
        st.markdown(f"""
        - **URL Base de la API**: {API_BASE_URL}
        - **URL de Documentación Swagger**: [{api_docs_url}]({api_docs_url})
        - **URL de OpenAPI**: [{openapi_url}]({openapi_url})
        """)
        
        st.markdown("---")
        
        st.subheader("Endpoints Disponibles")
        endpoints = [
            {"Endpoint": "/dumprestore/api/health", "Método": "GET", "Descripción": "Verificar estado de salud de la API"},
            {"Endpoint": "/dumprestore/api/config", "Método": "GET", "Descripción": "Obtener configuración actual"},
            {"Endpoint": "/dumprestore/api/workflow/dump-restore", "Método": "POST", "Descripción": "Iniciar workflow de backup/restore"},
            {"Endpoint": "/dumprestore/api/workflow/status", "Método": "GET", "Descripción": "Obtener estado de workflows"}
        ]
        
        st.markdown("**Nota**: Todos los endpoints requieren el encabezado `Ocp-Apim-Subscription-Key` con la clave de suscripción de API Management.")
        st.table(pd.DataFrame(endpoints))

        # Agregar información de debug para ayudar a diagnosticar problemas
        with st.expander("Información de Depuración"):
            st.code(f"""
API Base URL: {API_BASE_URL}
Function Key configurada: {"Sí" if FUNCTION_KEY else "No"}
Ejemplo de llamada a la API:
    import requests
    headers = {{"Ocp-Apim-Subscription-Key": "YOUR_SUBSCRIPTION_KEY"}}
    response = requests.get("{API_BASE_URL}/dumprestore/api%2Fhealth", headers=headers)
            """)
    else:
        st.error("No se pudo obtener la configuración. Verifique la conexión con la API y la Function Key.")

# Pie de página
st.markdown("---")
st.markdown("PostgreSQL Backup & Restore Frontend - Powered by Streamlit")

# Fecha de actualización
st.sidebar.markdown("---")
st.sidebar.info(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")