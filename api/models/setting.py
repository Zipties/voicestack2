import uuid
from sqlalchemy import Column, Integer, JSON, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db.base import Base

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, default=1)  # Singleton
    smtp_config = Column(JSON, nullable=True)
    model_config = Column(JSON, nullable=True)
    presets = Column(JSON, nullable=True, default=list)
    secrets_config = Column(JSON, nullable=True)
    api_token = Column(String, nullable=True)
    hf_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 