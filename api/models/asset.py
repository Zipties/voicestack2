import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    input_path = Column(String, nullable=False)
    archival_path = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    samplerate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    media_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="assets")
    transcripts = relationship("Transcript", back_populates="asset") 