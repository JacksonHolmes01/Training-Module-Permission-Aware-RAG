#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
curl -s localhost:8000/health | grep -q '"ok":true' && echo "  ✔ service up" || { echo "  ✘ service down"; exit 1; }
curl -s localhost:8000/health | grep -qE '"chunks": ?1[01]' && echo "  ✔ corpus loaded" || { echo "  ✘ corpus not loaded"; exit 1; }
bin/rag.sh bob ask 'what are the support hours' | grep -qi "office hours" && echo "  ✔ retrieval works" || { echo "  ✘ retrieval failed"; exit 1; }
echo "All smoke tests passed."
