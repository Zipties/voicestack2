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
    original_label: str | None = None
    match_confidence: float | None = None
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
            original_label=speaker.original_label,
            match_confidence=speaker.match_confidence,
            embedding=embedding_vector
        ))
    
    return speaker_responses

@router.post("/merge")
def merge_speakers(
    request: SpeakerMergeRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Merge two speakers - reassigns all segments and embeddings from source to target."""
    from models.segment import Segment
    from models.embedding import Embedding
    
    # Get the speakers
    source_speaker = db.query(Speaker).filter(Speaker.id == request.source_speaker_id).first()
    target_speaker = db.query(Speaker).filter(Speaker.id == request.target_speaker_id).first()
    
    if not source_speaker or not target_speaker:
        raise HTTPException(status_code=404, detail="One or both speakers not found")
    
    if source_speaker.id == target_speaker.id:
        raise HTTPException(status_code=400, detail="Cannot merge speaker with itself")
    
    try:
        # Reassign all segments from source to target
        segments_updated = db.query(Segment).filter(
            Segment.speaker_id == source_speaker.id
        ).update({Segment.speaker_id: target_speaker.id})
        
        # Reassign all embeddings from source to target
        embeddings_updated = db.query(Embedding).filter(
            Embedding.speaker_id == source_speaker.id
        ).update({Embedding.speaker_id: target_speaker.id})
        
        # Update target speaker's match confidence to best of both
        if source_speaker.match_confidence and target_speaker.match_confidence:
            target_speaker.match_confidence = max(source_speaker.match_confidence, target_speaker.match_confidence)
        elif source_speaker.match_confidence:
            target_speaker.match_confidence = source_speaker.match_confidence
        
        # Keep the original_label of whichever speaker was created first
        if source_speaker.created_at < target_speaker.created_at and source_speaker.original_label:
            target_speaker.original_label = source_speaker.original_label
        
        # Delete the source speaker
        db.delete(source_speaker)
        db.commit()
        
        return {
            "message": "Speakers merged successfully",
            "source_speaker_id": request.source_speaker_id,
            "target_speaker_id": request.target_speaker_id,
            "target_speaker_name": target_speaker.name,
            "segments_reassigned": segments_updated,
            "embeddings_reassigned": embeddings_updated
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to merge speakers: {str(e)}") 

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
        original_label=speaker.original_label,
        match_confidence=speaker.match_confidence,
        embedding=None  # Don't include embedding in update response
    )} 