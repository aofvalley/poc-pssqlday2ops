import streamlit as st
import requests
from utils.api import execute_workflow, get_server_info
from utils.auth import get_azure_token
from utils.config import load_secrets

# Título de la página
st.title("🛠️ Operaciones Day-2 PostgreSQL")

# Recuperar configuración de la API de la sesión
api_base_url = st.session_state.get("api_base_url", "")
function_key = st.session_state.get("function_key", "")
secrets = load_secrets()

# Inicializar el estado de selección de operación si no existe
if 'selected_operation' not in st.session_state:
    st.session_state.selected_operation = None

st.markdown("""
Seleccione la operación que desea realizar en sus servidores PostgreSQL Flexible. 
Las operaciones Day-2 son aquellas que se realizan durante el ciclo de vida operativo de las bases de datos.
""")

# Operation selection buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresco de Entornos", key="btn_refresh", 
                type="primary" if st.session_state.selected_operation == "refresh" else "secondary", 
                use_container_width=True):
        st.session_state.selected_operation = "refresh" if st.session_state.selected_operation != "refresh" else None
        st.rerun()

with col2:
    if st.button("⬆️ Version Upgrade", key="btn_upgrade", 
                type="primary" if st.session_state.selected_operation == "upgrade" else "secondary", 
                use_container_width=True):
        st.session_state.selected_operation = "upgrade" if st.session_state.selected_operation != "upgrade" else None
        st.rerun()

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
                    result = execute_workflow(api_base_url, function_key, workflow_data)
                
                if result:
                    st.success(result["message"])
                    st.markdown(f"[Ver Workflow en GitHub]({result['workflowUrl']})")
                    
                    # Guardar el workflow_id en la sesión para monitoreo automático
                    if "workflowUrl" in result:
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
            token = get_azure_token(secrets)
            if token:
                st.success("Conexión a Azure API disponible. Token obtenido correctamente.")
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
                token = get_azure_token(secrets)
                
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
                        upgrade_url = f"{api_base_url}/major/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version={api_version}"
                    
                    # Prepare headers with Azure token
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    
                    # Add API Management subscription key if using custom gateway
                    if endpoint_type == "Custom API Gateway" and function_key:
                        headers["Ocp-Apim-Subscription-Key"] = function_key
                    
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
