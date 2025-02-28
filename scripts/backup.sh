#!/bin/bash
set -e

# Variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${PG_DATABASE}_${TIMESTAMP}.dump"

echo "Starting backup of ${PG_DATABASE} from ${PG_HOST_PROD}..."

# Create backup using pg_dump
PGPASSWORD=$PG_PASSWORD pg_dump -h ${PG_HOST_PROD}.postgres.database.azure.com -U $PG_USER -d $PG_DATABASE -F c -b -v -f /tmp/db_backup.dump

echo "Backup completed successfully."

# Upload to Azure Storage
echo "Uploading backup to Azure Storage..."
az storage blob upload \
  --account-name ${AZURE_STORAGE_ACCOUNT} \
  --container-name ${AZURE_STORAGE_CONTAINER} \
  --name ${BACKUP_FILE} \
  --file /tmp/db_backup.dump \
  --auth-mode login

echo "Backup uploaded successfully to ${AZURE_STORAGE_ACCOUNT}/${AZURE_STORAGE_CONTAINER}/${BACKUP_FILE}"

# Store the backup filename for the restore step
echo "BACKUP_FILE=${BACKUP_FILE}" >> $GITHUB_ENV