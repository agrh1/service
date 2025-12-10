#!/usr/bin/env sh
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: restore_postgres.sh <backup_file>" >&2
  exit 1
fi

BACKUP_FILE=$1
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-microservices}
POSTGRES_DB=${POSTGRES_DB:-microservices_db}
PGPASSWORD=${POSTGRES_PASSWORD:-microservices}

export PGPASSWORD

psql --host="${POSTGRES_HOST}" --port="${POSTGRES_PORT}" --username="${POSTGRES_USER}" "${POSTGRES_DB}" < "${BACKUP_FILE}"
