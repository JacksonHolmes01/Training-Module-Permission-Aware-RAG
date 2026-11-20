#!/usr/bin/env bash
# Talk to the RAG service as a user.
#   bin/rag.sh <alice|bob|carol|none> search '<query>'
#   bin/rag.sh <user|none> raw    '<query>'          # the no-filter endpoint
#   bin/rag.sh <user|none> ask    '<query>' [as_user] # as_user spoofs identity
set -euo pipefail
cd "$(dirname "$0")/.."
who="${1:?user or none}"; verb="${2:?search|raw|ask}"; query="${3:-}"; as_user="${4:-}"

AUTH=()
if [[ "$who" != "none" ]]; then
  tok="$(cat "secrets/token_$who.txt" 2>/dev/null || true)"
  [[ -n "$tok" ]] || { echo "no token for '$who' (run bin/setup_secrets.sh)"; exit 1; }
  AUTH=(-H "Authorization: Bearer $tok")
fi

case "$verb" in
  search) path=/search; body=$(printf '{"query":%s}' "$(printf '%s' "$query" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')");;
  raw)    path=/search_raw; body=$(printf '{"query":%s}' "$(printf '%s' "$query" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')");;
  ask)
    if [[ -n "$as_user" ]]; then
      body=$(QUERY="$query" AS="$as_user" python3 -c 'import json,os;print(json.dumps({"query":os.environ["QUERY"],"user_id":os.environ["AS"]}))')
    else
      body=$(QUERY="$query" python3 -c 'import json,os;print(json.dumps({"query":os.environ["QUERY"]}))')
    fi
    path=/ask;;
  *) echo "verb must be search, raw, or ask"; exit 1;;
esac

curl -s ${AUTH[@]+"${AUTH[@]}"} -H "Content-Type: application/json" \
  -d "$body" "http://localhost:8000$path" | python3 -m json.tool
