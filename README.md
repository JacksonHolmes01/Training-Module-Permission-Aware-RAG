# Permission-Aware RAG: A Hands-On Lab

Retrieval-augmented generation (RAG) is how most teams put their own documents
behind an AI chatbot. The quick version has a quiet, serious flaw: a vector index
returns the chunks *closest* to a question, not the chunks the asker is *allowed*
to see. Put two people's documents in one index and the right question hands
private text to the wrong person. Nobody broke in.

This lab makes that failure concrete and then fixes it. You take a small RAG
service over Postgres + [pgvector](https://github.com/pgvector/pgvector),
**attack it six ways** (anonymous access, cross-user retrieval, identity
spoofing, an endpoint that forgot its filter, and a poisoned document), then add
**five protections** and measure each until every leak is closed.

Everything runs locally in two Docker containers. The embedding is deterministic
and there is no language model in the loop, so every retrieval and every attack
is reproducible, and the focus stays on the one thing that matters here: the
retrieval permission boundary.

## Get started

```bash
git clone https://github.com/JacksonHolmes01/Training-Module-Permission-Aware-RAG.git
cd Training-Module-Permission-Aware-RAG/part-1-permission-aware-rag
```

Then open [Part 1](part-1-permission-aware-rag/README.md).

## The scoreboard

| Level | Defense added | Attacks leaking |
|------:|---|:---:|
| 0 | none | **6** |
| 1 | require auth | **5** |
| 2 | scope retrieval (ACL filter) | **3** |
| 3 | identity from the token, not the body | **2** |
| 4 | row-level security | **1** |
| 5 | sanitize retrieved text | **0** |

Every defense removes at least one attack; no single defense removes all of
them. Security is the stack, not any one switch.

## Related

This lab secures the **data** an AI retrieves. Its companions secure the rest of
an AI system:

- [Secure AI Agents](https://github.com/JacksonHolmes01/Training-Module-Secure-AI-Agents):
  the **actions** an agent takes, build, attack, defend, contain, monitor.
- [Secure an MCP Server](https://github.com/JacksonHolmes01/Training-Module-Secure-MCP-Server):
  the **tools** a model connects to over the Model Context Protocol.

Real systems need all three secured.

## License

Code is **MIT**. Lessons are **CC BY-SA 4.0**. See [README-LICENSE.md](README-LICENSE.md).
