import streamlit as st
from utils.config import load_secrets
from utils.ui import setup_page_config, apply_custom_css

# Configurar página
setup_page_config()

# Aplicar estilos CSS personalizados
apply_custom_css()

# Cargar configuración de secretos
secrets = load_secrets()

# Sidebar para configuración global de la API
st.sidebar.title("PostgreSQL Backup & Restore")
st.sidebar.title("Configuración de API")
API_BASE_URL = st.sidebar.text_input("API Base URL", "https://alfonsodapi.azure-api.net")
FUNCTION_KEY = st.sidebar.text_input("API Subscription Key", "", type="password")

# Almacenar en session_state para acceso desde otras páginas
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = API_BASE_URL
else:
    if st.session_state.api_base_url != API_BASE_URL:
        st.session_state.api_base_url = API_BASE_URL

if "function_key" not in st.session_state:
    st.session_state.function_key = FUNCTION_KEY
else:
    if st.session_state.function_key != FUNCTION_KEY:
        st.session_state.function_key = FUNCTION_KEY

# Área de contenido principal en la página de inicio
st.title("🐘 PostgreSQL Backup & Restore")
st.write("Bienvenido a la herramienta de gestión de bases de datos PostgreSQL")

st.markdown("""
Esta aplicación te permite:
- Monitorear el estado de tus servicios PostgreSQL
- Ejecutar operaciones de mantenimiento Day-2
- Gestionar backups y restauraciones entre entornos
- Actualizar versiones de PostgreSQL

Utiliza el menú de navegación de la barra lateral izquierda para acceder a las diferentes funcionalidades.
""")

# Mostrar información de uso
st.info("""
**Instrucciones de uso:**
1. Configura la URL base de la API y la Subscription Key en la barra lateral
2. Navega a las diferentes secciones usando el menú de la izquierda
3. Consulta la sección de Configuración para verificar la conectividad con la API
""")

# Pie de página
st.sidebar.markdown("---")
st.sidebar.info(f"PostgreSQL Backup & Restore Tool")