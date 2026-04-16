from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import datetime
from core.database import Base

note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', UUID(as_uuid=True), ForeignKey('notes.id')),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    notes = relationship("Note", back_populates="owner")
    conversations = relationship("Conversation", back_populates="user")

class Note(Base):
    __tablename__ = "notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source_type = Column(String) # "text", "voice", "url", "file"
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    owner = relationship("User", back_populates="notes")
    tags = relationship("Tag", secondary=note_tags, back_populates="notes")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)
    
    notes = relationship("Note", secondary=note_tags, back_populates="tags")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="conversations")
