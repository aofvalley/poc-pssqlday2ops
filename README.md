# PoC Operaciones Day-2 en Azure PostgreSQL Flexible Server

Este proyecto proporciona una solución completa para automatizar backups y restauraciones de bases de datos PostgreSQL utilizando GitHub Actions, con una API REST y una interfaz web para facilitar su uso.

## Arquitectura del Sistema

El sistema consta de tres componentes principales:

1. **GitHub Actions Workflow**: Pipeline de automatización que ejecuta los comandos de backup/restore de PostgreSQL.
2. **API REST**: Implementada con Azure Functions y FastAPI, permite disparar y monitorear los workflows.
3. **Frontend**: Interfaz web desarrollada con Streamlit que facilita la interacción con la API para usuarios no técnicos.

### Flujo de Ejecución

```
+-------------+     +-----------------+     +---------------+     +---------------+
|   Frontend   | --> |   Azure Function| --> | GitHub Actions| --> | PostgreSQL DB |
|  (Streamlit) |     |   API (FastAPI) |     |   Workflow    |     |               |
+-------------+     +-----------------+     +---------------+     +---------------+
       ^                     |                     |
       |                     v                     v
       +-------------+ Status updates        Logs y resultados
```

1. Un usuario solicita un backup o restore a través del frontend de Streamlit
2. El frontend hace una petición a la API REST
3. La API dispara el workflow de GitHub Actions con los parámetros correspondientes
4. GitHub Actions ejecuta los comandos de PostgreSQL necesarios
5. El estado y resultados se pueden consultar a través de la API
6. El frontend muestra el progreso y resultado al usuario

## Requisitos previos

- Python 3.8 a 3.12 (recomendado para FastAPI, Azure Functions y Streamlit)
- Azure Functions Core Tools 4.x
- Una cuenta de GitHub con un token de acceso personal (PAT)
- Una cuenta de Azure

## Dependencias del Proyecto

El archivo `requirements.txt` contiene todas las dependencias necesarias:

```
azure-functions    # Para el desarrollo de Azure Functions
requests           # Para llamadas HTTP a la API de GitHub
python-dotenv      # Para manejo de variables de entorno
azure-identity     # Para autenticación con Azure
azure-keyvault-secrets # Para gestión de secretos en Azure KeyVault
fastapi            # Framework web para la API
uvicorn            # Servidor ASGI para FastAPI
streamlit          # Para el desarrollo del frontend
```

## Componentes del Proyecto

### 1. GitHub Actions Workflow

El workflow (`pg-backup-restore.yml`) está diseñado para:

- Realizar backup de bases de datos PostgreSQL
- Restaurar bases de datos en otros servidores
- Trabajar con credenciales seguras mediante GitHub Secrets
- Proporcionar logs detallados del proceso

Ubicación: `.github/workflows/pg-backup-restore.yml`

#### Capacidades

- Backup completo de bases de datos
- Backup selectivo de tablas
- Restauración con o sin esquema
- Soporte para transformaciones durante la restauración

### 2. API REST (Azure Functions + FastAPI)

La API proporciona endpoints para:

- Iniciar trabajos de backup/restore
- Verificar el estado de trabajos en ejecución
- Consultar historial de trabajos
- Gestionar configuraciones

Ubicación: `/api`

#### Endpoints principales

- `/api/workflow/dump-restore`: Inicia un proceso de backup/restore
- `/api/workflow/status`: Consulta el estado de los workflows
- `/api/health`: Verifica el estado de la API
- `/api/config`: Consulta la configuración actual (solo desarrollo)
- `/api/docs`: Documentación interactiva (Swagger UI)

### 3. Frontend (Streamlit)

Interfaz de usuario que permite:

- Formularios intuitivos para configurar operaciones
- Visualización de estado y progreso de trabajos
- Historial de operaciones
- Gestión de configuraciones

Ubicación: `/frontend`

## Instalación y Configuración

### Clonar el repositorio

```bash
git clone https://github.com/yourusername/ghaction-pgdumprestore-api.git
cd ghaction-pgdumprestore-api
```

### Configurar el entorno virtual de Python

```bash
# Crear un entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows
.venv\Scripts\activate
# En macOS/Linux
source .venv/bin/activate

# Verificar la versión de Python
python --version  # Se recomienda Python 3.8+

# Instalar todas las dependencias del proyecto
pip install -r requirements.txt
```

### Configuración de Secretos

Hay dos formas de configurar las credenciales y parámetros necesarios:

#### Opción 1: Usar archivo secrets.json

