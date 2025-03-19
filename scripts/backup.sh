#!/bin/bash
#
# PostgreSQL Database Backup Script
# 
# Este script realiza un backup de una base de datos PostgreSQL y lo sube a Azure Storage.
# Incluye mecanismo de reintento para la carga a Azure Storage.
#
# Requisitos:
#   - pg_dump instalado
#   - Azure CLI instalado y configurado
#   - Variables de entorno configuradas:
#     - PG_HOST_PROD: Hostname del servidor PostgreSQL de producción
#     - PG_USER: Usuario de PostgreSQL
#     - PG_PASSWORD: Contraseña del usuario
#     - PG_DATABASE: Nombre de la base de datos a respaldar
#     - AZURE_STORAGE_ACCOUNT: Nombre de la cuenta de almacenamiento
#     - AZURE_STORAGE_CONTAINER: Nombre del contenedor

set -e

# Variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${PG_DATABASE}_${TIMESTAMP}.dump"

echo "Starting backup of ${PG_DATABASE} from ${PG_HOST_PROD}..."

# Verificar variables de entorno requeridas
required_vars=("PG_HOST_PROD" "PG_USER" "PG_PASSWORD" "PG_DATABASE" "AZURE_STORAGE_ACCOUNT" "AZURE_STORAGE_CONTAINER")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        echo "Make sure all required parameters are provided in the GitHub workflow inputs"
        exit 1
    fi
done

# Create backup using pg_dump
echo "Executing pg_dump with user $PG_USER on database $PG_DATABASE from server ${PG_HOST_PROD}.postgres.database.azure.com..."
PGPASSWORD=$PG_PASSWORD pg_dump -h ${PG_HOST_PROD}.postgres.database.azure.com -U $PG_USER -d $PG_DATABASE -F c -b -v -f /tmp/db_backup.dump

if [ $? -ne 0 ]; then
    echo "Error: pg_dump failed with exit code $?"
    exit 1
fi

echo "Backup completed successfully."

# Upload to Azure Storage with retry mechanism
echo "Uploading backup to Azure Storage account ${AZURE_STORAGE_ACCOUNT} in container ${AZURE_STORAGE_CONTAINER}..."
MAX_RETRIES=5
for i in $(seq 1 $MAX_RETRIES); do
    echo "Upload attempt $i of $MAX_RETRIES..."
    
    az storage blob upload \
        --account-name ${AZURE_STORAGE_ACCOUNT} \
        --container-name ${AZURE_STORAGE_CONTAINER} \
        --name ${BACKUP_FILE} \
        --file /tmp/db_backup.dump \
        --auth-mode login && upload_success=true && break
    
    upload_success=false
    echo "Upload attempt failed, retrying in 15 seconds..."
    sleep 15
done

if [ "$upload_success" != "true" ]; then
    echo "Error: Failed to upload backup after $MAX_RETRIES attempts"
    exit 1
fi

echo "Backup uploaded successfully to ${AZURE_STORAGE_ACCOUNT}/${AZURE_STORAGE_CONTAINER}/${BACKUP_FILE}"

# Store the backup filename for the restore step
echo "BACKUP_FILE=${BACKUP_FILE}" >> $GITHUB_ENV

# Cleanup temporary files
echo "Cleaning up temporary files..."
rm -f /tmp/db_backup.dump

echo "Backup process completed"