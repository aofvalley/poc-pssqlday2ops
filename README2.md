# PostgreSQL Backup and Restore

This project provides a GitHub Actions workflow to automate the backup and restore of a PostgreSQL database named `test01` hosted on Azure PostgreSQL Flexible Servers. The backup is stored in an Azure Storage Account, and the restore process can be executed to another Azure PostgreSQL Flexible Server.

## Project Structure

```
postgres-backup-restore
├── .github
│   └── workflows
│       └── pg-backup-restore.yml  # GitHub Actions workflow for backup and restore
├── scripts
│   ├── backup.sh                   # Script to backup the PostgreSQL database
│   └── restore.sh                  # Script to restore the PostgreSQL database
├── .env.example                    # Template for environment variables
└── README.md                       # Project documentation
```

## Prerequisites

- PostgreSQL client tools installed (`pg_dump` and `pg_restore`).
- Access to Azure PostgreSQL Flexible Servers.
- An Azure Storage Account for storing backups.
- GitHub repository with Actions enabled.

## Environment Variables

Create a `.env` file in the root directory based on the `.env.example` template. The following variables should be defined:

- `PG_HOST_PROD`: Hostname of the production PostgreSQL server (e.g., `prodpssql01`).
- `PG_HOST_DEV`: Hostname of the development PostgreSQL server (e.g., `devpssql01`).
- `PG_DATABASE`: Name of the database to backup and restore (e.g., `test01`).
- `PG_USER`: PostgreSQL username.
- `PG_PASSWORD`: PostgreSQL password.
- `AZURE_STORAGE_ACCOUNT`: Name of the Azure Storage Account (e.g., `pssqlstorage`).
- `AZURE_STORAGE_CONTAINER`: Name of the container in the Azure Storage Account where backups will be stored.

## Usage

### Backup

To perform a backup of the PostgreSQL database, run the `backup.sh` script:

```bash
bash scripts/backup.sh
```

This script will create a backup of the `test01` database from the `prodpssql01` server and upload it to the specified Azure Storage Account.

### Restore

To restore the PostgreSQL database, run the `restore.sh` script:

```bash
bash scripts/restore.sh
```

This script will restore the `test01` database to the `devpssql01` server from the backup file stored in the Azure Storage Account.

## GitHub Actions Workflow

The GitHub Actions workflow defined in `.github/workflows/pg-backup-restore.yml` automates the backup and restore process. It can be triggered manually or set to run on a schedule.

## Step-by-Step Implementation Guide

### 1. Configure the Repository

1. Create a new repository in GitHub or use an existing one
2. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/your-username/repository-name.git
   cd repository-name
   ```

### 2. Create the Directory Structure

Create the following structure of directories and files:

```
.
├── .github/
│   └── workflows/
│       └── pg-backup-restore.yml
├── scripts/
│   ├── backup.sh
│   └── restore.sh
├── .env.example
└── README.md
```

### 3. Create the Required Files

#### GitHub Actions Workflow File

Create the following file at `.github/workflows/pg-backup-restore.yml`:

```yaml
name: PostgreSQL Backup and Restore

on:
  workflow_dispatch:  # For manual activation
  schedule:
    - cron: '0 2 * * *'  # Runs daily at 2 AM UTC

