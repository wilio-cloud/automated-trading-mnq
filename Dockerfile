FROM python:3.11-slim

WORKDIR /app

# Logs sense buffering per veure'ls a l'instant al dashboard
ENV PYTHONUNBUFFERED=1
ENV TZ=America/New_York

# Instalar zona horària i paquets base
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codi del bot
COPY bot/ ./bot/
COPY run_bot.sh .

# Comanda d'arrencada com a procés continu
CMD ["python", "bot/main.py"]
