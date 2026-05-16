# app/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import os
import mimetypes
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .utils import get_model, split_into_short_segments

app = FastAPI(
    title="API Subtítulos Whisper",
    description="Transcribe MP3 y devuelve JSON de segmentos para subtítulos.",
    version="1.0.0"
)

# Thread pool for CPU-heavy Whisper transcription work
executor = ThreadPoolExecutor(max_workers=2)

def run_in_threadpool(func, *args, **kwargs):
    """Run a function in a thread pool to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, func, *args, **kwargs)

@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment verification.
    Returns status without loading Whisper model.
    """
    return {"status": "ok"}

@app.post("/transcribe")
async def transcribe_mp3(file: UploadFile = File(...)):
    """
    Recibe un archivo de audio (MP3/WAV), lo transcribe usando Whisper y devuelve
    JSON con segmentos en formato:
    { "segments": [ {"start":0, "end":3.2, "text":"..."} ] }

    Límites:
    - Tamaño máximo: 25MB
    - Formatos: MP3, WAV, M4A, OGG
    """
    # 1. Validar tipo MIME (seguridad básica)
    allowed_types = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/m4a", "audio/ogg"]
    file_mime = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

    if file_mime not in allowed_types and not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail={"error": "invalid_file_type"})

    # 2. Validar tamaño (25MB máximo para no llenar el disco del tier gratuito)
    MAX_SIZE_MB = 25
    MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

    content = await file.read()

    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={"error": "file_too_large"})

    if len(content) == 0:
        raise HTTPException(status_code=400, detail={"error": "empty_file"})

    suffix = os.path.splitext(file.filename)[1]
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Get model (lazy loaded on first use)
        model = get_model()

        # Transcribe in thread pool to avoid blocking event loop
        def _transcribe():
            return model.transcribe(tmp_path, language="es")

        result = await run_in_threadpool(_transcribe)

        # Re-segmentar en subtítulos más legibles
        segments = split_into_short_segments(result["segments"], max_words=15)

        return JSONResponse(content={"segments": segments})

    except Exception as e:
        # Error without leaking filesystem paths or stack traces
        raise HTTPException(status_code=500, detail={"error": "transcription_failed"})

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)