El archivo `secrets.json` debe contener los siguientes valores:

```json
{
    "GITHUB_OWNER": "tu_usuario_github",
    "GITHUB_REPO": "ghaction-pgdumprestore-api",
    "GITHUB_WORKFLOW_ID": "pg-backup-restore.yml",
    "GITHUB_TOKEN": "tu_github_token",
    "tenant_id": "id_del_tenant_azure",
    "apim_key": "clave_de_api_management",
    "client_id": "id_de_managed_indentity_azure",
    "client_secret": "secreto_de_managed_identity_azure",
    "scope": "https://management.azure.com/.default"
}
```

> ⚠️ **IMPORTANTE**: No comprometas este archivo en el control de versiones. Asegúrate de que esté incluido en `.gitignore`.

#### Opción 2: Usar local.settings.json (para Azure Functions)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "GITHUB_TOKEN": "tu_github_token",
    "GITHUB_OWNER": "tu_usuario_github",
    "GITHUB_REPO": "ghaction-pgdumprestore-api",
    "GITHUB_WORKFLOW_ID": "pg-backup-restore.yml"
  }
}
```

### Configuración del Backend (API)

```bash
# Situarse en el directorio de la API
cd api

# Iniciar la API localmente
func start
```

La API estará disponible en http://localhost:7071/api/docs

### Configuración del Frontend (Streamlit)

```bash
# Situarse en el directorio del frontend
cd frontend

# Iniciar la aplicación Streamlit
streamlit run app.py
```

El frontend estará disponible en http://localhost:8501

## Uso del Sistema

### Casos de uso comunes

#### 1. Backup de una base en producción y restauración en desarrollo

1. Accede al frontend de Streamlit (http://localhost:8501)
2. Selecciona la opción "Backup y Restore" del menú lateral
3. Completa el formulario con:
   - Servidor de origen (producción)
   - Servidor de destino (desarrollo)
   - Nombre de la base de datos
   - Opciones adicionales
4. Haz clic en "Iniciar proceso"
5. Observa el estado del trabajo en tiempo real gracias a la actualización dinámica de Streamlit

#### 2. Verificación del estado mediante API

```bash
curl http://localhost:7071/api/workflow/status?run_id=123456789
```

## Despliegue en producción

### Despliegue de la API en Azure Functions

```bash
cd api
func azure functionapp publish pgdumprestore-api
```

### Despliegue del Frontend de Streamlit

Puedes desplegar la aplicación Streamlit en varias plataformas:

#### Opción 1: Streamlit Sharing (servicio oficial)

1. Crea una cuenta en [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio GitHub
3. Selecciona el archivo del frontend para su despliegue

#### Opción 2: Despliegue en Azure Web App

```bash
# Crear un archivo de configuración para la web app
echo "web: streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0" > Procfile

# Crear una web app en Azure
az webapp up --name pgdumprestore-frontend --resource-group pgdumprestore-rg --sku B1
```

## Seguridad

- La API utiliza autenticación mediante claves de función
- El token de GitHub debe tener permisos mínimos necesarios
- Las credenciales de bases de datos se gestionan como secrets en GitHub Actions
- Los secretos de Azure se pueden gestionar con Azure Key Vault (incluido en `requirements.txt`)
- Para entornos de producción, se recomienda implementar autenticación adicional como Azure AD

## Mantenimiento y Solución de problemas

### Actualización de dependencias

Para actualizar todas las dependencias del proyecto:

```bash
pip install --upgrade -r requirements.txt
```

### Verificación del entorno

Para verificar que todas las dependencias están correctamente instaladas:

```bash
pip freeze
```

### Logs

- **API**: Los logs se almacenan en Azure Functions
- **GitHub Actions**: Los logs están disponibles en la interfaz de GitHub
- **Frontend**: Los logs de Streamlit se muestran en la terminal donde se ejecuta

### Problemas comunes

- **Error 401 Unauthorized**: Verifica tu token de GitHub y asegúrate de que tenga los permisos adecuados.
- **Error 404 Not Found**: Verifica que el nombre del repositorio y del workflow sean correctos.
- **Error de conexión**: Asegúrate de que la función tenga acceso a internet para comunicarse con la API de GitHub.
- **Problemas con Streamlit**: Verifica que estás usando una versión compatible de Python y que todas las dependencias están instaladas.

## Contribución

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios
4. Commit tus cambios (`git commit -m 'Add some amazing feature'`)
5. Push a la rama (`git push origin feature/amazing-feature`)
6. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo [LICENCIA] - ver el archivo LICENSE para más detalles.