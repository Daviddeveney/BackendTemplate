#!/bin/bash

# Load environment variables
set -a
source ../.env
set +a

# Create backup directory if it doesn't exist
BACKUP_DIR="../backups/$(date +%Y-%m)"
mkdir -p $BACKUP_DIR

# Create backup filename with timestamp
BACKUP_FILENAME="$BACKUP_DIR/backup_$(date +%Y-%m-%d_%H-%M-%S).sql"

# Perform backup
docker-compose exec db pg_dump \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -F p \
    > $BACKUP_FILENAME

# Compress backup
gzip $BACKUP_FILENAME

# Remove backups older than 30 days
find ../backups -type f -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILENAME}.gz" 