FROM python:3.11-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential git wget cmake ffmpeg libsndfile1-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clonar whisper.cpp, compilar y mover binario
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp /app/whisper.cpp \
    && cd /app/whisper.cpp \
    && make -j$(nproc) \
    && ls -lh /app/whisper.cpp/build/bin \
    && cp /app/whisper.cpp/build/bin/main /app/whisper.cpp/main \
    && chmod +x /app/whisper.cpp/main

# Copiar requirements y API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY entrypoint.sh .

# Dar permisos de ejecución al entrypoint
RUN chmod +x entrypoint.sh

EXPOSE 9000

CMD ["./entrypoint.sh"]
