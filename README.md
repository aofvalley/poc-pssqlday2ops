# PostgreSQL Backup and Restore API

## 1. Preparación del entorno local

Instala Azure Functions Core Tools:

```sh
npm install -g azure-functions-core-tools@4
```

Instala Python 3.9 (recomendado para Azure Functions)

Crea un entorno virtual:

```sh
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

Instala las dependencias:

```sh
pip install -r requirements.txt
```

## 2. Configuración del GitHub workflow

Asegúrate de que tu archivo `.github/workflows/pg-backup-restore.yml` acepte parámetros de entrada:

```yaml
name: PostgreSQL Backup and Restore

on:
  workflow_dispatch:
    inputs:
      pg_host_prod:
        description: 'Production PostgreSQL server hostname'
        required: true
        default: 'prodpssql01'
      pg_host_dev:
        description: 'Development PostgreSQL server hostname'
        required: true
        default: 'devpssql01'
      pg_database:
        description: 'Database name'
        required: true
        default: 'test01'
      pg_user:
        description: 'PostgreSQL username'
        required: true
      pg_password:
        description: 'PostgreSQL password'
        required: true
      azure_storage_account:
        description: 'Azure Storage Account name'
        required: true
        default: 'pssqlstorage'
      azure_storage_container:
        description: 'Azure Storage Container name'
        required: true
        default: 'backups'
  # ...resto del workflow...
```

## 3. Prueba local

Configura `local.settings.json` con tus valores reales

Inicia la función localmente:

```sh
func start
```

Prueba la función con una solicitud HTTP:

```sh
curl -X POST http://localhost:7071/api/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prodpssql01",
    "pg_host_dev": "devpssql01",
    "pg_database": "test01",
    "pg_user": "postgres",
    "pg_password": "your-password",
    "azure_storage_account": "pssqlstorage",
    "azure_storage_container": "backups"
  }'
```

## 4. Despliegue en Azure

Crea un Function App en Azure:

```sh
az group create --name pg-backup-restore-rg --location eastus
az storage account create --name pgbackupstorage --location eastus --resource-group pg-backup-restore-rg --sku Standard_LRS
az functionapp create --resource-group pg-backup-restore-rg --consumption-plan-location eastus --runtime python --runtime-version 3.9 --functions-version 4 --name pg-backup-restore-function --storage-account pgbackupstorage --os-type linux
```

Configura las variables de entorno en Azure:

```sh
az functionapp config appsettings set --name pg-backup-restore-function --resource-group pg-backup-restore-rg --settings "GITHUB_OWNER=your-github-username" "GITHUB_REPO=your-repo-name" "GITHUB_WORKFLOW_ID=pg-backup-restore.yml" "GITHUB_TOKEN=your-personal-access-token"
```

Despliega la función:

```sh
func azure functionapp publish pg-backup-restore-function
```

## 5. Uso de la API

Para activar el workflow de backup/restore, envía una solicitud POST a tu Azure Function:

```sh
curl -X POST https://pg-backup-restore-function.azurewebsites.net/api/workflow/trigger?code=YOUR_FUNCTION_KEY \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prodpssql01",
    "pg_host_dev": "devpssql01",
    "pg_database": "test01",
    "pg_user": "postgres",
    "pg_password": "your-password",
    "azure_storage_account": "pssqlstorage",
    "azure_storage_container": "backups"
  }'
```

Para verificar el estado, usa:

```sh
curl -X GET "https://pg-backup-restore-function.azurewebsites.net/api/workflow/status?code=YOUR_FUNCTION_KEY"
```

Para verificar un run específico:

```sh
curl -X GET "https://pg-backup-restore-function.azurewebsites.net/api/workflow/status?code=YOUR_FUNCTION_KEY&runId=12345678"
```

## Consideraciones de seguridad

- **Autenticación de funciones**: Usa `authLevel: "function"` para requerir una clave de función.
- **Almacenamiento seguro de credenciales**: Considera usar Azure Key Vault para almacenar tokens y contraseñas.
- **Permisos minimizados**: Usa un token de GitHub con permisos mínimos (solo workflow).
- **VNET Integration**: Considera integrar tus funciones con una red virtual para mayor seguridad.
- **Almacenamiento seguro**: Nunca almacenes las contraseñas en código o repositorios.