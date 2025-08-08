import uuid
from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(UUID(as_uuid=True), ForeignKey("transcripts.id"), nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    text = Column(String, nullable=False)
    word_timings = Column(JSON, nullable=True)
    speaker_id = Column(UUID(as_uuid=True), ForeignKey("speakers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transcript = relationship("Transcript", back_populates="segments")
    speaker = relationship("Speaker", back_populates="segments") 