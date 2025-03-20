# Guía de Prueba y Despliegue en Azure Functions

Esta guía detalla cómo probar localmente y desplegar la API de PostgreSQL Backup and Restore en Azure Functions.

## Requisitos Previos

- [Python](https://www.python.org/) 3.8 o superior
- [Git](https://git-scm.com/) instalado
- [Azure CLI](https://docs.microsoft.com/es-es/cli/azure/install-azure-cli) instalada
- [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools) instalada
- Una cuenta de Azure (para la fase de despliegue)
- Un token de acceso personal de GitHub (PAT)

## 1. Configuración Inicial

### 1.1. Clone el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/ghaction-pgdumprestore-api.git
cd ghaction-pgdumprestore-api
```

### 1.2. Prepare el Entorno Virtual

**En Windows PowerShell:**
```powershell
# Crear entorno virtual
python -m venv .venv

# Activar el entorno virtual
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r api/requirements.txt
```

**En Linux/macOS:**
```bash
# Crear entorno virtual
python -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r api/requirements.txt
```

## 2. Obtener un Token de GitHub

La API necesita un token de GitHub para interactuar con los workflows.

1. Vaya a GitHub → Settings → Developer Settings → [Personal Access Tokens](https://github.com/settings/tokens)
2. Haga clic en "Generate new token" (Generate new token (classic))
3. Asigne un nombre descriptivo como "PG Backup Restore API"
4. Seleccione los siguientes permisos:
   - `repo` (acceso completo al repositorio)
   - `workflow` (para gestionar workflows)
5. Haga clic en "Generate token"
6. **IMPORTANTE**: Guarde este token de forma segura, no podrá verlo nuevamente

## 3. Configurar Variables de Entorno Locales

Cree un archivo local.settings.json en la carpeta api para las pruebas locales:

```bash
cd api
```

**En Windows PowerShell:**
```powershell
@"
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "GITHUB_TOKEN": "su-token-de-github",
    "GITHUB_OWNER": "su-nombre-de-usuario-u-organizacion",
    "GITHUB_REPO": "nombre-del-repositorio",
    "GITHUB_WORKFLOW_ID": "pg-backup-restore.yml"
  }
}
"@ | Out-File -FilePath local.settings.json -Encoding utf8
```

**En Linux/macOS:**
```bash
cat > local.settings.json << EOL
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "GITHUB_TOKEN": "su-token-de-github",
    "GITHUB_OWNER": "su-nombre-de-usuario-u-organizacion",
    "GITHUB_REPO": "nombre-del-repositorio",
    "GITHUB_WORKFLOW_ID": "pg-backup-restore.yml"
  }
}
EOL
```

> **NOTA**: Reemplace los valores con su información real. No comparta este archivo ya que contiene credenciales.

## 4. Ejecutar y Probar Localmente

```bash
# Asegúrese de estar en la carpeta api
cd api
func start
```

Debería ver un mensaje indicando que la API está ejecutándose en http://localhost:7071.

### 4.3. Probar los Endpoints

Puede probar los endpoints utilizando un navegador, curl o herramientas como Postman.

**Comprobar estado de la API:**

**En Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:7071/api/health" | ConvertTo-Json -Depth 3
```

**En Linux/macOS:**
```bash
curl http://localhost:7071/api/health
```

**Verificar la configuración:**

**En Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:7071/api/config" | ConvertTo-Json
```

**En Linux/macOS:**
```bash
curl http://localhost:7071/api/config
```

**Ejecutar un workflow de backup/restore:**

**En Windows PowerShell:**
```powershell
$body = @{
  pg_host_prod = "prod-server"
  pg_host_dev = "dev-server"
  pg_database = "my_database"
  pg_user = "postgres"
  pg_password = "securepassword123"
  resource_group = "my-resource-group"
  storage_account = "mystorageaccount"
  storage_container = "backups"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:7071/api/workflow/dump-restore" -Body $body -ContentType "application/json" | ConvertTo-Json
```

**En Linux/macOS:**
```bash
curl -X POST http://localhost:7071/api/workflow/dump-restore \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prod-server",
    "pg_host_dev": "dev-server",
    "pg_database": "my_database",
    "pg_user": "postgres",
    "pg_password": "securepassword123",
    "resource_group": "my-resource-group",
    "storage_account": "mystorageaccount",
    "storage_container": "backups"
  }'
