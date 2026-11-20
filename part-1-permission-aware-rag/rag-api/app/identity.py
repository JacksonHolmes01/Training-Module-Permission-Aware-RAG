"""
identity.py: who is calling, decided from a bearer token.

Each user has a secret token (a file in secrets/). The service maps a token to
a username. A real deployment would get this username from an identity provider
or a signed session; the security decision is the same either way.

The thing to notice through the whole lab: the username the service *trusts*
must come from the token, never from a field the caller can set. When a request
body carries its own "user_id", that is a claim, not a fact.
"""

import os
import pathlib
from typing import Optional


def _token(user: str) -> str:
    for path in (f"/run/secrets/token_{user}", f"/app/secrets/token_{user}.txt"):
        try:
            return pathlib.Path(path).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            continue
    return ""


def _users() -> list[str]:
    import json
    seed = pathlib.Path(os.getenv("USERS_PATH", "/app/corpus/users.json"))
    return [u["username"] for u in json.loads(seed.read_text())] if seed.exists() else []


# username -> token, built once at import.
TOKENS = {u: _token(u) for u in _users()}


def identify(token: str) -> Optional[str]:
    """Return the username for a token, or None if it matches no user."""
    if not token:
        return None
    for user, tok in TOKENS.items():
        if tok and token == tok:
            return user
    return None
