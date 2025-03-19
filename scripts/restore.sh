#!/bin/bash
#
# PostgreSQL Database Restore Script
# 
# Este script descarga un backup de Azure Storage y lo restaura en un servidor PostgreSQL.
#
# Requisitos:
#   - pg_restore y psql instalados
#   - Azure CLI instalado y configurado
#   - Variables de entorno configuradas:
#     - PG_HOST_DEV: Hostname del servidor PostgreSQL de destino
#     - PG_USER: Usuario de PostgreSQL
#     - PG_PASSWORD: Contraseña del usuario
#     - PG_DATABASE: Nombre de la base de datos a restaurar
#     - AZURE_STORAGE_ACCOUNT: Nombre de la cuenta de almacenamiento
#     - AZURE_STORAGE_CONTAINER: Nombre del contenedor
#     - BACKUP_FILE: Nombre del archivo de backup a descargar

set -e

echo "Starting restore of ${PG_DATABASE} to ${PG_HOST_DEV}..."

# Verificar variables de entorno requeridas
required_vars=("PG_HOST_DEV" "PG_USER" "PG_PASSWORD" "PG_DATABASE" "AZURE_STORAGE_ACCOUNT" "AZURE_STORAGE_CONTAINER" "BACKUP_FILE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        echo "Make sure all required parameters are provided in the GitHub workflow inputs"
        exit 1
    fi
done

# Download from Azure Storage
echo "Downloading backup ${BACKUP_FILE} from Azure Storage account ${AZURE_STORAGE_ACCOUNT} in container ${AZURE_STORAGE_CONTAINER}..."
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
    echo "Download attempt $i of $MAX_RETRIES..."
    
    az storage blob download \
      --account-name ${AZURE_STORAGE_ACCOUNT} \
      --container-name ${AZURE_STORAGE_CONTAINER} \
      --name ${BACKUP_FILE} \
      --file ${BACKUP_FILE} \
      --auth-mode login && download_success=true && break
    
    download_success=false
    echo "Download attempt failed, retrying in 10 seconds..."
    sleep 10
done

if [ "$download_success" != "true" ]; then
    echo "Error: Failed to download backup after $MAX_RETRIES attempts"
    exit 1
fi

echo "Backup downloaded successfully."

# Drop and recreate database
echo "Connecting to ${PG_HOST_DEV}.postgres.database.azure.com with user ${PG_USER}..."
echo "Dropping existing database ${PG_DATABASE} if it exists..."
if ! PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} postgres -c "DROP DATABASE IF EXISTS ${PG_DATABASE} WITH (FORCE);" ; then
    echo "Error: Failed to drop database ${PG_DATABASE}"
    exit 1
fi

echo "Creating fresh database..."
if ! PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} postgres -c "CREATE DATABASE ${PG_DATABASE};" ; then
    echo "Error: Failed to create database ${PG_DATABASE}"
    exit 1
fi

# Restore using pg_restore
echo "Restoring database ${PG_DATABASE} from backup file ${BACKUP_FILE}..."
if ! PGPASSWORD=${PG_PASSWORD} pg_restore -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} -d ${PG_DATABASE} -v ${BACKUP_FILE} ; then
    echo "Warning: pg_restore completed with warnings or errors. Check the output above for details."
    # No salimos con error porque pg_restore puede terminar con código distinto de 0 pero la base de datos
    # aún así puede estar restaurada correctamente con algunas advertencias
fi

# Verificar que la base de datos contiene datos
echo "Verifying restored database..."
tables_count=$(PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} -d ${PG_DATABASE} -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
if [ -z "$tables_count" ] || [ "$tables_count" -eq "0" ]; then
    echo "Warning: The restored database appears to be empty. Verify that the backup was valid."
else
    echo "Database verified: $tables_count tables found."
fi

# Limpiar archivos
echo "Cleaning up temporary files..."
rm -f ${BACKUP_FILE}

echo "Restore completed successfully."