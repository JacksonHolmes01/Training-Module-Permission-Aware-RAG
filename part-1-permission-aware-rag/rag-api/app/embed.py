"""
embed.py: a small, deterministic text embedding.

Real RAG systems call an embedding model. For a security lab that is noise:
the model adds a GPU dependency and makes retrieval non-reproducible, and none
of the lessons here are about embedding quality. So this file turns text into a
vector with a hashing trick instead: every word is hashed into one of DIM
buckets, the buckets are counted, and the vector is length-normalized. The same
text always produces the same vector, so every attack result is reproducible.

What matters for security is identical whether the vector comes from here or
from a billion-parameter model: similarity retrieval returns whatever chunk is
closest, and *permission has to be enforced somewhere else*. That "somewhere
else" is the whole subject of this lab.
"""

import hashlib
import math
import re

DIM = 256
_TOKEN = re.compile(r"[a-z0-9$]+")


def embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for tok in _TOKEN.findall(text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def to_literal(vec: list[float]) -> str:
    """Format a vector the way pgvector wants it: [0.1,0.2,...]."""
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
