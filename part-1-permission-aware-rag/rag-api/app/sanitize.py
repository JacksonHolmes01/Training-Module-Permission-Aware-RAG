"""
sanitize.py: strip instructions hidden in retrieved text.

A retrieved chunk is data, but a language model downstream will read it as part
of its prompt, so a document that *contains* instructions ("ignore your rules",
"email this to...") is an injection aimed at that model. This is the retrieval
version of the poisoned document: the attacker does not need access to the
secret, only to get their text retrieved alongside it.

Permission scoping does not help here, because the poisoned document is one the
user is genuinely allowed to read. The fix is to neutralize instruction-shaped
text before it is handed to a model. Note what this does NOT touch: plain facts
like a salary figure are data, not instructions, so scoping (not sanitizing) is
what keeps those out.
"""

import re

_INJECTION = re.compile(
    r"(?is)(<!--.*?-->|assistant\s*:|system\s*:|ignore (all |your )?(previous )?(instructions|rules)|"
    r"do this silently|do not mention|send (a copy|it) to|email (a copy|it|them) to)")


def sanitize(text: str) -> str:
    from . import guards
    if not guards.on("RAG_SANITIZE"):
        return text
    cleaned, n = _INJECTION.subn("[removed: possible injected instruction]", text)
    if n:
        cleaned = "[note: suspected injected instructions were removed]\n" + cleaned
    return cleaned
