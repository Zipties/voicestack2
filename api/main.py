from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from core.config import settings
from db.session import engine
from db.init_pgvector import init_pgvector
from models.setting import Setting
from routers import health, settings, uploads, jobs, transcripts, speakers, stt, email

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting VoiceStack2 API...")
    
    # Ensure directories exist
    settings.__init__()
    
    # Initialize database and pgvector
    try:
        init_pgvector()
        print("✓ pgvector extension initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize pgvector: {e}")
    
    # Ensure singleton settings row exists
    with engine.connect() as conn:
        try:
            # Check if settings table exists and has data
            result = conn.execute(text("SELECT COUNT(*) FROM settings"))
            count = result.scalar()
            
            if count == 0:
                # Create default settings
                conn.execute(text("""
                    INSERT INTO settings (id, model_config, presets) 
                    VALUES (1, '{}', '[]')
                """))
                conn.commit()
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
app.include_router(settings.router, prefix="/settings", tags=["settings"])
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
