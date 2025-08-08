import uuid
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from db.base import Base

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speaker_id = Column(UUID(as_uuid=True), ForeignKey("speakers.id"), nullable=False)
    vector = Column(Vector(768), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    speaker = relationship("Speaker", back_populates="embeddings") 