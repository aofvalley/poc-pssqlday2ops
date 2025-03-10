# Guía de Despliegue en Azure Functions

Esta guía explica cómo desplegar la API de PostgreSQL Backup and Restore en Azure Functions.

## Requisitos Previos

- Una cuenta de Azure
- [Azure CLI](https://docs.microsoft.com/es-es/cli/azure/install-azure-cli) instalada
- [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools) instalada
- [Git](https://git-scm.com/) instalado
- [Python](https://www.python.org/) 3.8 o superior

## 1. Preparación del Entorno Local

Primero, clone el repositorio y prepare el entorno local:

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/ghaction-pgdumprestore-api.git
cd ghaction-pgdumprestore-api

# Crear entorno virtual
python -m venv .venv

# En Windows PowerShell
.venv\Scripts\Activate.ps1
# O en Windows CMD
# .venv\Scripts\activate.bat
# En Linux/macOS
# source .venv/bin/activate

# Instalar dependencias
pip install -r api/requirements.txt
```

## 2. Configuración de Variables de Entorno

La API necesita las siguientes variables de entorno:

| Variable | Descripción | Obligatorio |
|----------|-------------|-------------|
| GITHUB_TOKEN | Token personal de GitHub con permiso para ejecutar workflows | Sí |
| GITHUB_OWNER | Nombre de usuario o organización propietaria del repositorio | Sí |
| GITHUB_REPO | Nombre del repositorio que contiene el workflow | Sí |
| GITHUB_WORKFLOW_ID | ID o nombre del archivo de workflow (default: pg-backup-restore.yml) | No |

### Obtener un GitHub Personal Access Token (PAT)

1. Vaya a GitHub -> Settings -> Developer Settings -> [Personal Access Tokens](https://github.com/settings/tokens)
2. Haga clic en "Generate new token" (Generate new token (classic))
3. Asigne un nombre descriptivo
4. Seleccione los siguientes permisos:
   - `repo` (acceso completo al repositorio)
   - `workflow` (para gestionar workflows)
5. Haga clic en "Generate token"
6. **IMPORTANTE**: Copie el token generado y guárdelo de forma segura, no podrá verlo nuevamente

## 3. Prueba Local (opcional)

Antes de desplegar, puede probar la función localmente:

```bash
cd api
func start
```

Visite http://localhost:7071/api/health para verificar que la API funciona correctamente.

## 4. Despliegue en Azure Functions

### 4.1 Iniciar sesión en Azure

```powershell
az login
```

### 4.2 Crear Recursos Necesarios

#### En PowerShell (Windows):

```powershell
# Definir variables
$resourceGroup = "rg-pgdumprestore-api"
$location = "eastus"  # o la región más cercana a usted
$randomSuffix = -join ((48..57) + (97..122) | Get-Random -Count 6 | ForEach-Object {[char]$_})
$storageAccount = "pgdumpstorage$randomSuffix"  # nombre único
$functionApp = "pgdumprestore-api-$randomSuffix"  # nombre único

# Solicitar credenciales de GitHub de forma segura
$githubToken = Read-Host -Prompt "Introduce tu GitHub Token" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($githubToken)
$githubTokenValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$githubOwner = Read-Host -Prompt "Introduce tu GitHub Owner (nombre de usuario)"
$githubRepo = Read-Host -Prompt "Introduce el nombre del repositorio"
$githubWorkflowId = Read-Host -Prompt "Introduce el ID del workflow (pg-backup-restore.yml por defecto)"
if (-not $githubWorkflowId) { $githubWorkflowId = "pg-backup-restore.yml" }

# Crear grupo de recursos
az group create --name $resourceGroup --location $location

# Crear cuenta de almacenamiento (necesaria para Functions)
az storage account create `
  --name $storageAccount `
  --location $location `
  --resource-group $resourceGroup `
  --sku Standard_LRS `
  --kind StorageV2

# Crear la Function App (Plan de Consumo)
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

#### En Bash (Linux/macOS):

```bash
# Definir variables
resourceGroup="rg-pgdumprestore-api"
location="eastus"  # o la región más cercana a usted
randomSuffix=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 6 | head -n 1)
storageAccount="pgdumpstorage${randomSuffix}"  # nombre único
functionApp="pgdumprestore-api-${randomSuffix}"  # nombre único

# Solicitar credenciales de GitHub de forma interactiva
read -sp "Introduce tu GitHub Token: " githubTokenValue
echo ""
read -p "Introduce tu GitHub Owner (nombre de usuario): " githubOwner
read -p "Introduce el nombre del repositorio: " githubRepo
read -p "Introduce el ID del workflow (pg-backup-restore.yml por defecto): " githubWorkflowId
if [ -z "$githubWorkflowId" ]; then githubWorkflowId="pg-backup-restore.yml"; fi

# Crear grupo de recursos
az group create --name $resourceGroup --location $location

# Crear cuenta de almacenamiento (necesaria para Functions)
az storage account create \
  --name $storageAccount \
  --location $location \
  --resource-group $resourceGroup \
  --sku Standard_LRS \
  --kind StorageV2

# Crear la Function App (Plan de Consumo)
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

### 4.3 Configurar Variables de Entorno en la Function App

#### En PowerShell (Windows):

```powershell
# Establecer variables de entorno con los valores de configuración
az functionapp config appsettings set `
  --name $functionApp `
  --resource-group $resourceGroup `
  --settings `
  "GITHUB_TOKEN=$githubTokenValue" `
  "GITHUB_OWNER=$githubOwner" `
  "GITHUB_REPO=$githubRepo" `
  "GITHUB_WORKFLOW_ID=$githubWorkflowId" `
  "SCM_DO_BUILD_DURING_DEPLOYMENT=true"

# Limpiar la variable que contiene el token para seguridad
$githubTokenValue = $null
[System.GC]::Collect()
```

#### En Bash (Linux/macOS):

```bash
# Establecer variables de entorno con los valores de configuración
az functionapp config appsettings set \
  --name $functionApp \
  --resource-group $resourceGroup \
  --settings \
  "GITHUB_TOKEN=$githubTokenValue" \
  "GITHUB_OWNER=$githubOwner" \
  "GITHUB_REPO=$githubRepo" \
  "GITHUB_WORKFLOW_ID=$githubWorkflowId" \
  "SCM_DO_BUILD_DURING_DEPLOYMENT=true"

# Limpiar la variable que contiene el token para seguridad
githubTokenValue=""
```

### 4.4 Desplegar la Aplicación

```powershell
# Asegúrese de estar en la raíz del proyecto
cd /path/to/ghaction-pgdumprestore-api

# Desplegar usando Azure Functions Core Tools
func azure functionapp publish $functionApp --python
```

## 5. Verificar el Despliegue

Una vez completado el despliegue, puede verificar que la API está funcionando correctamente:

### En PowerShell (Windows):

```powershell
# Obtener la URL
$functionUrl = az functionapp show --name $functionApp --resource-group $resourceGroup --query "defaultHostName" -o tsv

# Obtener la clave de función desde el portal de Azure:
# 1. Vaya al Azure Portal y seleccione su Function App
# 2. Navegue a "Funciones" en el menú lateral
# 3. Seleccione la función "handle_http"
# 4. Haga clic en "Claves de función" (en la sección "Desarrollador")
# 5. Copie la clave predeterminada o cree una nueva

# Solicitar la clave de función de forma segura
$functionKey = Read-Host -Prompt "Introduce la clave de función obtenida del portal" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($functionKey)
$functionKeyValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Verificar salud de la API
$response = Invoke-RestMethod -Uri "https://$functionUrl/api/health?code=$functionKeyValue"
$response | ConvertTo-Json -Depth 3
```

### En Bash (Linux/macOS):

```bash
# Obtener la URL
functionUrl=$(az functionapp show --name $functionApp --resource-group $resourceGroup --query "defaultHostName" -o tsv)

# Obtener la clave de función desde el portal de Azure:
# 1. Vaya al Azure Portal y seleccione su Function App
# 2. Navegue a "Funciones" en el menú lateral
# 3. Seleccione la función "handle_http"
# 4. Haga clic en "Claves de función" (en la sección "Desarrollador")
# 5. Copie la clave predeterminada o cree una nueva

# Solicitar la clave de función de forma segura
read -sp "Introduce la clave de función obtenida del portal: " functionKeyValue
echo ""

# Verificar salud de la API
curl "https://$functionUrl/api/health?code=$functionKeyValue"
```

Este comando debería devolver información sobre el estado de la API en formato JSON.

## 6. Obtener la Clave de Función para Autenticación

Para acceder a los endpoints protegidos, necesitará incluir la clave de función como parámetro de consulta `code` en sus solicitudes:

### En PowerShell (Windows):

```powershell
# Obtener la clave de función principal (usando la API REST)
$masterKey = az functionapp keys list --name $functionApp --resource-group $resourceGroup --query "masterKey" -o tsv
$apiUrl = "https://$functionUrl/admin/functions/handle_http/keys?code=$masterKey"
$response = Invoke-RestMethod -Method Get -Uri $apiUrl
$functionKey = $response.keys[0].value

Write-Host "Su clave de función es: $functionKey"
```

### En Bash (Linux/macOS):

```bash
# Obtener la clave de función principal 
masterKey=$(az functionapp keys list --name $functionApp --resource-group $resourceGroup --query "masterKey" -o tsv)
functionKey=$(curl -s -X GET "https://$functionUrl/admin/functions/handle_http/keys?code=$masterKey" | jq -r '.keys[0].value')

echo "Su clave de función es: $functionKey"
```

Alternativamente, también puede obtener las claves desde el portal de Azure:
1. Vaya al Azure Portal y seleccione su Function App
2. Navegue a "Funciones" en el menú lateral
3. Seleccione la función "handle_http"
4. Haga clic en "Claves de función" (en la sección "Desarrollador")
5. Las claves se mostrarán allí y puede copiarlas o generar nuevas

## 7. Usar la API

Una vez desplegada, puede usar la API enviando solicitudes HTTP:

### En PowerShell (Windows):

```powershell
# Guardar la URL y la clave de función en variables (para los ejemplos)
$functionUrl = "your-function-app.azurewebsites.net"  # Reemplazar por tu URL
$functionKeyValue = Read-Host -Prompt "Introduce la clave de función" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($functionKeyValue)
$functionKeyValue = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Verificar estado
$healthResponse = Invoke-RestMethod -Uri "https://$functionUrl/api/health?code=$functionKeyValue"
$healthResponse | ConvertTo-Json -Depth 3

# Ver configuración (redactada)
$configResponse = Invoke-RestMethod -Uri "https://$functionUrl/api/config?code=$functionKeyValue"
$configResponse | ConvertTo-Json

# Ejecutar un workflow de backup/restore
$body = @{
  pg_host_prod = "prod-server"
  pg_host_dev = "dev-server"
  pg_database = "my_database"
  pg_user = "postgres"
  resource_group = "my-resource-group"
} | ConvertTo-Json

$workflowResponse = Invoke-RestMethod -Method Post -Uri "https://$functionUrl/api/workflow/dump-restore?code=$functionKeyValue" -Body $body -ContentType "application/json"
$workflowResponse | ConvertTo-Json

# Ver estado de workflows
$statusResponse = Invoke-RestMethod -Uri "https://$functionUrl/api/workflow/status?code=$functionKeyValue"
$statusResponse | ConvertTo-Json -Depth 5
```

### En Bash (Linux/macOS):

```bash
# Guardar la URL y la clave de función en variables (para los ejemplos)
functionUrl="your-function-app.azurewebsites.net"  # Reemplazar por tu URL
read -sp "Introduce la clave de función: " functionKeyValue
echo ""

# Verificar estado
curl "https://$functionUrl/api/health?code=$functionKeyValue"

# Ver configuración (redactada)
curl "https://$functionUrl/api/config?code=$functionKeyValue"

# Ejecutar un workflow de backup/restore
curl -X POST "https://$functionUrl/api/workflow/dump-restore?code=$functionKeyValue" \
-H "Content-Type: application/json" \
-d '{
  "pg_host_prod": "prod-server",
  "pg_host_dev": "dev-server",
  "pg_database": "my_database",
  "pg_user": "postgres",
  "resource_group": "my-resource-group"
}'

# Ver estado de workflows
curl "https://$functionUrl/api/workflow/status?code=$functionKeyValue"
```

## 8. Resolución de Problemas

Si enfrenta algún problema durante el despliegue o al usar la API, puede verificar los logs:

```powershell
# Ver logs en vivo
az webapp log tail --name $functionApp --resource-group $resourceGroup

# Ver logs de la aplicación
az webapp log download --name $functionApp --resource-group $resourceGroup --log-file app.log
```

## Seguridad

La API utiliza el nivel de autenticación `Function` (más sencilla) de Azure Functions. Esto significa que:

- Cada endpoint está protegido por una clave de función
- Debe incluir esta clave como parámetro `code` en todas las solicitudes
- La seguridad depende de mantener esta clave en secreto

Si necesita un nivel de seguridad más alto, considere:
- Implementar autenticación de Azure AD
- Configurar un Private Endpoint para la Function App
- Utilizar Azure API Management para gestionar el acceso a la API

## Recursos Adicionales

- [Documentación de Azure Functions](https://docs.microsoft.com/es-es/azure/azure-functions/)
- [Python en Azure Functions](https://docs.microsoft.com/es-es/azure/azure-functions/functions-reference-python)
