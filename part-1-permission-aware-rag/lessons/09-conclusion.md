# 9. Conclusion

You took a RAG service that leaked six ways and closed every leak, measuring each
defense against the attack it was meant to stop. The point was never the five
switches. It was the way of thinking they teach.

## What to carry out of here

**Similarity is not permission.** A vector index returns what is close, not what
is allowed. The moment more than one person's documents share an index, "most
relevant" and "permitted" are different sets, and retrieval that does not know
the difference will hand private text to whoever asks the right question. This is
the defining risk of multi-tenant RAG, and it is invisible in any demo with one
user.

**Authentication is not authorization.** Knowing who is calling is a
prerequisite for every access decision and is itself not one. Five of the six
attacks were carried out by a properly authenticated user.

**The identity that drives a decision must be unforgeable.** A username in a
request body is a claim. Scope to the token, never to a field the caller fills
in. A scoping filter pointed at a spoofable identity is theater.

**Enforce the rule where it cannot be skipped.** Application-level filters are
worth writing, for speed and for clarity, but code grows endpoints and endpoints
get forgotten. Row-Level Security in the database is the backstop that does not
depend on anyone remembering. Use both.

**Retrieved text is untrusted input.** A document the user may legitimately read
can still carry instructions aimed at the model downstream. Scoping cannot catch
that, because the document is permitted. Sanitize what you retrieve, and do not
hand the model tools it should not have.

## How this maps to a real system

The lab uses a deterministic embedding and no model so results are reproducible,
but every control moves straight to production:

- The token lookup is an identity provider or a signed session.
- The ACL filter is the `WHERE` clause on your real retrieval query, and the
  deterministic embedding is the only part you swap for a real one.
- RLS is a feature of Postgres (and has equivalents in other stores); the
  `app.current_user` session variable is how you carry the request's identity
  into the policy.
- Sanitizing is one layer of prompt-injection defense among several.

## Where to go next

This lab secured the **data** an AI system retrieves. Its companion,
[Secure AI Agents](https://github.com/JacksonHolmes01/Training-Module-Secure-AI-Agents),
secures the **actions** an AI system takes: build an agent, attack it, then
defend, contain, and monitor it. The poisoned document here tried to make a model
exfiltrate data by email; that lab is where you take the email tool away. And
[Secure an MCP Server](https://github.com/JacksonHolmes01/Training-Module-Secure-MCP-Server)
secures the **tools** a model connects to. Retrieval, actions, and tools: a real
AI system needs all three secured, and the same habits of mind run through every
one.

## Tear down

```bash
docker compose down -v
```

That removes the containers and the database volume. Re-running
`docker compose up -d --build` starts fresh and re-seeds the corpus.
