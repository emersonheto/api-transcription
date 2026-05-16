# app/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
import os

from .utils import model, split_into_short_segments

app = FastAPI(
    title="API Subtítulos Whisper",
    description="Transcribe MP3 y devuelve JSON de segmentos para subtítulos.",
    version="1.0.0"
)

@app.post("/transcribe")
async def transcribe_mp3(file: UploadFile = File(...)):
    """
    Recibe un archivo MP3, lo transcribe usando Whisper y devuelve
    JSON con segmentos en formato:
    { "segments": [ {"start":0, "end":3.2, "text":"..."} ] }
    """
    suffix = os.path.splitext(file.filename)[1]
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Transcripción usando Whisper
        result = model.transcribe(tmp_path, language="es")

        # Re-segmentar en subtítulos más legibles
        segments = split_into_short_segments(result["segments"], max_words=15)

        return JSONResponse(content={"segments": segments})

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)