# Part 1: Permission-Aware RAG

Retrieval-augmented generation puts a company's documents behind a chatbot, and
the quick version leaks: a vector index returns what is *closest* to a question,
not what the asker is *allowed* to see. This lab takes a small RAG service over
Postgres + [pgvector](https://github.com/pgvector/pgvector), attacks it six ways,
then adds five protections and measures each until every leak is closed.

Everything runs locally in two containers. The embedding is deterministic and
there is no model in the loop, so every retrieval and every attack is
reproducible, and the lessons stay on the retrieval boundary instead of on
coaxing a model.

---

## Lessons (read in order)

1. [The Permission Problem in RAG](lessons/01-overview.md)
2. [Setup](lessons/02-setup.md)
3. [Attacking the Service](lessons/03-attacks.md)
4. [Who Is Asking: Authentication](lessons/04-auth.md)
5. [Scope Retrieval to the User](lessons/05-scope-retrieval.md)
6. [Enforce It in the Database](lessons/06-row-level-security.md)
7. [Poisoned Documents](lessons/07-poisoned-documents.md)
8. [The Scoreboard](lessons/08-scoreboard.md)
9. [Conclusion](lessons/09-conclusion.md)

---

## Quick start

```bash
bin/setup_secrets.sh
docker compose up -d --build
bin/smoke_test.sh
python3 attacks/run_attacks.py     # 6 of 6 attacks leak, undefended
bin/scoreboard.sh                  # turn on defenses one at a time, watch them close
```

| Command | What |
|---|---|
| `bin/rag.sh <alice\|bob\|carol\|none> search '<q>'` | retrieve chunks as a user |
| `bin/rag.sh <user> ask '<q>' [as_user]` | ask a question; `as_user` spoofs identity |
| `bin/rag.sh <user> raw '<q>'` | hit the endpoint that forgot its ACL filter |
| `bin/defend.sh <name> on` | turn on a protection (auth, acl, identity, rls, sanitize) |
| `bin/scoreboard.sh` | attacks after each defense, the whole progression |
| `bin/db_shell.sh "SELECT ..."` | run a query against the lab database |

## The scoreboard

| Level | Defense added | Attacks leaking |
|------:|---|:---:|
| 0 | none | **6** |
| 1 | require auth | **5** |
| 2 | scope retrieval (ACL filter) | **3** |
| 3 | identity from the token, not the body | **2** |
| 4 | row-level security | **1** |
| 5 | sanitize retrieved text | **0** |

## Requirements
- Docker with Compose v2, `python3`, and `curl`
- About 2 GB of memory free for Postgres
- No model, GPU, or cloud account

Pairs with [Secure AI Agents](https://github.com/JacksonHolmes01/Training-Module-Secure-AI-Agents)
(securing the actions an AI takes) and
[Secure an MCP Server](https://github.com/JacksonHolmes01/Training-Module-Secure-MCP-Server)
(securing the tools it connects to).

License: code is MIT, lessons are CC BY-SA 4.0. See [README-LICENSE.md](../README-LICENSE.md).
