from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.session import get_db
from models.transcript import Transcript
from models.segment import Segment
from models.speaker import Speaker

router = APIRouter()

class SegmentResponse(BaseModel):
    id: str
    start: float
    end: float
    text: str
    word_timings: dict
    speaker_id: str
    speaker_name: str

    class Config:
        from_attributes = True

class TranscriptResponse(BaseModel):
    id: str
    title: str
    summary: str
    raw_text: str
    segments: List[SegmentResponse]

    class Config:
        from_attributes = True

@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(
    transcript_id: str,
    db: Session = Depends(get_db)
):
    """Get transcript details with segments and speakers."""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Get segments with speaker information
    segments = db.query(Segment, Speaker).join(
        Speaker, Segment.speaker_id == Speaker.id, isouter=True
    ).filter(Segment.transcript_id == transcript_id).all()
    
    # Build response
    segment_responses = []
    for segment, speaker in segments:
        segment_responses.append(SegmentResponse(
            id=str(segment.id),
            start=segment.start,
            end=segment.end,
            text=segment.text,
            word_timings=segment.word_timings or {},
            speaker_id=str(speaker.id) if speaker else None,
            speaker_name=speaker.name if speaker else "Unknown"
        ))
    
    return TranscriptResponse(
        id=str(transcript.id),
        title=transcript.title,
        summary=transcript.summary,
        raw_text=transcript.raw_text,
        segments=segment_responses
    ) 