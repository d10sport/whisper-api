from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import os
import uuid

app = FastAPI()

MODEL_PATH = "/app/models/ggml-small.en.bin"  # modelo en el contenedor
WHISPER_BIN = "/app/whisper.cpp/main"  # binario compilado (whisper-cli)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Guardar archivo temporal
    tmp_dir = "/tmp/whisper"
    os.makedirs(tmp_dir, exist_ok=True)
    random_name = f"{uuid.uuid4().hex}_{file.filename}"
    tmp_input = os.path.join(tmp_dir, random_name)

    with open(tmp_input, "wb") as f:
        f.write(await file.read())

    # Convertir a wav 16k mono (compatibilidad) -> salida tmp_wav
    tmp_wav = tmp_input + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_input, "-ar", "16000", "-ac", "1", tmp_wav],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # si ffmpeg falla, usar archivo original
        tmp_wav = tmp_input

    # Validar binario y modelo
    if not os.path.exists(WHISPER_BIN):
        raise HTTPException(
            status_code=500, detail="Whisper binary not found in container"
        )
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=500, detail="Modelo no encontrado en /app/models"
        )

    try:
        # Whisper-cli genera archivos de salida (txt, srt, etc.)
        out_file = tmp_wav + ".txt"

        subprocess.run(
            [WHISPER_BIN, "-m", MODEL_PATH, "-f", tmp_wav, "-otxt", "-of", tmp_wav],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )

        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8") as f:
                transcription = f.read().strip()
        else:
            transcription = "[error] no se generó el archivo de salida"

    except subprocess.TimeoutExpired:
        transcription = "[error] timeout durante inferencia"
    except subprocess.CalledProcessError as e:
        transcription = e.stdout + "\n" + e.stderr

    # limpiar archivos temporales
    try:
        if os.path.exists(tmp_input):
            os.remove(tmp_input)
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        if os.path.exists(out_file):
            os.remove(out_file)
    except:
        pass

    return JSONResponse({"transcription": transcription})
