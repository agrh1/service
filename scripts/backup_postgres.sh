#!/usr/bin/env sh
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-/backups}
BACKUP_NAME=${BACKUP_NAME:-postgres_$(date +%Y%m%d_%H%M%S).sql}
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-microservices}
POSTGRES_DB=${POSTGRES_DB:-microservices_db}
PGPASSWORD=${POSTGRES_PASSWORD:-microservices}

export PGPASSWORD

mkdir -p "${BACKUP_DIR}"

pg_dump --host="${POSTGRES_HOST}" --port="${POSTGRES_PORT}" --username="${POSTGRES_USER}" "${POSTGRES_DB}" > "${BACKUP_DIR}/${BACKUP_NAME}"

find "${BACKUP_DIR}" -type f -mtime +${BACKUP_RETENTION_DAYS:-7} -name 'postgres_*.sql' -delete

printf "Backup stored at %s/%s\n" "${BACKUP_DIR}" "${BACKUP_NAME}"
