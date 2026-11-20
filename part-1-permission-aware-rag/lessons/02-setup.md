# 2. Setup

## Requirements

- Docker with Compose v2 (`docker compose version`)
- `python3` and `curl`
- About 2 GB of memory free for the Postgres container

No model, no GPU, no cloud account. Everything runs on your machine.

## Start the lab

From `part-1-permission-aware-rag/`:

```bash
bin/setup_secrets.sh          # database passwords + one token per user
docker compose up -d --build  # Postgres (pgvector) + the RAG service
bin/smoke_test.sh             # confirm it is up and the corpus loaded
```

`setup_secrets.sh` writes six files into `secrets/`: the Postgres superuser
password, a password for the restricted database role the service uses later,
and a token for Alice, Bob, and Carol. These are git-ignored. On first startup
the service creates the table, seeds the eleven documents from `corpus/`, and
computes an embedding for each.

Check the health endpoint:

```bash
curl -s localhost:8000/health
```

```json
{"ok": true, "chunks": 11, "guards": {"RAG_AUTH": false, "RAG_ACL": false,
 "RAG_IDENTITY": false, "RAG_RLS": false, "RAG_SANITIZE": false}}
```

Every guard starts `false`. The service begins as the trusting chatbot from
Lesson 1, and you will turn the guards on one at a time.

## Talking to the service

`bin/rag.sh` is a thin wrapper over `curl` that attaches a user's token:

```bash
# Ask a question as Bob
bin/rag.sh bob ask 'what are the support hours'

# Retrieve raw chunks as Alice
bin/rag.sh alice search 'paid time off'

# Ask with no token at all
bin/rag.sh none ask 'what are the support hours'
```

Try a legitimate question now:

```bash
bin/rag.sh bob ask 'how do I report phishing'
```

Bob gets the org-wide security policy back. That is retrieval working as
intended. In the next lesson you will ask for things Bob should not get, and the
service will hand them over.

## The corpus

Open `corpus/documents.json` to see who owns what. A few to notice:

- **Alice Compensation Plan 2026** (private to Alice): contains a salary figure.
- **Project Atlas Acquisition Memo** (private to Carol): names an acquisition
  target and a price.
- **Sales Forecast Q1** (Alice's, shared with Bob through its access list): the
  one private document Bob is genuinely allowed to read.
- **Partner Update** (org-wide): looks harmless, but read it to the end.

Next: [Attacking the Service](03-attacks.md).
