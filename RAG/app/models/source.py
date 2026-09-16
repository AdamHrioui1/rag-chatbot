from pydantic import BaseModel

class Source(BaseModel):
    id: str
    title: str
    snippets: str
    distance: float
    confidence: int