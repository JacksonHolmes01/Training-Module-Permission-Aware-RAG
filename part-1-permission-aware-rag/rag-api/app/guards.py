"""
guards.py: the RAG service's security switches.

Each defense is an environment variable, flipped by bin/defend.sh. They all
start OFF, so the service begins as the kind of quick, trusting RAG chatbot
people ship in an afternoon: anyone can ask, retrieval returns whatever is
closest, and the service believes whatever the caller says about who they are.
You turn the protections on one at a time and watch the leaks close.

  RAG_AUTH       every request must carry a valid user token
  RAG_ACL        retrieval is filtered to documents the user is allowed to see
  RAG_IDENTITY   the user is taken from the token, never from the request body
  RAG_RLS        the database enforces the same rule, even on a buggy query
  RAG_SANITIZE   instructions hidden in retrieved text are stripped before use

Audit logging is always on: a retrieval you cannot see into is one you cannot
secure.
"""

import os

ORDERED = ("RAG_AUTH", "RAG_ACL", "RAG_IDENTITY", "RAG_RLS", "RAG_SANITIZE")


def on(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() == "true"


def status() -> dict:
    return {g: on(g) for g in ORDERED}
