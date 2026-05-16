# app/utils.py

import whisper
import os

# Cargar modelo Whisper al iniciar la API
# Default: "small" (467MB) - Balance perfecto de precisión y velocidad para 8GB RAM.
# Para máxima calidad: cambiar a "medium" (1.4GB).
# Para máxima velocidad: cambiar a "tiny" (74MB).
model_name = os.getenv("MODEL_NAME", "small")
model = whisper.load_model(model_name)

def split_into_short_segments(whisper_segments, max_words=15):
    """
    Re-segmenta los bloques de Whisper en subtítulos más cortos y legibles.
    max_words: cantidad máxima de palabras por segmento
    """
    new_segments = []

    for seg in whisper_segments:
        text = seg.get("text", "").strip()
        start = seg.get("start", 0.0)
        end = seg.get("end", start + 2.0)
        duration = end - start
        if not text:
            continue

        # Separar frases por puntuación
        sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]

        for sentence in sentences:
            words = sentence.split()
            for i in range(0, len(words), max_words):
                chunk_words = words[i:i + max_words]
                if len(chunk_words) < 3:
                    continue
                chunk_text = " ".join(chunk_words)
                chunk_start = start + duration * (i / len(words))
                chunk_end = start + duration * ((i + len(chunk_words)) / len(words))
                new_segments.append({
                    "start": round(chunk_start, 2),
                    "end": round(chunk_end, 2),
                    "text": chunk_text
                })

    return new_segments