```

### 4.4. Ver Documentación de la API

Acceda a la documentación Swagger en: http://localhost:7071/api/docs

## 5. Desplegar en Azure Functions

Una vez que haya probado con éxito la API localmente, puede desplegarla en Azure.

### 5.1. Iniciar Sesión en Azure

```bash
az login
```

### 5.2. Crear Recursos Necesarios

**En Windows PowerShell:**
```powershell
# Definir variables
$resourceGroup = "rg-pgdumprestore-api"
$location = "eastus"  # o la región más cercana a usted
$randomSuffix = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object {[char]$_})
$storageAccount = "pgdumpstorage$randomSuffix"
$functionApp = "pgdumprestore-api-$randomSuffix"

# Crear grupo de recursos
az group create --name $resourceGroup --location $location

# Crear cuenta de almacenamiento
az storage account create `
  --name $storageAccount `
  --location $location `
  --resource-group $resourceGroup `
  --sku Standard_LRS `
  --kind StorageV2

# Crear la Function App
az functionapp create `
  --name $functionApp `
  --storage-account $storageAccount `
  --consumption-plan-location $location `
  --resource-group $resourceGroup `
  --os-type Linux `
  --runtime python `
  --runtime-version 3.9 `
  --functions-version 4
```

**En Linux/macOS:**
```bash
# Definir variables
resourceGroup="rg-pgdumprestore-api"
location="eastus"
randomSuffix=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 6 | head -n 1)
storageAccount="pgdumpstorage${randomSuffix}"
functionApp="pgdumprestore-api-${randomSuffix}"

# Crear grupo de recursos
az group create --name $resourceGroup --location $location

# Crear cuenta de almacenamiento
az storage account create \
  --name $storageAccount \
  --location $location \
  --resource-group $resourceGroup \
  --sku Standard_LRS \
  --kind StorageV2

# Crear la Function App
az functionapp create \
  --name $functionApp \
  --storage-account $storageAccount \
  --consumption-plan-location $location \
  --resource-group $resourceGroup \
  --os-type Linux \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4
```

### 5.3. Configurar Variables de Entorno en Azure

**En Windows PowerShell:**
```powershell
# Solicitar valores de GitHub de forma segura
$githubToken = Read-Host -Prompt "Introduce tu GitHub Token" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($githubToken)
$githubTokenValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$githubOwner = Read-Host -Prompt "Introduce tu GitHub Owner (nombre de usuario u organización)"
$githubRepo = Read-Host -Prompt "Introduce el nombre del repositorio"
$githubWorkflowId = Read-Host -Prompt "Introduce el ID del workflow (pg-backup-restore.yml por defecto)"
if (-not $githubWorkflowId) { $githubWorkflowId = "pg-backup-restore.yml" }

# Configurar variables de entorno
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings `
  "GITHUB_TOKEN=$githubTokenValue" `
  "GITHUB_OWNER=$githubOwner" `
  "GITHUB_REPO=$githubRepo" `
  "GITHUB_WORKFLOW_ID=$githubWorkflowId" `
  "SCM_DO_BUILD_DURING_DEPLOYMENT=true"

# Limpiar variable de token por seguridad
$githubTokenValue = $null
[System.GC]::Collect()
```

**En Linux/macOS:**
```bash
# Solicitar valores de GitHub de forma interactiva
read -sp "Introduce tu GitHub Token: " githubTokenValue
echo ""
read -p "Introduce tu GitHub Owner (nombre de usuario u organización): " githubOwner
read -p "Introduce el nombre del repositorio: " githubRepo
read -p "Introduce el ID del workflow (pg-backup-restore.yml por defecto): " githubWorkflowId
if [ -z "$githubWorkflowId" ]; then githubWorkflowId="pg-backup-restore.yml"; fi

# Configurar variables de entorno
az functionapp config appsettings set \
  --name $functionApp \
  --resource-group $resourceGroup \
  --settings \
  "GITHUB_TOKEN=$githubTokenValue" \
  "GITHUB_OWNER=$githubOwner" \
  "GITHUB_REPO=$githubRepo" \
  "GITHUB_WORKFLOW_ID=$githubWorkflowId" \
  "SCM_DO_BUILD_DURING_DEPLOYMENT=true"

# Limpiar variable de token por seguridad
githubTokenValue=""
```

### 5.4. Desplegar Código

Asegúrese de estar en la carpeta raíz del proyecto:

```bash
# Volver a la raíz del proyecto si es necesario
cd ..

# Desplegar usando Azure Functions Core Tools
func azure functionapp publish $functionApp --python
```

### 5.5. Verificar Despliegue

**En Windows PowerShell:**
```powershell
# Obtener la URL de la function app
$functionUrl = az functionapp show --name $functionApp --resource-group $resourceGroup --query "defaultHostName" -o tsv

