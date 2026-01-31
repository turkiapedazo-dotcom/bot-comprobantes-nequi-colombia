# Imagen slim con Python
FROM python:3.11-slim

# Instalar libzbar (necesario para pyzbar)
RUN apt-get update && apt-get install -y --no-install-recommends libzbar0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY main.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
