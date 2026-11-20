#!/usr/bin/env bash
# Turn the service's defenses on or off, then restart the API.
#   bin/defend.sh status | <name> on|off | all on|off | level <0-5>
# Names: auth acl identity rls sanitize
set -euo pipefail
cd "$(dirname "$0")/.."
ORDER=(AUTH ACL IDENTITY RLS SANITIZE)
setv(){ if grep -qE "^RAG_$1=" .env; then sed -i.bak "s/^RAG_$1=.*/RAG_$1=$2/" .env && rm -f .env.bak; else echo "RAG_$1=$2">>.env; fi; }
restart(){ docker compose up -d rag-api >/dev/null 2>&1; for i in $(seq 1 30); do curl -s localhost:8000/health|grep -q '"ok":true'&&{ echo "Service ready.";return;};sleep 2;done;echo "not up";exit 1; }
case "${1:-}" in
  status) grep -E '^RAG_' .env|sed 's/^/  /';exit 0;;
  level) n="${2:?0-5}"; for i in "${!ORDER[@]}"; do [[ $i -lt $n ]]&&setv "${ORDER[$i]}" true||setv "${ORDER[$i]}" false;done; restart;;
  all) v=$([[ "${2:-}" == on ]]&&echo true||echo false); for d in "${ORDER[@]}";do setv "$d" "$v";done; restart;;
  auth|acl|identity|rls|sanitize) v=$([[ "${2:-}" == on ]]&&echo true||echo false); setv "$(echo "$1"|tr a-z A-Z)" "$v"; restart;;
  *) echo "usage: bin/defend.sh status|<name> on|off|all on|off|level N";exit 1;;
esac
