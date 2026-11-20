# 6. Enforce It in the Database

Two leaks left. One of them, `rls-bypass`, has walked through every defense so
far untouched:

```bash
bin/rag.sh bob raw 'project atlas acquisition riverside robotics'
```

Carol's acquisition memo, handed to Bob, with auth on, the ACL filter on, and
identity locked to the token. How?

Because `/search_raw` does not have the filter. The `WHERE` clause from Lesson 5
lives in the code path for `/search` and `/ask`. The developer who added
`/search_raw` (for a dashboard, a batch job, an internal tool, pick your reason)
forgot it, and no amount of correctness in the *other* endpoints covers this one.

This is not a contrived bug. It is the single most common way permission-aware
systems leak in production: the rule is enforced in application code, application
code grows more entry points over time, and eventually one of them does not get
the rule. You cannot fix this by being more careful, because "be more careful on
every future endpoint forever" is not a control.

## Push the rule down to the data

The fix is to make the database itself refuse to return rows the caller may not
see, so that *any* query, filtered or not, is scoped. Postgres has exactly this:
**Row-Level Security** (RLS). You attach a policy to the table, and from then on
a restricted role simply cannot see rows outside the policy.

```bash
bin/defend.sh rls on
python3 attacks/run_attacks.py
```

```
rls-bypass         secure     database policy scoped the raw query
...
1 of 6 attacks leaked.
```

The raw, unfiltered query now comes back scoped, because the database scoped it.

## How it works

The policy is created once, at startup (`rag-api/app/db.py`):

```sql
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY chunk_visibility ON chunks FOR SELECT TO rag_app
USING (
    visibility = 'org'
    OR owner = current_setting('app.current_user', true)
    OR current_setting('app.current_user', true) = ANY(acl)
);
```

It is the same rule as the application filter, which is the point: the boundary
is now in two places, and a query has to get past both.

What `RAG_RLS` actually toggles is **which database role the service connects
as**:

- **off**: the service connects as the Postgres superuser, which bypasses RLS.
  This is the world of the earlier lessons, where only application code scoped
  anything.
- **on**: the service connects as `rag_app`, a restricted role the policy
  applies to, and runs `SET app.current_user = '<the token's user>'` so the
  policy knows whose rows to allow.

Because the policy is bound to the role and the session variable, it holds for
every query that role runs, the forgotten endpoint included. The application
filter from Lesson 5 is still there and still valuable (it keeps forbidden rows
from ever being candidates, and it keeps your intent visible in the code). RLS is
the backstop underneath it. **Defense in depth** is not a slogan here; it is the
literal reason `rls-bypass` is now `secure` while `/search_raw` still has no
filter of its own.

One leak left, and it is a different animal: the attacker is not reading a
document they are forbidden to see. They are reading one they are allowed to see,
that someone wrote instructions into.

Next: [Poisoned Documents](07-poisoned-documents.md).
