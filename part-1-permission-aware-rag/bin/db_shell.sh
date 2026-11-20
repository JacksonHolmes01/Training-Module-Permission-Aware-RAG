#!/usr/bin/env bash
# Open a psql shell on the lab database (as the superuser).
#   bin/db_shell.sh                 interactive shell
#   bin/db_shell.sh "SELECT ..."    run one query
set -euo pipefail
cd "$(dirname "$0")/.."
pw="$(cat secrets/postgres_password.txt)"
if [[ -n "${1:-}" ]]; then
  docker compose exec -e PGPASSWORD="$pw" pgvector psql -U postgres -d raglab -c "$1"
else
  docker compose exec -e PGPASSWORD="$pw" pgvector psql -U postgres -d raglab
fi
