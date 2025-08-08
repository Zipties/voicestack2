from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from db.session import get_db
from models.setting import Setting
from schemas.settings import SettingsRequest, SettingsResponse
from core.security import require_bearer

router = APIRouter()

def get_or_create_settings(db: Session) -> Setting:
    """Get or create the singleton settings row."""
    settings = db.query(Setting).filter(Setting.id == 1).first()
    if not settings:
        settings = Setting(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get application settings with secrets masked."""
    settings = get_or_create_settings(db)
    
    response = SettingsResponse(
        smtp=settings.smtp_config,
        models=settings.model_config or {},
        presets=settings.presets or [],
        api_token=settings.api_token,
        hf_token=settings.hf_token
    )
    
    return response.mask_secrets()

@router.put("/settings")
def update_settings(
    request: SettingsRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Update application settings."""
    settings = get_or_create_settings(db)
    
    if request.smtp is not None:
        settings.smtp_config = request.smtp.model_dump()
    
    if request.models is not None:
        settings.model_config = request.models.model_dump()
    
    if request.presets is not None:
        settings.presets = [preset.model_dump() for preset in request.presets]
    
    if request.api_token is not None:
        settings.api_token = request.api_token
    
    if request.hf_token is not None:
        settings.hf_token = request.hf_token
    
    db.commit()
    db.refresh(settings)
    
    return {"message": "Settings updated successfully"} 