import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.session import get_db
from models.job import Job
from models.asset import Asset
from models.transcript import Transcript
from schemas.common import JobResponse, JobStatus
from core.security import require_bearer

router = APIRouter()

class ReprocessRequest(BaseModel):
    params: dict = {}

class JobDetailResponse(BaseModel):
    id: str
    status: str
    progress: int
    params: dict
    email_to: Optional[str]
    log_path: Optional[str]
    created_at: str
    updated_at: str
    asset: Optional[dict] = None
    transcript: Optional[dict] = None
    artifacts: Optional[dict] = None

    class Config:
        from_attributes = True


def _update_status_from_artifacts(job: Job) -> bool:
    """Return True if status was updated based on artifacts."""
    artifacts_dir = f"/data/artifacts/{job.id}"
    transcript_txt = os.path.join(artifacts_dir, "transcript.txt")
    if os.path.exists(transcript_txt) and job.status != JobStatus.SUCCEEDED.value:
        job.status = JobStatus.SUCCEEDED.value
        job.progress = 100
        return True
    return False

@router.get("", response_model=List[JobResponse])
def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering."""
    query = db.query(Job)
    
    if active_only:
        query = query.filter(Job.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]))
    
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()

    # Opportunistically update status from artifacts for stuck jobs
    changed = False
    for job in jobs:
        if job.status != JobStatus.SUCCEEDED.value:
            if _update_status_from_artifacts(job):
                changed = True
    if changed:
        db.commit()

    # Convert to response models with proper UUID serialization
    job_responses = []
    for job in jobs:
        job_responses.append(JobResponse(
            id=str(job.id),
            status=job.status,
            progress=job.progress,
            params=job.params,
            email_to=job.email_to,
            log_path=job.log_path,
            created_at=job.created_at,
            updated_at=job.updated_at
        ))
    
    return job_responses

@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Cancel a job (stub implementation)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in [JobStatus.FAILED.value, JobStatus.SUCCEEDED.value, JobStatus.CANCELLED.value]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    job.status = JobStatus.CANCELLED.value
    db.commit()
    
    return {"message": "Job cancelled successfully"}

@router.post("/{job_id}/reprocess")
def reprocess_job(
    job_id: str,
    request: ReprocessRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Create a new job with the same asset but different parameters (stub)."""
    # Get the original job and its asset
    original_job = db.query(Job).filter(Job.id == job_id).first()
    if not original_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # This is a stub - in Phase 2 we'll implement the actual reprocessing logic
    # For now, just return a success message
    return {"message": "Reprocessing job created (stub implementation)"}

@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job_detail(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed job information including asset and transcript."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Opportunistically update status from artifacts
    changed = _update_status_from_artifacts(job)
    
    # Get asset
    asset = db.query(Asset).filter(Asset.job_id == job_id).first()
    asset_data = None
    if asset:
        asset_data = {
            "id": str(asset.id),
            "input_path": asset.input_path,
            "archival_path": asset.archival_path,
            "duration": asset.duration,
            "samplerate": asset.samplerate,
            "channels": asset.channels,
            "media_type": asset.media_type
        }
    
    # Get transcript from DB
    transcript_data = None
    db_transcript = None
    if asset:
        db_transcript = db.query(Transcript).filter(Transcript.asset_id == asset.id).first()
        if db_transcript:
            # Get segments with speaker information
            from models.segment import Segment
            from models.speaker import Speaker
            
            segments = db.query(Segment, Speaker).join(
                Speaker, Segment.speaker_id == Speaker.id, isouter=True
            ).filter(Segment.transcript_id == db_transcript.id).order_by(Segment.start).all()
            
            segments_data = []
            for segment, speaker in segments:
                segments_data.append({
                    "id": str(segment.id),
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "original_speaker_label": segment.original_speaker_label,
                    "speaker": {
                        "id": str(speaker.id) if speaker else None,
                        "name": speaker.name if speaker else "Unknown",
                        "original_label": speaker.original_label if speaker else None,
                        "match_confidence": speaker.match_confidence if speaker else None
                    }
                })
            
            transcript_data = {
                "id": str(db_transcript.id),
                "title": db_transcript.title,
                "summary": db_transcript.summary,
                "raw_text": db_transcript.raw_text,
                "segments": segments_data
            }
    
    # Fallback to artifacts transcript if DB transcript missing
    artifacts_dir = f"/data/artifacts/{job_id}"
    transcript_txt_path = os.path.join(artifacts_dir, "transcript.txt")
    if transcript_data is None and os.path.exists(transcript_txt_path):
        try:
            with open(transcript_txt_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            
            # Create a sensible title from first few words, not the entire first line
            title = "Transcript"
            if raw_text:
                first_words = raw_text.split()[:8]  # First 8 words
                if len(first_words) >= 3:  # Only use as title if we have at least 3 words
                    title = " ".join(first_words) + ("..." if len(raw_text.split()) > 8 else "")
            
            transcript_data = {
                "id": str(db_transcript.id) if db_transcript else job_id,
                "title": title,
                "summary": "",
                "raw_text": raw_text,
            }
            # Also mark job as succeeded if not already
            if job.status != JobStatus.SUCCEEDED.value:
                job.status = JobStatus.SUCCEEDED.value
                job.progress = 100
                changed = True
        except Exception:
            pass
    
    # Artifacts info
    artifacts_data = None
    if os.path.exists(artifacts_dir):
        artifacts_data = {
            "transcript_json": f"{artifacts_dir}/transcript.json",
            "transcript_txt": f"{artifacts_dir}/transcript.txt",
            "transcript_srt": f"{artifacts_dir}/transcript.srt",
            "transcript_vtt": f"{artifacts_dir}/transcript.vtt",
            "aligned_words": f"{artifacts_dir}/aligned_words.json",
            "pipeline_log": f"{artifacts_dir}/_pipeline.log"
        }
    
    if changed:
        db.commit()
    
    return JobDetailResponse(
        id=str(job.id),
        status=job.status,
        progress=job.progress,
        params=job.params,
        email_to=job.email_to,
        log_path=job.log_path,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        asset=asset_data,
        transcript=transcript_data,
        artifacts=artifacts_data
    ) 