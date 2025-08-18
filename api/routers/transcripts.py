import json
import os
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
    original_speaker_label: str | None = None

    class Config:
        from_attributes = True
        use_enum_values = True

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
    
    # First try to get from artifacts (for fallback jobs)
    artifacts_dir = os.getenv("ARTIFACTS_DIR", "/data/artifacts")
    transcript_file = os.path.join(artifacts_dir, transcript_id, "transcript.json")
    
    if os.path.exists(transcript_file):
        try:
            with open(transcript_file, 'r') as f:
                data = json.load(f)
            
            return TranscriptResponse(
                id=transcript_id,
                title=f"Transcript {transcript_id}",
                summary="Processed in fallback mode",
                raw_text=data.get("transcript", ""),
                segments=[]  # Fallback mode doesn't have segments
            )
        except Exception as e:
            print(f"Error reading transcript file {transcript_file}: {e}")
    
    # Fallback to database lookup (for normal processing)
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
            speaker_name=speaker.name if speaker else "Unknown",
            original_speaker_label=segment.original_speaker_label
        ))
    
    return TranscriptResponse(
        id=str(transcript.id),
        title=transcript.title,
        summary=transcript.summary,
        raw_text=transcript.raw_text,
        segments=segment_responses
    )

class SegmentReassignRequest(BaseModel):
    speaker_id: str

@router.put("/segments/{segment_id}/speaker")
def reassign_segment_speaker(
    segment_id: str,
    request: SegmentReassignRequest,
    db: Session = Depends(get_db)
):
    """Reassign a segment to a different speaker."""
    
    # Get the segment
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Verify the new speaker exists
    speaker = db.query(Speaker).filter(Speaker.id == request.speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")
    
    # Update the segment
    segment.speaker_id = request.speaker_id
    db.commit()
    db.refresh(segment)
    
    return {
        "message": "Segment speaker reassigned successfully",
        "segment_id": str(segment.id),
        "new_speaker_id": str(segment.speaker_id),
        "new_speaker_name": speaker.name
    } 