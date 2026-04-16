from pydantic import BaseModel
from typing import List


class ResurfaceSuggestion(BaseModel):
    id: str
    content: str


class ResurfaceResponse(BaseModel):
    suggestions: List[ResurfaceSuggestion]
