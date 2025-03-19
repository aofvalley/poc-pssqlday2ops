import streamlit as st
import pandas as pd
import time
import plotly.express as px
from utils.api import get_workflow_status
from utils.ui import format_job_status

# Título de la página
st.title("📊 Monitoreo de Workflows")

# Recuperar configuración de la API de la sesión
api_base_url = st.session_state.get("api_base_url", "")
function_key = st.session_state.get("function_key", "")

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
        st.rerun()

# Verificar credenciales
if not function_key and api_base_url.startswith("https://"):
    st.warning("⚠️ Se requiere la API Key para obtener información de los workflows. Configúrela en la página principal.")
else:
    # Obtener estado del workflow
    with st.spinner("Obteniendo información de estado..."):
        workflow_status = get_workflow_status(api_base_url, function_key, run_id if run_id else None)
    
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
                            timeline_data = [
                                {
                                    'Paso': step['name'], 
                                    'Inicio': pd.to_datetime(step['started_at']) if step['started_at'] else None,
                                    'Fin': pd.to_datetime(step['completed_at']) if step['completed_at'] else None
                                } 
                                for step in job["steps"] if step['started_at']
                            ]
                            
                            if timeline_data:  # Verificar que hay datos para el gráfico
                                fig = px.timeline(
                                    pd.DataFrame(timeline_data),
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
    else:
        st.error("No se pudo obtener información de los workflows. Verifique la conexión con la API.")
