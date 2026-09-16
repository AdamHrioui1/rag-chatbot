from pydantic import BaseModel
from app.models.source import Source

class QuestionResponse(BaseModel):
    answer: str
    sources: list[Source]