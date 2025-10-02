from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import os
import uuid
import shutil

app = FastAPI()

MODEL_PATH = "/app/models/ggml-small.en.bin"  # donde estará el modelo en el contenedor
WHISPER_BIN = "/app/whisper.cpp/main"  # ruta al binario compilado


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

    # Convertir a wav 16k mono (por compatibilidad) -> salida tmp_wav
    tmp_wav = tmp_input + ".wav"
    try:
        # -y sobreescribe si existe
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_input, "-ar", "16000", "-ac", "1", tmp_wav],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        # si ffmpeg falla, proceder a intentar usar el archivo original
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        # no abortamos aún, intentaremos usar el archivo original
        tmp_wav = tmp_input

    # Ejecutar whisper.cpp (main) sobre tmp_wav
    if not os.path.exists(WHISPER_BIN):
        raise HTTPException(
            status_code=500, detail="Whisper binary not found in container"
        )

    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=500, detail="Modelo no encontrado en /app/models"
        )

    try:
        proc = subprocess.run(
            [WHISPER_BIN, "-m", MODEL_PATH, "-f", tmp_wav],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        transcription = proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        transcription = e.stdout + "\n" + e.stderr
    except subprocess.TimeoutExpired:
        transcription = "[error] timeout durante inferencia"

    # limpiar archivos temporales
    try:
        os.remove(tmp_input)
        if tmp_wav != tmp_input and os.path.exists(tmp_wav):
            os.remove(tmp_wav)
    except:
        pass

    return JSONResponse({"transcription": transcription})