Write-Host "Su API está disponible en: https://$functionUrl"
Write-Host "Documentación Swagger: https://$functionUrl/api/docs"
```

**En Linux/macOS:**
```bash
# Obtener la URL de la function app
functionUrl=$(az functionapp show --name $functionApp --resource-group $resourceGroup --query "defaultHostName" -o tsv)

echo "Su API está disponible en: https://$functionUrl"
echo "Documentación Swagger: https://$functionUrl/api/docs"
```

## 6. Obtener Clave de Función para Autenticación

Para acceder a su API desplegada, necesitará una clave de función:

### 6.1. Desde el Portal de Azure

1. Vaya al [Portal de Azure](https://portal.azure.com)
2. Navegue a su Function App (`$functionApp`)
3. Seleccione "Funciones" en el menú lateral
4. Haga clic en la función "handle_http" (o "api")
5. Haga clic en "Claves de función" (en la sección "Desarrollador")
6. Copie la clave predeterminada o cree una nueva

### 6.2. Usando Azure CLI

**En Windows PowerShell:**
```powershell
# Obtener la clave de host predeterminada
$functionKey = az functionapp keys list --name $functionApp --resource-group $resourceGroup --query "functionKeys.default" -o tsv

Write-Host "Su clave de función es: $functionKey"
Write-Host "Para probar la API, use: https://$functionUrl/api/health?code=$functionKey"
```

**En Linux/macOS:**
```bash
# Obtener la clave de host predeterminada
functionKey=$(az functionapp keys list --name $functionApp --resource-group $resourceGroup --query "functionKeys.default" -o tsv)

echo "Su clave de función es: $functionKey"
echo "Para probar la API, use: https://$functionUrl/api/health?code=$functionKey"
```

## 7. Probar la API Desplegada

### 7.1. Verificar Estado

**En Windows PowerShell:**
```powershell
$response = Invoke-RestMethod -Uri "https://$functionUrl/api/health?code=$functionKey"
$response | ConvertTo-Json -Depth 3
```

**En Linux/macOS:**
```bash
curl "https://$functionUrl/api/health?code=$functionKey"
```

### 7.2. Ejecutar un Workflow de Backup y Restauración

**En Windows PowerShell:**
```powershell
$body = @{
  pg_host_prod = "prod-server"
  pg_host_dev = "dev-server"
  pg_database = "my_database"
  pg_user = "postgres"
  pg_password = "securepassword123"
  resource_group = "my-resource-group"
  storage_account = "mystorageaccount"
  storage_container = "backups"
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "https://$functionUrl/api/workflow/dump-restore?code=$functionKey" -Body $body -ContentType "application/json"
$response | ConvertTo-Json
```

**En Linux/macOS:**
```bash
curl -X POST "https://$functionUrl/api/workflow/dump-restore?code=$functionKey" \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "prod-server",
    "pg_host_dev": "dev-server",
    "pg_database": "my_database",
    "pg_user": "postgres",
    "pg_password": "securepassword123",
    "resource_group": "my-resource-group",
    "storage_account": "mystorageaccount",
    "storage_container": "backups"
  }'
```

## 8. Monitoreo y Resolución de Problemas

### 8.1. Ver Logs en Tiempo Real

```bash
az webapp log tail --name $functionApp --resource-group $resourceGroup
```

### 8.2. Descargar Logs

```bash
az webapp log download --name $functionApp --resource-group $resourceGroup --log-file logs.zip
```

### 8.3. Verificar Problemas Comunes

Si la API no responde correctamente:

1. Verifique que las variables de entorno están configuradas correctamente
2. Asegúrese de que el token de GitHub tiene los permisos necesarios
3. Revise los logs para identificar errores específicos
4. Compruebe que el workflow de GitHub existe y está correctamente configurado

## 9. Documentación Adicional

- [Documentación de Azure Functions](https://docs.microsoft.com/es-es/azure/azure-functions/)
- [Python en Azure Functions](https://docs.microsoft.com/es-es/azure/azure-functions/functions-reference-python)
- [GitHub Actions API](https://docs.github.com/es/rest/reference/actions)
- [FastAPI en Azure Functions](https://docs.microsoft.com/es-es/azure/azure-functions/functions-create-serverless-api)

---

Para eliminar todos los recursos cuando ya no los necesite:

```bash
az group delete --name $resourceGroup --yes --no-wait
```
