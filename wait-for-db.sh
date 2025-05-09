#!/bin/bash
# wait-for-db.sh - Wait for the PostgreSQL database to be ready

set -e

host="$1"
user="$2"
database="$3"
shift 3
cmd="$@"

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -U "$user" -d "$database" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd