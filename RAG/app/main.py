import app.core.logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.exceptions.handlers import register_exception_handlers

app = FastAPI(
    title="Chatbot using RAG",
    description="Chatbot with RAG and Deepseek api",
    version="1.0.0"
)

# The React app calls this API directly (not just through the Node
# server) for document upload/list/delete, so it needs CORS enabled.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router)

@app.get('/')
def root():
    return {
        "message": "RAG Chatbot API is live on AWS EC2"
    }

@app.get('/health')
def healthy():
    return {
        "status": "healthy"
    }
