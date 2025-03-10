#!/bin/bash
# Ejemplos de uso de la API PostgreSQL Backup & Restore con curl

# Configurar las variables de la API (reemplazar con los valores correctos)
API_URL=""
FUNCTION_KEY=""

# Solicitar la clave de función de forma segura
echo -n "Ingrese la clave de función: "
read -s FUNCTION_KEY
echo ""

# 1. Verificar el estado de salud del servicio
echo -e "\n===== Verificando estado de salud =====\n"
curl -s "https://$API_URL/api/health?code=$FUNCTION_KEY" | jq

# 2. Obtener configuración actual
echo -e "\n===== Obteniendo configuración =====\n"
curl -s "https://$API_URL/api/config?code=$FUNCTION_KEY" | jq

# 3. Ejecutar un workflow de backup/restore
echo -e "\n===== Ejecutar workflow de backup/restore =====\n"
curl -s -X POST "https://$API_URL/api/workflow/dump-restore?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pg_host_prod": "advpsqlfxuk",
    "pg_host_dev": "advpsqlfxukdev",
    "pg_database": "test01",
    "pg_user": "alfonsod",
    "resource_group": "adv_data_rg"
  }' | jq

# 4. Verificar estado del workflow (último ejecutado)
echo -e "\n===== Verificar estado del último workflow =====\n"
curl -s "https://$API_URL/api/workflow/status?code=$FUNCTION_KEY" | jq

# 5. Verificar estado de un workflow específico
# Para usar, descomenta y reemplaza RUN_ID por el ID real del workflow
#
# echo -e "\n===== Verificar estado de un workflow específico =====\n"
# RUN_ID="12345678"  # Reemplazar con el ID real del workflow
# curl -s "https://$API_URL/api/workflow/status?run_id=$RUN_ID&code=$FUNCTION_KEY" | jq

# Limpiar la variable que contiene la clave para seguridad
FUNCTION_KEY=""
