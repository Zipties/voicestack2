import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base

class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    json_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="transcripts")
    segments = relationship("Segment", back_populates="transcript")
    tags = relationship("Tag", back_populates="transcript") 