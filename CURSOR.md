Cursor MASTER PROMPT (Persist this file in repo root)

Purpose: This document is the single source of truth for Cursor when working on VoiceStack2. It prevents scope drift, enforces tech choices, and lists the exact deliverables for each phase. Always follow these constraints.

0) Project Overview

A privacy-first audio pipeline that ingests media, normalizes/transcodes with FFmpeg, runs ASR + alignment + diarization, maintains searchable transcripts, and optionally summarizes/tags with an LLM. Stack:

API: FastAPI + SQLAlchemy + Pydantic v2

Queue: Redis + RQ (no Celery)

DB: Postgres 16 with pgvector

Worker: Python (Phase 2+)

Web: Next.js 14 (app dir) + TypeScript + Tailwind + shadcn/ui

Artifacts: on-disk volume under /data

Mandatory libraries (no substitutes):

Ingest/transcode: ffmpeg CLI only

ASR: faster-whisper (CTranslate2)

Alignment: WhisperX aligner

Diarization: pyannote.audio pipeline (HuggingFace token)

Speaker embeddings: SpeechBrain ECAPA (speechbrain/spkrec-ecapa-voxceleb)

Text embeddings: sentence-transformers (e.g. all-MiniLM-L6-v2 or bge-small-en)

LLM orchestration: HTTP providers via settings (OpenAI/OpenRouter/local endpoint)

Email: emails or aiosmtplib (TLS/STARTTLS)

Filesystem layout (volumes only; never write into image paths at runtime):

Inputs: /data/inputs

Artifacts: /data/artifacts/<job_id>/ (JSON with word timings & speakers, SRT, VTT, TXT, _pipeline.log)

Archival audio: /data/archival

Models cache: /data/models/{whisper,pyannote,speechbrain,llm}

Job states: QUEUED | RUNNING | FAILED | SUCCEEDED | CANCELLED

Security: Backend is only reachable by the frontend BFF (single Bearer token) for now.

Do-not-build list: No custom diarizers, no custom aligners, no “voice fingerprinting,” no GPU hacks, no model training. Don’t store secrets in YAML; bootstrap via .env then move to DB-backed settings.

1) Repo Conventions

Do not modify docker-compose.yml or Dockerfiles unless explicitly asked.

All config via ENV or DB settings table. No hardcoded model names or SMTP.

On API startup: enable pgvector → create tables → ensure settings row.

Use relative router paths with prefixes (avoid double /settings/settings).

Commit messages: feat(api): …, fix(worker): …, chore(web): ….

When done with a task: print a concise list of created/updated files with paths and STOP.

2) Current Status

Phase 1 – Backend skeleton (DONE)

FastAPI app + routers: uploads, jobs, transcripts, speakers, settings, stt, email

SQLAlchemy models: jobs, assets, transcripts, segments, speakers, embeddings (Vector(768)), tags, settings

/upload saves media → creates Job/Asset → enqueues RQ stub

/health, /settings (GET/PUT)

Bearer guard for write endpoints

Phase 2 – Worker pipeline + basic Web UI (INCREMENTAL)

Implement actual worker pipeline per constraints

Minimal admin UI for upload / jobs / transcripts

LLM service (optional but scaffolded) via provider adapters

3) Implementation Constraints (MANDATORY)

Pin minimum versions to avoid surprise API changes:

faster-whisper>=1.0.0
ctranslate2>=4.3.0
pyannote.audio>=3.1.0
speechbrain>=0.5.16
transformers>=4.41.0
sentence-transformers>=2.6.0
fastapi>=0.111.0
sqlalchemy>=2.0.30
psycopg[binary]>=3.1.19
redis>=5.0.6
rq>=1.16.2
pgvector>=0.2.5
python-dotenv>=1.0.1
python-multipart>=0.0.9
emails>=0.6  # or aiosmtplib

4) Phase 2 — Detailed Tasks

Goal: Implement the end-to-end worker pipeline and a minimal Web UI to drive it. Keep API contracts stable.

4.1 Worker: Pipeline Orchestrator

Create worker/pipeline.py with:

run_job(job_id: str, input_path: str, params: dict) -> None

Steps (strict order):

Prepare workspace: create /data/artifacts/<job_id>/ and _pipeline.log.

Probe + extract: if video, extract audio; accept H.265; output 16kHz mono WAV for ASR (-ar 16000 -ac 1).

Normalize: EBU R128 loudness via loudnorm (e.g., I=-16:TP=-1.5:LRA=11).

ASR: run faster-whisper (model from settings) with chunking for long files; keep token timestamps.

Alignment: WhisperX word-level timestamps using the audio + ASR text.

Diarization: pyannote.audio; map speaker turns to words/segments by overlap.

Speaker embeddings: create ECAPA embeddings; store vectors in embeddings table (pgvector); cosine sim for known speaker assignment (threshold from settings).

Artifacts: write JSON (segments + words + speakers), SRT, VTT, TXT; update transcripts/segments tables.

Archival: encode Opus (Ogg) ~24 kbps VBR and write to /data/archival.

