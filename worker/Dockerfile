FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (git needed for some ML packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in stages
COPY requirements.txt ./

# First install core dependencies
RUN pip install --no-cache-dir rq redis python-dotenv sqlalchemy psycopg[binary] pydantic fastapi uvicorn httpx

# Install PyTorch with CUDA support (will use CPU if GPU not available)
RUN pip install --no-cache-dir torch torchvision torchaudio

# Install OpenAI Whisper instead of faster-whisper (no ctranslate2)
RUN pip install --no-cache-dir openai-whisper

# Install remaining audio processing dependencies
# Note: whisperx might still have issues, but we'll try
RUN pip install --no-cache-dir \
    whisperx \
    pyannote.audio \
    speechbrain \
    transformers \
    sentence-transformers \
    pgvector \
    tiktoken \
    librosa \
    numba

COPY . .
CMD ["python","worker.py"]
