# 1. The Permission Problem in RAG

Retrieval-augmented generation (RAG) is the most common way to put a company's
own documents behind a chatbot. You embed every document into a vector index,
and when someone asks a question you retrieve the closest chunks and feed them
to a model. It is a few hundred lines of code and it works on the first try,
which is exactly why it is dangerous.

Here is the problem in one sentence: **similarity does not know about
permission.** The vector index returns whatever text is closest to the question.
If Alice's salary and Carol's acquisition memo are in the same index, then the
right question pulls them back for whoever asks, and the model dutifully reads
them into its answer. Nobody broke in. The system did what it was built to do.

## The shape of a permission-aware RAG

A document store with permissions has three facts about every document:

- an **owner** (whose document it is),
- a **visibility** (private to the owner, or shared with the whole org),
- an **access list** (specific other people who may see it).

And every request has one fact that has to be trustworthy: **who is asking.**

Permission-aware retrieval is just the rule that connects them: a search returns
a chunk only if the asker is allowed to see that chunk. Easy to state. The lab
is about the five places it tends to go wrong.

## The service in this lab

A small RAG service over a document store (Postgres with the `pgvector`
extension). Three users, Alice and Bob in sales and Carol in legal, each with a
token. Eleven documents: some shared with the whole org, some private to one
person, one that Alice has shared with Bob, and one poisoned document planted by
an attacker. Three HTTP endpoints:

| Endpoint | What it does |
|---|---|
| `POST /search` | retrieve the closest chunks |
| `POST /ask` | retrieve, then compose a grounded answer from what came back |
| `POST /search_raw` | the same retrieval, with the permission filter left out |

There is no language model in the loop. The embedding is a small deterministic
function (see `rag-api/app/embed.py`), so every retrieval and every attack gives
the same result every run. That is a feature: you are here to study the
retrieval boundary, not to coax a model, and a leak you can reproduce is a leak
you can fix and verify.

## What you will do

1. Attack the service six ways and watch private documents come back to the
   wrong person (Lesson 3).
2. Turn on five defenses, one at a time, and measure each one:
   - **auth**, so the service knows who is asking (Lesson 4),
   - **a scoping filter**, so retrieval returns only the asker's documents, and
     a **trust boundary**, so "the asker" comes from the token and not from a
     field the caller controls (Lesson 5),
   - **row-level security**, so the database enforces the same rule even on the
     endpoint a developer forgot to filter (Lesson 6),
   - **sanitizing**, so instructions hidden inside a document cannot steer the
     model that reads it (Lesson 7).
3. Watch the scoreboard go from six leaks to zero (Lesson 8).

Next: [Setup](02-setup.md).
