#!/bin/sh
set -e

MODEL_PATH="/app/models/ggml-small.en.bin"

if [ ! -f "$MODEL_PATH" ]; then
  echo "Modelo no encontrado, descargando..."
  mkdir -p /app/models
  wget -O "$MODEL_PATH" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin
else
  echo "Modelo encontrado, usando cache existente."
fi

# Ejecutar uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 9000
