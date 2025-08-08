import uuid
from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base
from schemas.common import JobStatus

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default=JobStatus.QUEUED)
    progress = Column(Integer, nullable=False, default=0)
    params = Column(JSON, nullable=False, default=dict)
    email_to = Column(String, nullable=True)
    log_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assets = relationship("Asset", back_populates="job", cascade="all, delete-orphan") 