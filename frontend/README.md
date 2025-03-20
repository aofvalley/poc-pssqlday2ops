# PostgreSQL Backup & Restore Frontend

Este es un frontend de Streamlit para la API de PostgreSQL Backup and Restore que permite ejecutar y monitorear los workflows de backup y restauración, así como realizar operaciones Day-2 en servidores PostgreSQL.

## Estructura del Proyecto

La aplicación Streamlit está organizada siguiendo un patrón modular:

## Requisitos

- Python 3.8+
- Streamlit y otras dependencias listadas en `requirements.txt`
- La API de PostgreSQL Backup and Restore debe estar corriendo

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación Streamlit:
```bash
streamlit run Main.py
```

3. Accede a la aplicación en tu navegador:
```
http://localhost:8501
```

## Funcionalidades

- **Dashboard**: Muestra una visión general del estado del sistema y la API
- **Operaciones Day-2**: Interfaz para ejecutar workflows de refresco de entornos y actualización de versiones
- **Monitoreo**: Visualización detallada del estado de ejecución de los workflows
- **Configuración**: Información sobre la configuración actual de la API

## Configuración

Al iniciar la aplicación, puedes configurar la URL base de la API y la API Subscription Key en la barra lateral.

## Guía Detallada de Uso

### Navegación

La interfaz principal contiene una barra lateral con las siguientes secciones:
- **Inicio/Dashboard**: Página principal con resumen del estado del sistema y la API
- **Operaciones Day-2**: Ejecutar operaciones como refresco de entornos y actualización de versiones
- **Monitoreo de Workflows**: Ver estado y detalles de los workflows en ejecución
- **Configuración**: Ajustes del sistema y detalles de la API

### Dashboard

En el Dashboard encontrarás:
- **Estado del sistema**: Indicador visual del estado de la API y sus componentes
- **Métricas principales**: Tiempo de actividad, estado de GitHub API, configuración
- **GitHub API Rate Limit**: Gráfico con información del límite de peticiones disponible
- **Entorno de ejecución**: Detalles sobre el entorno donde se ejecuta la API

### Operaciones Day-2

#### Refresco de Entornos
1. Selecciona la operación "Refresco de Entornos" haciendo clic en el botón
2. Completa el formulario con los siguientes datos:
   - Host de Producción: Servidor PostgreSQL de origen
   - Host de Desarrollo: Servidor PostgreSQL de destino
   - Nombre de la Base de Datos: Base de datos a copiar
   - Usuario PostgreSQL: Usuario con privilegios suficientes
   - Grupo de Recursos: Grupo de recursos de Azure donde están los servidores
3. Haz clic en "Iniciar Refresco de Entornos" para ejecutar la operación

#### Version Upgrade
1. Selecciona la operación "Version Upgrade" haciendo clic en el botón
2. Completa el formulario con los siguientes datos:
   - Subscription ID: ID de la suscripción de Azure
   - Resource Group: Grupo de recursos donde está el servidor
   - Server Name: Nombre del servidor PostgreSQL Flexible
   - Target PostgreSQL Version: Versión a la que deseas actualizar
   - Endpoint Type: Selecciona entre API de Azure o API Gateway personalizada
3. Haz clic en "Iniciar Version Upgrade" para ejecutar la operación

### Monitoreo de Workflows

La sección de monitoreo permite:
1. **Consultar workflows activos**: Ver una lista de ejecuciones recientes o buscar por ID específico
2. **Refrescar automáticamente**: Activar actualización periódica del estado
3. **Ver detalles de ejecución**: Al consultar un workflow verás:
   - Estado general y URL de GitHub
   - Fecha de inicio y última actualización
   - Duración total de la ejecución
   - Trabajos individuales y sus estados
   - Pasos de cada trabajo con tiempos de ejecución
   - Gráfico de línea de tiempo mostrando la progresión

### Configuración del Sistema

La sección de configuración muestra:
1. **Configuración de GitHub Actions**:
   - Propietario del repositorio
   - Nombre del repositorio
   - ID del Workflow
   - Estado del token de GitHub
2. **Información de la API**:
   - URL Base
   - Enlaces a la documentación (Swagger)
   - Lista de endpoints disponibles
3. **Información de Depuración**:
   - Ejemplos de llamadas a la API
   - Verificación de la configuración

## Ejemplos de Uso Común

### Ejemplo 1: Refresco de entorno de desarrollo
1. Ve a "Operaciones Day-2"
2. Selecciona "Refresco de Entornos"
3. Completa el formulario con los siguientes datos:
   - Host de Producción: "prod-postgres"
   - Host de Desarrollo: "dev-postgres"
   - Nombre de la Base de Datos: "app_database"
   - Usuario PostgreSQL: "postgres"
   - Grupo de Recursos: "rg-database"
4. Haz clic en "Iniciar Refresco de Entornos"
5. Ve a la sección de "Monitoreo" para seguir el progreso

### Ejemplo 2: Actualización de versión de PostgreSQL
1. Ve a "Operaciones Day-2"
2. Selecciona "Version Upgrade"
3. Completa el formulario con los datos requeridos incluyendo la versión objetivo
4. Verifica la versión actual y las advertencias de compatibilidad
5. Selecciona el tipo de endpoint y haz clic en "Iniciar Version Upgrade"
6. Consulta el resultado de la operación y la URL para seguimiento

## Solución de Problemas

Si encuentras algún problema:

1. **Error de conexión API**: Verifica que la API esté ejecutándose y que las credenciales (URL y API Key) sean correctas
2. **Error 401/403**: Asegúrate de que la API Key tenga los permisos necesarios
3. **Workflow no aparece**: Espera unos segundos y refresca la página de monitoreo
4. **Error en la actualización de versión**: Verifica que la versión seleccionada sea compatible con la actual
5. **Problemas de autenticación Azure**: Confirma que los datos en secrets.json sean correctos