LLM (optional): call LLM service for title/summary/tags (if enabled in settings and within token caps).

Mark job SUCCEEDED or FAILED with error summary; always append to _pipeline.log.

Notes:

Use a simple GPU mutex (file lock under /tmp/voicestack_gpu.lock or Redis lock) so ASR/alignment don’t fight for VRAM.

Offload LLM to CPU/external provider if GPU is busy (configurable in settings).

Never import heavy ML libs at module import time inside API; only the worker.

4.2 Worker: Modules (create stubs if light on time)

Files under worker/:

audio.py — ffmpeg helpers (probe(), to_wav_16k_mono(), normalize_loudness(), to_opus_archival()).

asr.py — faster-whisper inference with chunking; return segments with token timestamps.

align.py — WhisperX alignment; return words with start/end.

diarize.py — pyannote pipeline; return speaker turns.

speaker.py — ECAPA embedding + cosine similarity + merge util.

embeddings.py — sentence-transformers for text embeddings (Phase 3 search).

llm.py — Provider-agnostic client (see 4.4) returning title/summary/tags.

utils.py — logging, UUID/time helpers, Redis lock.

db.py — shared ORM session helpers (import from api/db/session.py if possible, or duplicate minimal session code to avoid API import side-effects).

4.3 API: Endpoints to Wire Worker Results

/jobs — add GET /{id} to fetch single job with assets + transcript status.

/transcripts/{id} — ensure response includes segments + per-word timings + speaker names.

/speakers/merge — implement DB-level merge (Phase 2.5): reassign segments.speaker_id, append embeddings, delete source, write audit note in artifacts log.

/email/transcript — implement actual send using SMTP settings; attach TXT & VTT, include link to artifacts directory (path only).

4.4 LLM Service (Adapter Pattern)

Create api/services/llm/ with pluggable providers:

base.py: class LLMProvider(Protocol) with generate_title(text, **cfg), summarize(text, **cfg), suggest_tags(text, **cfg).

openai.py, openrouter.py, local_http.py (Open WebUI / LM Studio style). Read base URL, API key, model name, input/output caps from DB settings. Never hardcode. Handle 429/backoff.

factory.py: choose provider based on settings.model_config.llm_provider.

Settings additions (DB schema stays JSON-friendly):

{
  "models": {
    "whisper_model": "large-v3",
    "whisper_compute_type": "float16",
    "llm_provider": "openai|openrouter|local",
    "llm_model": "gpt-4o-mini",
    "llm_base_url": "https://api.openai.com/v1",
    "llm_api_key": "<masked>",
    "llm_max_input_tokens": 4000,
    "llm_max_output_tokens": 800
  }
}

API should not expose secrets on GET /settings (mask), but should accept updates on PUT /settings.

4.5 Web (Next.js app dir) — Minimal Admin UI

Create basic pages/components:

Upload page: choose file → POST /upload with Bearer.

Jobs list: list with status chips; cancel/reprocess actions.

Job detail: show artifacts links (TXT/VTT/SRT), transcript preview if available.

Settings page: edit SMTP + model selections + LLM provider config; save via /settings.

Transcript viewer (read-only): per-segment with word-level highlight (layout only; data from API).

Use Tailwind + shadcn/ui + basic toasts (no need to over-style). Configure NEXT_PUBLIC_API_URL env.

5) Non-Goals for Phase 2

Full-text semantic search UI (Phase 3)

Frontend authentication beyond Bearer in env (Phase 3/4)

Fancy player with waveform rendering (Phase 3)

6) Testing & Smoke Checks

pytest for small units where practical (audio utils, LLM adapter selection).

Manual smoke:

curl /health

PUT /settings with Bearer → set SMTP + models + LLM provider

POST /upload (small WAV) → observe RQ job logs → artifacts files appear

GET /transcripts/{id} returns segments & words & speakers

POST /email/transcript sends email (stub OK if SMTP not set)

7) Reliability & Logging

All pipeline steps must append to <artifacts>/_pipeline.log (human-readable).

On failure: mark job FAILED, keep partial artifacts, and write error summary to DB jobs.log_path.

Timeouts: ASR/alignment jobs should respect job_timeout from enqueue call.

8) Performance & GPU Policy

Use a simple Redis/file lock to serialize GPU-heavy steps.

Support compute types float16 or int8 for faster-whisper (from settings).

Defer LLM calls until GPU is free or run via cloud/local HTTP.

9) Deliverables Format (IMPORTANT)

When you implement/modify code:

Output full file contents with absolute repo paths for all new/changed files.

Print a compact file tree of impacted paths.

STOP and wait for confirmation—don’t auto-continue.

10) Guardrails Recap

Don’t change compose or Dockerfiles unless asked.

Don’t introduce Celery/FAISS/other stacks.

Don’t hardcode credentials or model names.

Keep endpoints backward-compatible.

11) Phase 3 (Preview — do not start)

Semantic search API and UI using sentence-transformers + pgvector

Rich transcript player w/ word highlight + seek

Speaker management UI (merge, rename, trust flag)

Share/Export flows (download artifacts)

