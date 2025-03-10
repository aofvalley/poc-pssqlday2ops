# PostgreSQL Backup and Restore API

Esta aplicación permite ejecutar un pipeline de GitHub Actions para realizar backups y restauraciones de bases de datos PostgreSQL mediante una API REST implementada con Azure Functions y FastAPI.

## Requisitos previos

- Python 3.8 a 3.12 (recomendado para FastAPI y Azure Functions)
- Azure Functions Core Tools 4.x
- Una cuenta de GitHub con un token de acceso personal (PAT)
- Una cuenta de Azure 
- Un repositorio con el workflow de GitHub Actions para backup/restore

## 1. Configuración del entorno de desarrollo

### Instalar Python con versión compatible

#### En macOS:

```bash
# Usando Homebrew
brew install python@3.9

# Verificar la instalación
python3.9 --version
```

#### En Windows:

Descarga e instala Python 3.9 desde [python.org](https://www.python.org/downloads/release/python-3913/)

#### En Linux:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3.9-dev

# Verificar la instalación
python3.9 --version
```

### Instalar Azure Functions Core Tools

```bash
# En Windows usando npm
npm install -g azure-functions-core-tools@4

# En macOS usando Homebrew
brew tap azure/functions
brew install azure-functions-core-tools@4

# En Linux
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### Clonar el repositorio

```bash
git clone https://github.com/yourusername/ghaction-pgdumprestore-api.git
cd ghaction-pgdumprestore-api
```

### Configurar el entorno virtual de Python

```bash
# Crear un entorno virtual con la versión específica de Python
# En macOS/Linux (con Python 3.9 específicamente)
python3.9 -m venv .venv

# En Windows (asegúrate de que Python 3.9 está en el PATH)
py -3.9 -m venv .venv

# Activar el entorno virtual
# En Windows
.venv\Scripts\activate
# En macOS/Linux
source .venv/bin/activate

# Verificar la versión de Python
python --version  # Debería mostrar Python 3.9.x

# Instalar las dependencias
pip install -r requirements.txt
```

### Configurar variables de entorno locales

Edita el archivo `api/local.settings.json` con tus valores:

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

## 2. Ejecutar localmente

```bash
cd api
func start
```

## 3. Probar la API localmente

Una vez que la API está ejecutándose localmente, puedes acceder a la interfaz de Swagger para explorar la API en:

```
http://localhost:7071/docs
```

### Disparar un workflow

```bash
curl -X POST http://localhost:7071/api/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prod-server",
    "pg_host_dev": "dev-server",
    "pg_database": "my_database",
    "pg_user": "postgres",
    "resource_group": "my-resource-group"
  }'
```

### Verificar el estado del workflow

```bash
# Ver todas las ejecuciones recientes
curl http://localhost:7071/api/workflow/status

# Ver una ejecución específica (reemplaza 123456789 con el ID de la ejecución)
curl http://localhost:7071/api/workflow/status?run_id=123456789
```

### Comprobar la salud del servicio

```bash
curl http://localhost:7071/api/health
```

## 4. Despliegue en Azure

### Crear recursos en Azure

```bash
# Iniciar sesión en Azure
az login

# Crear un grupo de recursos
az group create --name pgdumprestore-rg --location eastus

# Crear una cuenta de almacenamiento
az storage account create --name pgdumprestorestore --location eastus --resource-group pgdumprestore-rg --sku Standard_LRS

# Crear la Function App
az functionapp create --resource-group pgdumprestore-rg --consumption-plan-location eastus --runtime python --runtime-version 3.9 --functions-version 4 --name pgdumprestore-api --storage-account pgdumprestorestore --os-type linux
```

### Configurar las variables de entorno en Azure

```bash
az functionapp config appsettings set --name pgdumprestore-api \
  --resource-group pgdumprestore-rg \
  --settings \
  "GITHUB_TOKEN=tu_github_token" \
  "GITHUB_OWNER=tu_usuario_github" \
  "GITHUB_REPO=ghaction-pgdumprestore-api" \
  "GITHUB_WORKFLOW_ID=pg-backup-restore.yml"
```

### Desplegar la Function App

```bash
cd api
func azure functionapp publish pgdumprestore-api
```

## 5. Uso de la API en producción

### Interfaz de Swagger
Una vez desplegada, puedes acceder a la documentación interactiva en:

```
https://pgdumprestore-api.azurewebsites.net/docs
```

### Disparar un workflow

```bash
curl -X POST https://pgdumprestore-api.azurewebsites.net/api/workflow/trigger?code=TU_FUNCTION_KEY \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prod-server",
    "pg_host_dev": "dev-server",
    "pg_database": "my_database",
    "pg_user": "postgres",
    "resource_group": "my-resource-group"
  }'
```

### Verificar el estado del workflow

```bash
# Ver todas las ejecuciones recientes
curl https://pgdumprestore-api.azurewebsites.net/api/workflow/status?code=TU_FUNCTION_KEY

# Ver una ejecución específica
curl https://pgdumprestore-api.azurewebsites.net/api/workflow/status?code=TU_FUNCTION_KEY&run_id=123456789
```

### Comprobar la salud del servicio
```bash
curl https://pgdumprestore-api.azurewebsites.net/api/health?code=TU_FUNCTION_KEY
```

## Seguridad

- La API está protegida con autenticación a nivel de función. Se requiere una clave de función para acceder a los endpoints.
- El token de GitHub debe tener permisos para disparar workflows.
- Considera usar Azure Key Vault para almacenar de forma segura el token de GitHub y otras credenciales sensibles.
- Para entornos de producción, considera implementar autenticación adicional como Azure AD.

## Solución de problemas

- **Error 401 Unauthorized**: Verifica tu token de GitHub y asegúrate de que tenga los permisos adecuados.
- **Error 404 Not Found**: Verifica que el nombre del repositorio y del workflow sean correctos.
- **Error de conexión**: Asegúrate de que la función tenga acceso a internet para comunicarse con la API de GitHub.