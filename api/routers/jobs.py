from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.session import get_db
from models.job import Job
from schemas.common import JobResponse
from core.security import require_bearer

router = APIRouter()

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering."""
    query = db.query(Job)
    
    if active_only:
        query = query.filter(Job.status.in_(["QUEUED", "RUNNING"]))
    
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
    return jobs

@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Cancel a job (stub implementation)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in ["FAILED", "SUCCEEDED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    job.status = "CANCELLED"
    db.commit()
    
    return {"message": "Job cancelled successfully"}

@router.post("/jobs/{job_id}/reprocess")
def reprocess_job(
    job_id: str,
    params: dict,
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