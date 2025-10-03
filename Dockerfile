FROM python:3.11-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential git wget cmake ffmpeg libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Clonar whisper.cpp y compilar
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp /app/whisper.cpp \
    && make -C /app/whisper.cpp -j$(nproc)

# Copiar requirements y API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Crear carpeta de modelos (se llenará con un volumen persistente en Dokploy)
RUN mkdir -p /app/models

# Exponer puerto (igual que en main.py uvicorn)
EXPOSE 9000

# Ejecutar uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
