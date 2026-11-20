"""
db.py: the document store (Postgres + pgvector) and the retrieval query.

This is where permission-aware RAG is won or lost. There are two independent
places a document's visibility can be enforced, and a serious system uses both:

  1. The application query (RAG_ACL): the SELECT adds a WHERE clause so it only
     returns rows the caller is allowed to see. Fast, but only as correct as the
     developer who wrote each query. Forget it on one endpoint and that endpoint
     leaks.

  2. The database itself (RAG_RLS): Postgres Row-Level Security attaches a policy
     to the table, so a restricted role simply cannot see rows outside its scope,
     no matter what query runs. This is the backstop for the endpoint someone
     forgot. Defense in depth: the app filter AND the database policy.

The service connects two ways. As the Postgres superuser it bypasses RLS (this
is the "RLS off" world, and also how the corpus is seeded). As the restricted
role rag_app, RLS is in force, and the service sets `app.current_user` so the
policy knows whose rows to allow.
"""

import json
import os
import pathlib
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

from . import guards
from .embed import DIM, embed, to_literal

DB_HOST = os.getenv("DB_HOST", "pgvector")
DB_NAME = os.getenv("DB_NAME", "raglab")
ADMIN_USER = os.getenv("DB_ADMIN_USER", "postgres")
APP_USER = os.getenv("DB_APP_USER", "rag_app")
CORPUS = pathlib.Path(os.getenv("CORPUS_PATH", "/app/corpus/documents.json"))


def _secret(path_env: str, default_path: str) -> str:
    p = os.getenv(path_env, default_path)
    try:
        return pathlib.Path(p).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


ADMIN_PW = _secret("DB_ADMIN_PASSWORD_FILE", "/run/secrets/postgres_password")
APP_PW = _secret("DB_APP_PASSWORD_FILE", "/run/secrets/db_app_password")


def _connect(user: str, password: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=user, password=password)


def connect_admin() -> psycopg2.extensions.connection:
    """Superuser connection. Bypasses Row-Level Security."""
    return _connect(ADMIN_USER, ADMIN_PW)


def connect_scoped(username: Optional[str]) -> psycopg2.extensions.connection:
    """Restricted-role connection with RLS in force, scoped to one user."""
    conn = _connect(APP_USER, APP_PW)
    with conn.cursor() as cur:
        # A missing/NULL user sees only org-wide rows (the policy handles it).
        cur.execute("SELECT set_config('app.current_user', %s, false)", (username or "",))
    return conn


# ---------------------------------------------------------------- schema + seed

def init() -> None:
    conn = connect_admin()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS chunks (
            id serial PRIMARY KEY,
            doc text NOT NULL,
            owner text NOT NULL,
            visibility text NOT NULL,
            acl text[] NOT NULL DEFAULT '{{}}',
            content text NOT NULL,
            embedding vector({DIM})
        )""")

    # The restricted role the app uses when RLS is in force.
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_USER,))
    if not cur.fetchone():
        cur.execute(f"CREATE ROLE {APP_USER} LOGIN PASSWORD %s", (APP_PW,))
    cur.execute(f"GRANT USAGE ON SCHEMA public TO {APP_USER}")
    cur.execute(f"GRANT SELECT ON chunks TO {APP_USER}")

    # Row-Level Security: the policy is always present. It only bites the
    # restricted role; the superuser the app uses when RLS is "off" bypasses it.
    cur.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
    cur.execute("DROP POLICY IF EXISTS chunk_visibility ON chunks")
    cur.execute(f"""
        CREATE POLICY chunk_visibility ON chunks FOR SELECT TO {APP_USER}
        USING (
            visibility = 'org'
            OR owner = current_setting('app.current_user', true)
            OR current_setting('app.current_user', true) = ANY(acl)
        )""")

    cur.execute("SELECT count(*) FROM chunks")
    if cur.fetchone()[0] == 0 and CORPUS.exists():
        rows = json.loads(CORPUS.read_text())
        for r in rows:
            cur.execute(
                "INSERT INTO chunks (doc, owner, visibility, acl, content, embedding) "
                "VALUES (%s,%s,%s,%s,%s,%s::vector)",
                (r["doc"], r["owner"], r["visibility"], r.get("acl", []),
                 r["content"], to_literal(embed(r["content"]))))
    cur.close()
    conn.close()


def count() -> int:
    conn = connect_admin()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM chunks")
            return cur.fetchone()[0]
    finally:
        conn.close()


# ----------------------------------------------------------------- retrieval

def search(user: Optional[str], query: str, k: int = 5, apply_acl: bool = True) -> List[Dict[str, Any]]:
    """Return the k chunks closest to the query the caller may see.

    Two switches shape the result:
      - RAG_RLS picks the connection: the restricted role (policy enforced) or
        the superuser (policy bypassed).
      - apply_acl plus RAG_ACL decide whether the SELECT adds its own WHERE
        filter. The 'raw' endpoint passes apply_acl=False to model a query where
        a developer forgot the filter; only RLS can save it.
    """
    qvec = to_literal(embed(query))
    conn = connect_scoped(user) if guards.on("RAG_RLS") else connect_admin()
    try:
        sql = ["SELECT doc, owner, visibility, content, embedding <=> %s::vector AS dist FROM chunks"]
        params: list = [qvec]
        if apply_acl and guards.on("RAG_ACL"):
            sql.append("WHERE (visibility = 'org' OR owner = %s OR %s = ANY(acl))")
            params += [user or "", user or ""]
        sql.append("ORDER BY dist ASC LIMIT %s")
        params.append(k)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(" ".join(sql), params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
