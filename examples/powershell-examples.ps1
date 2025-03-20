<#
.SYNOPSIS
    Ejemplos de uso de la API PostgreSQL Backup & Restore desde PowerShell
.DESCRIPTION
    Este script contiene ejemplos de cómo interactuar con la API de PostgreSQL Backup & Restore
    desde PowerShell utilizando Invoke-RestMethod.
.NOTES
    Creado por: Alfonso de la Guardia
    Fecha: Junio 2023
#>

# Configurar las variables de la API (reemplazar con los valores correctos)
$apiUrl = "pssqlapitest.azurewebsites.net"

# Opción 1: Ingresar la clave de función de forma segura (recomendado)
$secureString = Read-Host -Prompt "Ingrese la clave de función" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString)
$functionKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Opción 2: Definir la clave directamente (no recomendado - solo para pruebas)
# $functionKey = "TU_CLAVE_DE_FUNCION"

# ============= Ejemplos de uso =============

# 1. Verificar el estado de salud del servicio
Write-Host "`n===== Verificando estado de salud =====`n" -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "https://$apiUrl/api/health?code=$functionKey" -ErrorAction Stop
    Write-Host "Estado del sistema: $($healthResponse.status)" -ForegroundColor $(if ($healthResponse.status -eq "healthy") { "Green" } else { "Yellow" })
    Write-Host "Estado de GitHub API: $($healthResponse.github_api_status)" -ForegroundColor $(if ($healthResponse.github_api_status -eq "ok") { "Green" } else { "Red" })
    Write-Host "Estado de configuración GitHub: $($healthResponse.github_config_status)" -ForegroundColor $(if ($healthResponse.github_config_status -eq "ok") { "Green" } else { "Red" })
    
    # Mostrar detalles de GitHub API rate limit si están disponibles
    if ($healthResponse.details.github_api.rate_limit) {
        Write-Host "Rate limit de GitHub: $($healthResponse.details.github_api.rate_limit.remaining)/$($healthResponse.details.github_api.rate_limit.limit)"
    }
}
catch {
    Write-Host "Error al verificar el estado de salud: $_" -ForegroundColor Red
}

# 2. Obtener configuración actual
Write-Host "`n===== Obteniendo configuración =====`n" -ForegroundColor Green
try {
    $configResponse = Invoke-RestMethod -Uri "https://$apiUrl/api/config?code=$functionKey" -ErrorAction Stop
    Write-Host "GitHub Owner: $($configResponse.github_owner)"
    Write-Host "GitHub Repo: $($configResponse.github_repo)"
    Write-Host "GitHub Workflow ID: $($configResponse.github_workflow_id)"
    Write-Host "Token cargado: $($configResponse.token_loaded)" -ForegroundColor $(if ($configResponse.token_loaded) { "Green" } else { "Red" })
}
catch {
    Write-Host "Error al obtener configuración: $_" -ForegroundColor Red
}

# 3. Ejecutar un workflow de backup/restore
Write-Host "`n===== Ejecutar workflow de backup/restore =====`n" -ForegroundColor Green
$body = @{
    pg_host_prod = "advpsqlfxuk"
    pg_host_dev = "advpsqlfxukdev" 
    pg_database = "test01"
    pg_user = "alfonsod"
    pg_password = "securepassword123"
    resource_group = "adv_data_rg"
    storage_account = "advpsqlstorage"
    storage_container = "backups"
} | ConvertTo-Json

try {
    Write-Host "Enviando solicitud para ejecutar workflow..."
    $executeResponse = Invoke-RestMethod -Method Post `
        -Uri "https://$apiUrl/api/workflow/dump-restore?code=$functionKey" `
        -Body $body `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "Respuesta: $($executeResponse.message)" -ForegroundColor Green
    Write-Host "URL del workflow: $($executeResponse.workflowUrl)" -ForegroundColor Cyan
}
catch {
    Write-Host "Error al ejecutar workflow: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Detalles del error: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

# 4. Verificar estado del workflow (último ejecutado)
Write-Host "`n===== Verificar estado del último workflow =====`n" -ForegroundColor Green
try {
    $statusResponse = Invoke-RestMethod -Uri "https://$apiUrl/api/workflow/status?code=$functionKey" -ErrorAction Stop
    
    if ($statusResponse.message -eq "No workflow runs found") {
        Write-Host "No hay ejecuciones de workflow disponibles." -ForegroundColor Yellow
    }
    else {
        Write-Host "ID: $($statusResponse.id)"
        Write-Host "Nombre: $($statusResponse.name)"
        Write-Host "Estado: $($statusResponse.status)" -ForegroundColor $(
            if ($statusResponse.status -eq "completed" -and $statusResponse.conclusion -eq "success") { "Green" } 
            elseif ($statusResponse.status -eq "in_progress") { "Yellow" } 
            else { "Red" }
        )
        if ($statusResponse.conclusion) {
            Write-Host "Conclusión: $($statusResponse.conclusion)" -ForegroundColor $(
                if ($statusResponse.conclusion -eq "success") { "Green" } 
                else { "Red" }
            )
        }
        Write-Host "URL: $($statusResponse.html_url)"
        
        # Mostrar jobs si existen
        if ($statusResponse.jobs -and $statusResponse.jobs.Count -gt 0) {
            Write-Host "`nJobs:" -ForegroundColor Yellow
            foreach ($job in $statusResponse.jobs) {
                Write-Host "  - $($job.name): $($job.status)" -ForegroundColor $(
                    if ($job.status -eq "completed" -and $job.conclusion -eq "success") { "Green" } 
                    elseif ($job.status -eq "in_progress") { "Yellow" } 
                    else { "Red" }
                )
            }
        }
    }
}
catch {
    Write-Host "Error al verificar estado del workflow: $_" -ForegroundColor Red
}

# 5. Verificar estado de un workflow específico
# Para usar, descomenta y reemplaza RUN_ID por el ID real del workflow
<#
Write-Host "`n===== Verificar estado de un workflow específico =====`n" -ForegroundColor Green
$runId = "12345678"  # Reemplazar con el ID real del workflow

try {
    $specificStatusResponse = Invoke-RestMethod -Uri "https://$apiUrl/api/workflow/status?run_id=$runId&code=$functionKey" -ErrorAction Stop
    
    Write-Host "ID: $($specificStatusResponse.id)"
    Write-Host "Nombre: $($specificStatusResponse.name)"
    Write-Host "Estado: $($specificStatusResponse.status)"
    Write-Host "Conclusión: $($specificStatusResponse.conclusion)"
    Write-Host "URL: $($specificStatusResponse.html_url)"
}
catch {
    Write-Host "Error al verificar estado del workflow específico: $_" -ForegroundColor Red
}
#>

# Limpiar la variable que contiene la clave para seguridad
$functionKey = $null
[System.GC]::Collect()
