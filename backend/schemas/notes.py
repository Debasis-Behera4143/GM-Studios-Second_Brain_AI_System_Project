from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    source_type: str = Field(default="text", min_length=1, max_length=32)
    metadata_json: Optional[Dict[str, Any]] = None

class NoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    content: str
    summary: Optional[str]
    source_type: str
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IngestResponse(BaseModel):
    status: str
    note_id: UUID
    message: str
