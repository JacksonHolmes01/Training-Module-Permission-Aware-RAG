"""
main.py: the permission-aware RAG service.

A RAG chatbot answers a question by retrieving the most relevant documents and
feeding them to a model. The security question this lab is about is simple to
say and easy to get wrong: *does retrieval return only the documents this user
is allowed to see?* A naive service retrieves by similarity alone, so the person
who asks the right question gets back someone else's private document.

Three HTTP endpoints, each a step in that story:

  POST /search      the retrieval step on its own: return the closest chunks
  POST /ask         retrieve, then compose a grounded answer from what came back
  POST /search_raw  the same retrieval with the ACL filter left out, the way a
                    second endpoint gets written in a hurry. Only RLS saves it.

Identity comes from the bearer token. The /ask body may also carry a "user_id";
that is the trap. Until RAG_IDENTITY is on, the service trusts it, and a caller
can read as anyone. Every request is written to a one-line audit log.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request

from . import db, guards, identity
from .sanitize import sanitize

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
audit = logging.getLogger("audit")

app = FastAPI(title="Permission-Aware RAG")


@app.on_event("startup")
def _startup() -> None:
    db.init()


def _log(user: str, endpoint: str, decision: str, detail: str = "") -> None:
    audit.warning(json.dumps({
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user": user, "endpoint": endpoint, "decision": decision,
        **({"detail": detail[:160]} if detail else {})}))


def _bearer(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    return auth[7:].strip() if auth.lower().startswith("bearer ") else ""


def _caller(request: Request) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Identify the caller. Return (username, error) where error is set when
    auth is required and the token is missing or invalid."""
    user = identity.identify(_bearer(request))
    if guards.on("RAG_AUTH") and user is None:
        return None, {"error": "unauthorized: a valid user token is required"}
    return user, None


def _effective_user(token_user: Optional[str], body: Dict[str, Any]) -> Optional[str]:
    """Whose documents this request is scoped to.

    With RAG_IDENTITY on, it is always the token's user. Without it, the service
    honors a 'user_id' from the request body if one is present, which is exactly
    how a caller impersonates someone else.
    """
    if guards.on("RAG_IDENTITY"):
        return token_user
    return body.get("user_id") or token_user


@app.get("/health")
def health():
    try:
        n = db.count()
        return {"ok": True, "chunks": n, "guards": guards.status()}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "guards": guards.status()}


@app.post("/search")
async def search(request: Request):
    user, err = _caller(request)
    if err:
        _log("unknown", "/search", "denied", "missing or invalid token")
        return err
    body = await request.json()
    scope = _effective_user(user, body)
    hits = db.search(scope, str(body.get("query", "")), int(body.get("k", 5)))
    _log(user or "anonymous", "/search", "ok", f"scope={scope} hits={len(hits)}")
    return {"user": user, "scope": scope,
            "results": [{"doc": h["doc"], "owner": h["owner"], "visibility": h["visibility"],
                         "snippet": sanitize(h["content"])[:240]} for h in hits]}


@app.post("/search_raw")
async def search_raw(request: Request):
    # The careless endpoint: retrieval with no application ACL filter at all.
    # If RLS is off, this returns everyone's documents.
    user, err = _caller(request)
    if err:
        _log("unknown", "/search_raw", "denied", "missing or invalid token")
        return err
    body = await request.json()
    scope = _effective_user(user, body)
    hits = db.search(scope, str(body.get("query", "")), int(body.get("k", 5)), apply_acl=False)
    _log(user or "anonymous", "/search_raw", "ok", f"scope={scope} hits={len(hits)}")
    return {"user": user, "scope": scope,
            "results": [{"doc": h["doc"], "owner": h["owner"], "visibility": h["visibility"],
                         "snippet": sanitize(h["content"])[:240]} for h in hits]}


@app.post("/ask")
async def ask(request: Request):
    user, err = _caller(request)
    if err:
        _log("unknown", "/ask", "denied", "missing or invalid token")
        return err
    body = await request.json()
    scope = _effective_user(user, body)
    query = str(body.get("query", ""))
    hits = db.search(scope, query, int(body.get("k", 5)))

    # Compose a grounded answer from the retrieved chunks. There is no model
    # here on purpose: this is exactly the context a model would be handed, so
    # whatever reaches this text is what a model would read and act on. Scoping
    # decides which chunks are here; sanitizing decides what the chunks may say.
    # Pass the full chunk text, the way a real RAG hands retrieved context to a
    # model. This is the boundary the poisoned document is aiming at.
    lines = [f"- [{h['doc']} | owner {h['owner']}] {sanitize(h['content'])}" for h in hits]
    answer = ("Based on your authorized documents:\n" + "\n".join(lines)) if lines \
        else "No documents you are allowed to see match that question."
    _log(user or "anonymous", "/ask", "ok", f"scope={scope} sources={len(hits)}")
    return {"user": user, "scope": scope, "answer": answer,
            "sources": [{"doc": h["doc"], "owner": h["owner"]} for h in hits]}
