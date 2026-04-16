from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    
class SourceNote(BaseModel):
    id: str
    content: str
    similarity: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceNote]
