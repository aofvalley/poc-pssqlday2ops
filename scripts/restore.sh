#!/bin/bash
set -e

echo "Starting restore of ${PG_DATABASE} to ${PG_HOST_DEV}..."

# Download from Azure Storage
echo "Downloading backup from Azure Storage..."
az storage blob download \
  --account-name ${AZURE_STORAGE_ACCOUNT} \
  --container-name ${AZURE_STORAGE_CONTAINER} \
  --name ${BACKUP_FILE} \
  --file ${BACKUP_FILE} \
  --auth-mode login

echo "Backup downloaded successfully."

# Drop and recreate database
echo "Dropping existing database if it exists..."
PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} postgres -c "DROP DATABASE IF EXISTS ${PG_DATABASE} WITH (FORCE);"

echo "Creating fresh database..."
PGPASSWORD=${PG_PASSWORD} psql -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} postgres -c "CREATE DATABASE ${PG_DATABASE};"

# Restore using pg_restore
echo "Restoring database from backup..."
pg_restore -h ${PG_HOST_DEV}.postgres.database.azure.com -U ${PG_USER} \
  -d ${PG_DATABASE} -v ${BACKUP_FILE}

echo "Restore completed successfully."