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
    embedding: list[float] | None = None  # Add embedding field for debugging

    class Config:
        from_attributes = True

class SpeakerMergeRequest(BaseModel):
    source_speaker_id: str
    target_speaker_id: str

class SpeakerUpdateRequest(BaseModel):
    name: str

@router.get("", response_model=List[SpeakerResponse])
def list_speakers(db: Session = Depends(get_db)):
    """List all speakers."""
    from models.embedding import Embedding
    
    speakers = db.query(Speaker).order_by(Speaker.name).all()
    
    # Create response with embeddings
    speaker_responses = []
    for speaker in speakers:
        # Get the latest embedding for this speaker
        latest_embedding = db.query(Embedding).filter(
            Embedding.speaker_id == speaker.id
        ).order_by(Embedding.created_at.desc()).first()
        
        embedding_vector = None
        if latest_embedding:
            embedding_vector = latest_embedding.vector.tolist() if hasattr(latest_embedding.vector, 'tolist') else list(latest_embedding.vector)
        
        speaker_responses.append(SpeakerResponse(
            id=str(speaker.id),
            name=speaker.name,
            is_trusted=speaker.is_trusted,
            embedding=embedding_vector
        ))
    
    return speaker_responses

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

@router.put("/{speaker_id}")
def update_speaker(
    speaker_id: str,
    request: SpeakerUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update speaker name."""
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    speaker.name = request.name
    db.commit()
    db.refresh(speaker)
    
    return {"message": "Speaker updated successfully", "speaker": SpeakerResponse(
        id=str(speaker.id),
        name=speaker.name,
        is_trusted=speaker.is_trusted,
        embedding=None  # Don't include embedding in update response
    )} 