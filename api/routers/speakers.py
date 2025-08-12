from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.session import get_db
from models.speaker import Speaker
from core.security import require_bearer

router = APIRouter()

class SpeakerResponse(BaseModel):
    id: str
    name: str
    is_trusted: bool

    class Config:
        from_attributes = True

class SpeakerMergeRequest(BaseModel):
    source_speaker_id: str
    target_speaker_id: str

@router.get("", response_model=List[SpeakerResponse])
def list_speakers(db: Session = Depends(get_db)):
    """List all speakers."""
    speakers = db.query(Speaker).order_by(Speaker.name).all()
    return speakers

@router.post("/merge")
def merge_speakers(
    request: SpeakerMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Merge two speakers (stub implementation)."""
    # Get the speakers
    source_speaker = db.query(Speaker).filter(Speaker.id == request.source_speaker_id).first()
    target_speaker = db.query(Speaker).filter(Speaker.id == request.target_speaker_id).first()
    
    if not source_speaker or not target_speaker:
        raise HTTPException(status_code=404, detail="One or both speakers not found")
    
    if source_speaker.id == target_speaker.id:
        raise HTTPException(status_code=400, detail="Cannot merge speaker with itself")
    
    # This is a stub - in Phase 2 we'll implement the actual merging logic
    # which will reassign segments, merge embeddings, and delete the source speaker
    
    return {"message": "Speaker merge initiated (stub implementation)"} 