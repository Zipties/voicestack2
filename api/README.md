# VoiceStack2 API - Phase 1

This is the backend API for VoiceStack2 Phase 1 implementation.

## Features

- **FastAPI** with SQLAlchemy and Pydantic v2
- **PostgreSQL** with pgvector extension for embeddings
- **Redis + RQ** for job queuing
- **Bearer token** authentication
- **File upload** with job enqueuing
- **Settings management** (SMTP, models, presets)
- **Job management** (list, cancel, reprocess)
- **Transcript retrieval** with segments and speakers
- **Speaker management** (list, merge)
- **Email integration** (stub)

## API Endpoints

### Health
- `GET /health` - Health check

### Settings
- `GET /settings` - Get application settings (secrets masked)
- `PUT /settings` - Update application settings (Bearer required)

### Uploads
- `POST /upload` - Upload media file and enqueue job (Bearer required)

### Jobs
- `GET /jobs` - List jobs with filtering
- `POST /jobs/{id}/cancel` - Cancel a job (Bearer required)
- `POST /jobs/{id}/reprocess` - Reprocess job with new params (Bearer required)

### Transcripts
- `GET /transcripts/{id}` - Get transcript with segments and speakers

### Speakers
- `GET /speakers` - List all speakers
- `POST /speakers/merge` - Merge two speakers (Bearer required)

### STT
- `POST /stt` - Speech-to-text endpoint (stub, returns 501)

### Email
- `POST /email/transcript` - Send transcript via email (Bearer required)

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `INPUTS_DIR` - Directory for uploaded files
- `ARCHIVAL_DIR` - Directory for archival files
- `ARTIFACTS_DIR` - Directory for job artifacts
- `MODELS_DIR` - Directory for ML models
- `API_TOKEN` - Bearer token for authentication
- `HF_TOKEN` - HuggingFace token for models

## Database Schema

### Core Tables
- `jobs` - Job tracking with status and progress
- `assets` - Media files with metadata
- `transcripts` - Generated transcripts
- `segments` - Text segments with timing
- `speakers` - Speaker identification
- `embeddings` - Speaker embeddings (pgvector)
- `tags` - Transcript tags
- `settings` - Application configuration

## Running

1. Install dependencies: `pip install -r requirements.txt`
2. Initialize database: `python init_db.py`
3. Start server: `uvicorn main:app --reload`

## Phase 1 Limitations

- No actual ML pipeline implementation
- STT endpoint returns 501 Not Implemented
- Email sending is stub only
- Speaker merging is stub only
- Job reprocessing is stub only

## Next Steps (Phase 2)

- Implement actual ML pipeline in worker
- Add real STT processing
- Implement email sending
- Add speaker merging logic
- Add job reprocessing logic 