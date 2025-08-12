from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings as app_settings
from db.base import Base
from db.session import engine
from db.init_pgvector import init_pgvector
from models.setting import Setting
from routers import health, settings as settings_router, uploads, jobs, transcripts, speakers, stt, email

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting VoiceStack2 API...")
    
    # Directories are created at import time by app_settings
    
    # 1) Initialize pgvector extension
    try:
        init_pgvector()
        print("✓ pgvector extension initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize pgvector: {e}")
    
    # 2) Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created")
    except Exception as e:
        print(f"⚠ Warning: Could not create tables: {e}")
    
    # 3) Ensure singleton settings row exists
    try:
        with Session(engine) as s:
            if not s.get(Setting, 1):
                s.add(Setting(id=1, model_config={}, presets=[]))
                s.commit()
                print("✓ Default settings created")
            else:
                print("✓ Settings already exist")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize settings: {e}")
    
    print("✓ VoiceStack2 API startup complete")
    
    yield
    
    # Shutdown
    print("Shutting down VoiceStack2 API...")

# Create FastAPI app
app = FastAPI(
    title="VoiceStack2 API",
    description="Backend API for VoiceStack2 - Phase 1",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])
app.include_router(uploads.router, prefix="/upload", tags=["uploads"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(transcripts.router, prefix="/transcripts", tags=["transcripts"])
app.include_router(speakers.router, prefix="/speakers", tags=["speakers"])
app.include_router(stt.router, prefix="/stt", tags=["stt"])
app.include_router(email.router, prefix="/email", tags=["email"])

@app.get("/")
def root():
    return {
        "message": "VoiceStack2 API - Phase 1",
        "version": "1.0.0",
        "status": "running"
    }
