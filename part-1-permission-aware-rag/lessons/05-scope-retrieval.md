# 5. Scope Retrieval to the User

This lesson closes three of the five remaining leaks, and it is the heart of the
whole lab. It has two halves: scope the retrieval, then make sure you scope it to
the *real* user.

## Half one: the access filter

Turn on the ACL filter:

```bash
bin/defend.sh acl on
python3 attacks/run_attacks.py
```

```
cross-user         secure     scoped out of Alice's document
secret-in-search   secure     scoped out of Alice's document
spoofed-identity   LEAK       body user_id let Bob read as Carol
...
3 of 6 attacks leaked.
```

Two leaks gone at once, both the `/ask` and the `/search` version of reading
someone else's document. Bob's question about Alice's salary now comes back with
Bob's own documents and the org-wide ones, and Alice's comp plan is simply not
in the result set.

The change is a `WHERE` clause on the retrieval query (`rag-api/app/db.py`):

```sql
SELECT ... FROM chunks
WHERE (visibility = 'org' OR owner = %s OR %s = ANY(acl))
ORDER BY embedding <=> %s::vector
LIMIT %s
```

Read the filter in plain words: return a chunk if it is shared with the whole
org, **or** the caller owns it, **or** the caller is on its access list. This is
the rule from Lesson 1, finally written down. Notice where it sits: it runs
*inside* the retrieval query, so a forbidden chunk is never a candidate. A
common mistake is to retrieve first and filter afterward in Python, which still
pulls the private text out of the database and often still ranks it, ready to
leak through a log line or an off-by-one. Filter in the query.

Confirm the legitimate path still works. Bob is on the access list for Alice's
Q1 forecast:

```bash
bin/rag.sh bob ask 'sales forecast first quarter pipeline'
```

He still gets it. Scoping is about returning the right documents, not the fewest.

## Half two: trust the token, not the request

One leak in that run got *worse*-looking, not better: `spoofed-identity` still
leaks. Here is why. The filter above scopes to a user, but which user? Look at
how the service decided, before this half:

```python
def _effective_user(token_user, body):
    if guards.on("RAG_IDENTITY"):
        return token_user
    return body.get("user_id") or token_user    # trusts the body
```

With only the ACL filter on, the service scopes retrieval to
`body["user_id"]` if the caller sent one. So Bob sends `"user_id": "carol"`, the
filter faithfully scopes to Carol, and hands Bob Carol's documents. The filter is
working perfectly. It is just pointed at an identity the attacker chose.

Close it:

```bash
bin/defend.sh identity on
python3 attacks/run_attacks.py
```

```
spoofed-identity   secure     identity taken from the token, not the body
...
2 of 6 attacks leaked.
```

Now `_effective_user` returns the token's user and ignores the body entirely.
This is the **trust boundary**: the identity that drives an access decision must
come from something the caller cannot forge (a verified token), never from a
field in the request they fill in themselves. A `user_id` in a request body is a
claim. Treating a claim as a credential is how "permission-aware" systems leak
while looking correct in every demo, because in a demo nobody lies about who
they are.

Three leaks closed, two to go. Both of the remaining ones get past everything in
this lesson, for different reasons, and the next two lessons are about why.

Next: [Enforce It in the Database](06-row-level-security.md).
