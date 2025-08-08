from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    CANCELLED = "CANCELLED"

class TagSource(str, Enum):
    LLM = "LLM"
    USER = "USER"

class JobBase(BaseModel):
    status: JobStatus
    progress: int = 0
    params: Dict[str, Any] = {}
    email_to: Optional[str] = None
    log_path: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 