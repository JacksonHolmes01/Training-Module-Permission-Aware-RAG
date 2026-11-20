# 8. The Scoreboard

You have turned the defenses on one at a time. Now watch the whole progression
in one shot:

```bash
bin/scoreboard.sh
```

It runs the six attacks at each level, adding one defense each time:

| Level | Defense added | Attacks leaking |
|------:|---|:---:|
| 0 | none (baseline) | **6** |
| 1 | require auth | **5** |
| 2 | scope retrieval (ACL filter) | **3** |
| 3 | identity from the token, not the body | **2** |
| 4 | row-level security | **1** |
| 5 | sanitize retrieved text | **0** |

Read the drops, because each one carries the lesson:

- **6 to 5 (auth).** Only the anonymous attack died. Authentication tells you
  *who*, and nothing about *what they may see*. The smallest drop in the table is
  the defense people most often mistake for the whole job.
- **5 to 3 (scoping).** The biggest drop: two leaks at once. Scoping retrieval to
  the caller's own documents is the single highest-value control in a
  permission-aware RAG. It is also the one naive RAG skips entirely.
- **3 to 2 (trust boundary).** A scoping filter aimed at an identity the caller
  can forge is not a control. Identity has to come from the token.
- **2 to 1 (RLS).** The application filter never reached `/search_raw`. The
  database policy does, because it does not depend on any endpoint remembering to
  call it. This is defense in depth paying for itself.
- **1 to 0 (sanitizing).** A different class of attack: a document the caller is
  allowed to read, carrying instructions for the model that reads it. Scoping
  could never catch it; sanitizing does.

## The shape of the lesson

Every defense removed at least one attack, and no single defense removed all of
them. There is no one setting that makes a RAG system "secure." There is a stack:

1. know who is asking (auth),
2. return only what they may see (scope the query),
3. decide "who" from something unforgeable (trust the token),
4. enforce it where it cannot be bypassed (the database),
5. treat retrieved text as untrusted (sanitize).

Take any one away and a specific, nameable document walks out the door. You have
the attack that proves each one.

Next: [Conclusion](09-conclusion.md).
