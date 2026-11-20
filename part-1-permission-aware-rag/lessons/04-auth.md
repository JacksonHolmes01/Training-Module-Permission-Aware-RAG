# 4. Who Is Asking: Authentication

You cannot scope retrieval to a user until you know which user is asking. So the
first defense is the cheapest one: require a valid token on every request.

```bash
bin/defend.sh auth on
```

This sets `RAG_AUTH=true` and restarts the service. Now re-run the attacks:

```bash
python3 attacks/run_attacks.py
```

```
no-auth            secure     rejected without a token
cross-user         LEAK       Bob's answer contained Alice's salary
...
5 of 6 attacks leaked.
```

One down. The anonymous caller is turned away.

## What changed

In `rag-api/app/main.py`, every endpoint starts by identifying the caller:

```python
user = identity.identify(_bearer(request))
if guards.on("RAG_AUTH") and user is None:
    return {"error": "unauthorized: a valid user token is required"}
```

`identity.identify` (in `identity.py`) looks up the bearer token and returns the
username it belongs to, or `None`. With `RAG_AUTH` on, `None` is a closed door.

## Why this alone fixes almost nothing

Look at the scoreboard again: auth stopped the *anonymous* attack and nothing
else. Bob still read Alice's salary. Carol's memo still leaked. That is the point
worth sitting with.

Authentication answers "are you a known user?" It does not answer "are you
allowed to see this document?" Those are different questions, and conflating them
is one of the most common security bugs there is. A logged-in user is not an
authorized user. Every one of the remaining five leaks happens to a caller who
passed authentication cleanly.

Auth is a prerequisite, not a protection. It gives you a trustworthy name to
make decisions about. Making those decisions is the next lesson.

Next: [Scope Retrieval to the User](05-scope-retrieval.md).
