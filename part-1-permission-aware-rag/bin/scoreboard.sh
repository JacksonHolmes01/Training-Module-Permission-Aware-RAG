#!/usr/bin/env bash
# Turn on the defenses one at a time and re-run the attacks after each.
set -euo pipefail
cd "$(dirname "$0")/.."
LEVELS=(
  "0 none (baseline)"
  "1 + require auth"
  "2 + scope retrieval to the user (ACL filter)"
  "3 + take identity from the token, not the body"
  "4 + enforce it in the database (RLS)"
  "5 + sanitize retrieved text"
)
for e in "${LEVELS[@]}"; do
  n="${e%% *}"; label="${e#* }"
  bin/defend.sh level "$n" >/dev/null
  echo "==== Level $label"
  python3 attacks/run_attacks.py | grep -E 'LEAK|secure|leaked'
  echo
done
