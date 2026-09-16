# RAG Chatbot

A multi-user, document-based RAG (Retrieval-Augmented Generation) chatbot.
Users upload their own documents (PDF/DOCX/TXT/ZIP); the chatbot answers
questions using only that user's uploaded documents, with source citations,
and never invents an answer when nothing relevant is found.

## Architecture

```
React client ──► Node/Express (auth, chat history) ──► FastAPI RAG service ──► DeepSeek LLM
                                                              │
      React client ─────────────────────────────────────────┘  (document upload/list/delete,
                                                                  same JWT, called directly)
                                                              │
                                                    MongoDB (users, chats, document metadata)
                                                    ChromaDB (vector store, local disk)
```

- `client/` - React app (auth, chat UI, document management)
- `server/` - Express + MongoDB (JWT auth, chat history, proxies chat questions to the RAG service)
- `RAG/` - FastAPI service (document ingestion pipeline + retrieval-augmented answers)

See `RAG/README.md` for the RAG pipeline in detail (chunking, embeddings,
similarity threshold, multi-user isolation).

## Running locally

Each service needs its own `.env` file - copy the matching `.env.example`
in each folder and fill in real values (never commit the real `.env` files).

**With Docker (recommended):**
```bash
docker compose up --build
```
Then open the client separately (see `client/README.md`) - the client runs
outside Docker for now, calling the two containerized services.

**Without Docker**, in three separate terminals:
```bash
# 1. RAG service
cd RAG && .venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000

# 2. Node server
cd server && npm run dev

# 3. React client
cd client && npm start
```

## Status

Core application (RAG pipeline, multi-user isolation, document management,
tests, Docker) is complete. Full documentation (setup details, AWS
architecture, CI/CD, deployment guide) is in progress.
