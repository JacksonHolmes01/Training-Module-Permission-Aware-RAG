#!/usr/bin/env bash
# Creates the database passwords, the per-user tokens, and .env.
# Safe to run more than once: existing secrets are kept.
set -euo pipefail
cd "$(dirname "$0")/.."
gen() { openssl rand -base64 36 | tr -d '/+=\n' | cut -c1-32; }
mkdir -p secrets
for s in postgres_password db_app_password token_alice token_bob token_carol; do
  f="secrets/$s.txt"
  [[ -s "$f" ]] && echo "  kept     $f" || { gen > "$f"; echo "  created  $f"; }
done
chmod 600 secrets/*.txt
[[ -f .env ]] || { cp .env.example .env; echo "  created  .env"; }
chmod 600 .env
echo "Secrets ready."
