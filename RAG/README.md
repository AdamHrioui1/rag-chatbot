# RAG Service (FastAPI)

This is the document-based RAG (Retrieval-Augmented Generation) engine for
the chatbot. It owns document upload/storage/indexing and answers chat
questions using only the authenticated user's own uploaded documents.

It runs as a separate service from the Node/Express server. The Node
server still owns authentication and chat history; this service owns
documents and the actual "answer this question" logic. Both trust the
same JWT (`ACCESS_TOKEN_SECRET`), so a user only ever needs to log in once.

```
React client ──► Node/Express (auth, chat history) ──► FastAPI (this service) ──► DeepSeek LLM
                                                              │
      React client ─────────────────────────────────────────┘  (document upload/list/delete
                                                                  called directly, same JWT)
                                                              │
                                                    MongoDB (document metadata)
                                                    ChromaDB (vectors, local disk)
                                                    ./storage (raw files, local disk)
```

## Pipeline

**Upload:**
```
file(s) or .zip
  -> validate (extension, size, not empty)
  -> save raw file to disk (storage.py)
  -> extract text (extractors.py: pypdf / python-docx / plain text)
  -> clean + chunk text (chunker.py)
  -> embed each chunk (sentence-transformers/all-MiniLM-L6-v2)
  -> store chunks + embeddings in ChromaDB, tagged with user_id + document_id
  -> record metadata (filename, size, status) in MongoDB
```

**Ask a question:**
```
question + JWT
  -> verify JWT, extract user_id
  -> if user has zero ready documents -> return "you haven't uploaded anything yet" (no LLM call)
  -> embed the question, search ChromaDB filtered to where user_id == this user
  -> drop chunks past the similarity threshold
  -> if nothing relevant -> return "couldn't find that in your documents" (no LLM call)
  -> build a prompt from the relevant chunks, call the LLM
  -> return the answer + which chunks/documents it came from
```

The "no LLM call" branches above are deliberate: an LLM asked to answer
without real context is free to fall back on outside knowledge and sound
confident about it. This app would rather say "not found" than guess.

## Multi-user isolation

Every chunk stored in ChromaDB carries `user_id` and `document_id` in its
metadata. Every search and every delete against ChromaDB passes
`where={"user_id": ...}` (or a specific `document_id`) - there is no code
path that queries the vector store without this filter. Document
metadata in MongoDB is looked up as *"this id AND this user_id together"*
(`get_by_id_for_user`), not "this id, then check ownership after" - so a
document can't be read or deleted by guessing/changing an id unless it
actually belongs to the caller.

See `app/services/vector_store.py`, `app/services/retriever.py`,
`app/services/document_service.py`, and `app/db/mongo.py`.

## Setup

```bash
cd RAG
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy the environment variables below into `RAG/.env` (see the existing
`.env` in this folder for real values used in local dev - never commit
that file).

| Variable | Meaning |
|---|---|
| `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` | LLM credentials (OpenAI-compatible API) |
| `ACCESS_TOKEN_SECRET` | Must match the Node server's JWT secret |
| `MONGO_URI`, `MONGO_DB_NAME` | Same MongoDB the Node server uses (separate `documents` collection) |
| `STORAGE_PATH` | Local folder for raw uploaded files (default `storage`) |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Chunking - see comments in `.env` for the reasoning |
| `TOP_K` | How many chunks to retrieve per question |
| `SIMILARITY_THRESHOLD` | Cosine distance cutoff for a chunk to count as relevant - calibrated empirically, see `.env` comments |
| `MAX_FILE_SIZE_MB`, `ALLOWED_EXTENSIONS` | Upload limits |
| `CORS_ORIGINS` | Frontend origin(s) allowed to call this API directly |

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
python -m pytest -q
```

(`python -m pytest`, not the bare `pytest` command - see `pytest.ini`. The
`-m` form is what reliably picks up the same Python environment you just
activated, regardless of what else might be on your PATH.)

44 tests covering: JWT enforcement on every route, request validation,
chunking edge cases, extraction of real DOCX/corrupted PDF/unsupported
types, ZIP path-traversal safety, per-file upload error reporting,
duplicate-file detection, ownership checks on delete, similarity
threshold filtering, and the "never hallucinate without context" rule.

Note: these are unit/route tests with mocked services (fast, no network
needed) except where a real in-memory DOCX/ZIP is built to test the
extractors themselves. There's no automated end-to-end test against the
live MongoDB/ChromaDB, since that would make CI depend on live network
credentials - that path was instead verified manually (see the "known
limitations" note below).

## Known limitations (current state)

- Uploaded files are read fully into memory before the size limit is
  checked - fine for a small student-project scale (`MAX_FILE_SIZE_MB`
  default 15MB), not meant for very large files.
- No content-hash dedup across renamed copies of the same file across
  *different* users - dedup only applies per-user.
- `MONGO_DB_NAME` defaults to `test`, matching Mongoose's default when no
  database name is given in the connection string used by the Node
  server. Fine for a shared dev database; worth naming explicitly before
  any real deployment.
- File storage is local disk (`RAG/storage/`), not yet object storage.
  This is intentional for now - see the project's AWS phase for the S3
  migration plan.
