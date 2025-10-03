FROM python:3.11-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential git wget cmake ffmpeg libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clonar whisper.cpp y compilar
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp /app/whisper.cpp \
    && make -C /app/whisper.cpp -j$(nproc)

# Copiar requirements y API
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY entrypoint.sh .

# Dar permisos de ejecución al entrypoint
RUN chmod +x entrypoint.sh

EXPOSE 9000

CMD ["./entrypoint.sh"]