jobs:
  backup-restore:
    runs-on: ubuntu-latest
    
    steps:
      - name: Check out repository code
        uses: actions/checkout@v3
        
      - name: Install PostgreSQL client tools
        run: |
          sudo apt-get update
          sudo apt-get install -y postgresql-client
          
      - name: Install Azure CLI
        run: |
          curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
          
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
          
      - name: Set environment variables
        run: |
          echo "PG_HOST_PROD=${{ secrets.PG_HOST_PROD }}" >> $GITHUB_ENV
          echo "PG_HOST_DEV=${{ secrets.PG_HOST_DEV }}" >> $GITHUB_ENV
          echo "PG_DATABASE=${{ secrets.PG_DATABASE }}" >> $GITHUB_ENV
          echo "PG_USER=${{ secrets.PG_USER }}" >> $GITHUB_ENV
          echo "PG_PASSWORD=${{ secrets.PG_PASSWORD }}" >> $GITHUB_ENV
          echo "AZURE_STORAGE_ACCOUNT=${{ secrets.AZURE_STORAGE_ACCOUNT }}" >> $GITHUB_ENV
          echo "AZURE_STORAGE_CONTAINER=${{ secrets.AZURE_STORAGE_CONTAINER }}" >> $GITHUB_ENV
          echo "PGPASSWORD=${{ secrets.PG_PASSWORD }}" >> $GITHUB_ENV
      
      - name: Create backup
        run: |
          chmod +x ./scripts/backup.sh
          ./scripts/backup.sh
        
      - name: Restore from backup
        run: |
          chmod +x ./scripts/restore.sh
          ./scripts/restore.sh
```

#### Backup Script

Create the following file at `scripts/backup.sh`:

```bash
#!/bin/bash
set -e

# Variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${PG_DATABASE}_${TIMESTAMP}.dump"

echo "Starting backup of ${PG_DATABASE} from ${PG_HOST_PROD}..."

# Create backup using pg_dump
pg_dump -h ${PG_HOST_PROD}.postgres.database.azure.com -U ${PG_USER} \
  -d ${PG_DATABASE} -F c -b -v -f ${BACKUP_FILE}

echo "Backup completed successfully."

# Upload to Azure Storage
echo "Uploading backup to Azure Storage..."
az storage blob upload \
  --account-name ${AZURE_STORAGE_ACCOUNT} \
  --container-name ${AZURE_STORAGE_CONTAINER} \
  --name ${BACKUP_FILE} \
  --file ${BACKUP_FILE} \
  --auth-mode login

echo "Backup uploaded successfully to ${AZURE_STORAGE_ACCOUNT}/${AZURE_STORAGE_CONTAINER}/${BACKUP_FILE}"

# Store the backup filename for the restore step
echo "BACKUP_FILE=${BACKUP_FILE}" >> $GITHUB_ENV
```

#### Restore Script

Create the following file at `scripts/restore.sh`:

```bash
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
```

#### Environment Variables Template

Create the following file at `.env.example`:

```
PG_HOST_PROD=prodpssql01
PG_HOST_DEV=devpssql01
PG_DATABASE=test01
PG_USER=postgres
PG_PASSWORD=your_password_here
AZURE_STORAGE_ACCOUNT=pssqlstorage
AZURE_STORAGE_CONTAINER=backups
```

### 4. Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Create the following secrets:
   - `PG_HOST_PROD`: Production PostgreSQL server name
   - `PG_HOST_DEV`: Development PostgreSQL server name
   - `PG_DATABASE`: Database name
   - `PG_USER`: PostgreSQL username
   - `PG_PASSWORD`: PostgreSQL password
   - `AZURE_STORAGE_ACCOUNT`: Storage account name
   - `AZURE_STORAGE_CONTAINER`: Container name
   - `AZURE_CREDENTIALS`: JSON with Azure Service Principal credentials

### 5. Create Azure Service Principal

Run the following command to create a service principal with appropriate permissions:

```bash
az ad sp create-for-rbac --name "PG-Backup-Restore" --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth
```

Save the JSON output as the `AZURE_CREDENTIALS` secret in GitHub.

### 6. Commit and Push Changes

```bash
git add .
git commit -m "Add PostgreSQL backup and restore workflow"
git push origin main
```

### 7. Run the Workflow

1. Go to the "Actions" tab in your GitHub repository
2. Select "PostgreSQL Backup and Restore" from the sidebar
3. Click "Run workflow" > "Run workflow"

The workflow will run automatically based on the schedule (cron) or you can trigger it manually.

### 8. Verify Results

After the workflow completes:

1. Check the logs to verify that the backup and restore completed successfully
2. Verify the storage account to confirm that the backup file was uploaded
3. Connect to the development server to confirm that the data was properly restored

## License

This project is licensed under the MIT License. See the LICENSE file for more details.