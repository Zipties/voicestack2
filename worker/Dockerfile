FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in stages to handle timeouts
COPY requirements.txt ./

# First install core dependencies that are essential for the worker to start
RUN pip install --no-cache-dir rq redis python-dotenv sqlalchemy psycopg[binary] pydantic fastapi uvicorn httpx

# Then install ML dependencies (this is the time-consuming part)
RUN pip install --no-cache-dir "torch>=2.0.0,<2.4.0" ctranslate2==4.0.0 numpy

# Finally install remaining audio processing dependencies
RUN pip install --no-cache-dir faster-whisper whisperx pyannote.audio speechbrain transformers sentence-transformers pgvector tiktoken

COPY . .
CMD ["python","worker.py"]
