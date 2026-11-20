#!/usr/bin/env python3
"""
run_attacks.py: attack the RAG service and report what really leaked.

Each attack is a direct HTTP request (no model in the loop, so the result is
deterministic). An attack LEAKS when the service hands back something the caller
should not see: another user's private document, a secret figure inside it, or
an instruction smuggled in through a document. Run it at each defense level and
watch the leaks drop to zero.

  python3 attacks/run_attacks.py
"""

import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def tok(user):
    f = ROOT / "secrets" / f"token_{user}.txt"
    return f.read_text().strip() if f.exists() else ""


def post(path, body, token=""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("http://localhost:8000" + path,
                                 data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def answer(resp):
    return resp.get("answer", "").lower()


def snippets(resp):
    return " ".join(r.get("snippet", "") for r in resp.get("results", [])).lower()


# --- the six attacks ---------------------------------------------------------

def a_no_auth():
    # Ask with no token at all.
    r = post("/search", {"query": "office hours support help desk"})
    hit = bool(r.get("results"))
    return hit, "anonymous caller retrieved documents" if hit else "rejected without a token"


def a_cross_user():
    # Bob asks a question whose answer lives in Alice's private comp plan.
    r = post("/ask", {"query": "alice base salary and q4 bonus pool"}, tok("bob"))
    leaked = "184,000" in answer(r)
    return leaked, "Bob's answer contained Alice's salary" if leaked else "scoped out of Alice's document"


def a_secret_in_search():
    # Same leak, one step earlier: the retrieval endpoint itself.
    r = post("/search", {"query": "alice base salary and q4 bonus pool"}, tok("bob"))
    leaked = "184,000" in snippets(r)
    return leaked, "search returned Alice's private comp figures" if leaked else "scoped out of Alice's document"


def a_spoofed_identity():
    # Bob's token, but the request body claims to be Carol.
    r = post("/ask", {"query": "project atlas acquisition riverside robotics", "user_id": "carol"}, tok("bob"))
    leaked = "riverside" in answer(r)
    return leaked, "body user_id let Bob read as Carol" if leaked else "identity taken from the token, not the body"


def a_rls_bypass():
    # The endpoint that forgot its ACL filter. Only the database can scope it.
    r = post("/search_raw", {"query": "project atlas acquisition riverside robotics"}, tok("bob"))
    leaked = "riverside" in snippets(r)
    return leaked, "the unfiltered endpoint returned Carol's memo" if leaked else "database policy scoped the raw query"


def a_poisoned_note():
    # A document Bob may see carries instructions aimed at the model.
    r = post("/ask", {"query": "partner update quarterly sync webinar"}, tok("bob"))
    leaked = "evil.example" in answer(r)
    return leaked, "a poisoned document's instructions reached the answer" if leaked else "injected instructions stripped"


ATTACKS = [
    ("no-auth", "Retrieve with no token at all", a_no_auth),
    ("cross-user", "Read another user's private document via /ask", a_cross_user),
    ("secret-in-search", "Read another user's figures via /search", a_secret_in_search),
    ("spoofed-identity", "Claim to be another user in the request body", a_spoofed_identity),
    ("rls-bypass", "Use the endpoint that forgot its ACL filter", a_rls_bypass),
    ("poisoned-note", "Smuggle instructions through a document", a_poisoned_note),
]


def main():
    print(f"Attacking the RAG service. {len(ATTACKS)} attacks; an attack LEAKS only if the")
    print("service actually returned something this caller should not see.\n")
    print(f"{'ATTACK':<18} {'RESULT':<10} WHAT HAPPENED")
    print("-" * 80)
    leaks = 0
    for name, _desc, fn in ATTACKS:
        try:
            leaked, note = fn()
        except Exception as e:
            leaked, note = False, f"error: {type(e).__name__}"
        leaks += 1 if leaked else 0
        print(f"{name:<18} {'LEAK' if leaked else 'secure':<10} {note}")
    print("-" * 80)
    print(f"{leaks} of {len(ATTACKS)} attacks leaked.")


if __name__ == "__main__":
    main()
