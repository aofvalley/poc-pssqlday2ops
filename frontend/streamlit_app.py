import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px

# Configuración de la aplicación
st.set_page_config(
    page_title="PostgreSQL Backup & Restore",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Variables de configuración
st.sidebar.title("Configuración de API")
API_BASE_URL = st.sidebar.text_input("API Base URL", "https://pssqlapitest.azurewebsites.net")
FUNCTION_KEY = st.sidebar.text_input("Azure Function Key", "", type="password")

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
    .sidebar-button {
        width: 100%;
        margin-bottom: 10px;
        padding: 10px;
        border-radius: 5px;
        border: none;
        color: #FFFFFF;
        background-color: #34495E;
        cursor: pointer;
    }
    .sidebar-button-selected {
        background-color: #1ABC9C !important;
    }
    .monitoring-card {
        padding: 15px;
        margin-bottom: 20px;
        background-color: #2C3E50;
        border-radius: 5px;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def get_health_status():
    """Obtiene el estado de salud de la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", params={"code": FUNCTION_KEY}, timeout=10)
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
        params = {"code": FUNCTION_KEY}
        if run_id:
            params["run_id"] = run_id
            
        response = requests.get(
            f"{API_BASE_URL}/api/workflow/status",
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
        response = requests.post(
            f"{API_BASE_URL}/api/workflow/dump-restore",
            params={"code": FUNCTION_KEY},
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
        response = requests.get(
            f"{API_BASE_URL}/api/config",
            params={"code": FUNCTION_KEY},
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

# Navegación en la barra lateral con botones personalizados
st.sidebar.title("PostgreSQL Backup & Restore")

# Verificar si se ha proporcionado la Function Key
if not FUNCTION_KEY and API_BASE_URL.startswith("https://"):
    st.sidebar.warning("⚠️ Se requiere la Function Key para conectarse a Azure")

pages = ["Dashboard", "Ejecutar Workflows", "Monitoreo", "Configuración"]
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "Dashboard"

for p in ["Dashboard", "Ejecutar Workflows", "Monitoreo", "Configuración"]:
    if st.sidebar.button(p, key=p):
        st.session_state.selected_page = p

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
        
        # Métricas principales
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

elif page == "Ejecutar Workflows":
    st.title("🚀 Ejecutar Workflow de Backup y Restauración")
    
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
        submit_button = st.form_submit_button("Iniciar Workflow de Backup/Restore")
        
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
        # Usar params para las URLs de documentación
        api_url_with_code = f"{API_BASE_URL}/api/docs"
        openapi_url_with_code = f"{API_BASE_URL}/api/openapi.json"
        
        # Agregar el código de función a las URLs si existe
        if FUNCTION_KEY:
            api_url_with_code += f"?code={FUNCTION_KEY}"
            openapi_url_with_code += f"?code={FUNCTION_KEY}"
        
        st.markdown(f"""
        - **URL Base de la API**: {API_BASE_URL}
        - **URL de Documentación Swagger**: [{API_BASE_URL}/api/docs]({api_url_with_code})
        - **URL de OpenAPI**: [{API_BASE_URL}/api/openapi.json]({openapi_url_with_code})
        """)
        
        st.markdown("---")
        
        st.subheader("Endpoints Disponibles")
        endpoints = [
            {"Endpoint": "/api/health", "Método": "GET", "Descripción": "Verificar estado de salud de la API"},
            {"Endpoint": "/api/config", "Método": "GET", "Descripción": "Obtener configuración actual"},
            {"Endpoint": "/api/workflow/dump-restore", "Método": "POST", "Descripción": "Iniciar workflow de backup/restore"},
            {"Endpoint": "/api/workflow/status", "Método": "GET", "Descripción": "Obtener estado de workflows"}
        ]
        
        st.markdown("**Nota**: Todos los endpoints requieren el parámetro `code` con la Function Key cuando se accede desde Azure.")
        st.table(pd.DataFrame(endpoints))

        # Agregar información de debug para ayudar a diagnosticar problemas
        with st.expander("Información de Depuración"):
            st.code(f"""
API Base URL: {API_BASE_URL}
Function Key configurada: {"Sí" if FUNCTION_KEY else "No"}
Ejemplo de URL completa: {API_BASE_URL}/api/health?code=FUNCTION_KEY_HERE
            """)
    else:
        st.error("No se pudo obtener la configuración. Verifique la conexión con la API y la Function Key.")

# Pie de página
st.markdown("---")
st.markdown("PostgreSQL Backup & Restore Frontend - Powered by Streamlit")

# Fecha de actualización
st.sidebar.markdown("---")
st.sidebar.info(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
