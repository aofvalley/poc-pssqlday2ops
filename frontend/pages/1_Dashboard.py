import streamlit as st
import plotly.graph_objects as go
from utils.api import get_health_status
from utils.ui import format_status_class

# Título de la página
st.title("🐘 Dashboard de PostgreSQL")

# Recuperar configuración de la API de la sesión
api_base_url = st.session_state.get("api_base_url", "")
function_key = st.session_state.get("function_key", "")

# Verificar credenciales
if not function_key and api_base_url.startswith("https://"):
    st.warning("⚠️ Se requiere la API Key para obtener información del sistema. Configúrela en la página principal.")
else:
    # Obtener estado de salud
    with st.spinner("Cargando estado del sistema..."):
        health_data = get_health_status(api_base_url, function_key)
    
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
            st.markdown(f"""
            <div class="metric-card">
                <h3>Tiempo de Actividad</h3>
                <p style="font-size: 24px;">{health_data["uptime"]} segundos</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            api_status = "✅ Operativo" if health_data["github_api_status"] == "ok" else "❌ Error"
            st.markdown(f"""
            <div class="metric-card">
                <h3>API de GitHub</h3>
                <p style="font-size: 24px;">{api_status}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            config_status = "✅ Configurado" if health_data["github_config_status"] == "ok" else "❌ Error"
            st.markdown(f"""
            <div class="metric-card">
                <h3>Configuración</h3>
                <p style="font-size: 24px;">{config_status}</p>
            </div>
            """, unsafe_allow_html=True)
        
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
    else:
        st.error("No se pudo obtener información del estado del sistema. Verifique la configuración de la API.")
