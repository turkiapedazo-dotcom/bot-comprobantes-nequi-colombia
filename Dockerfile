# Usar Python 3.11 slim como base
# Updated: 2026-01-31 - Added libzbar0 support
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para Pillow y zbar
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del proyecto
COPY . .

# Crear directorio para logs si no existe
RUN mkdir -p /app/logs

# Inicializar archivos JSON vacíos si no existen (se crearán automáticamente por el bot)
RUN touch /app/users.json /app/groups.json /app/logs.json /app/settings.json || true

# Variables de entorno (se sobrescribirán con las de Zeabur)
ENV PYTHONUNBUFFERED=1

# Exponer puerto para health checks de Zeabur
EXPOSE 8080

# Crear script de inicio para health check HTTP
RUN printf '#!/usr/bin/env python3\nimport http.server\nimport socketserver\nimport threading\nimport os\nimport subprocess\nimport sys\n\nPORT = int(os.getenv("PORT", "8080"))\n\nclass HealthHandler(http.server.SimpleHTTPRequestHandler):\n    def do_GET(self):\n        self.send_response(200)\n        self.send_header("Content-type", "text/plain")\n        self.end_headers()\n        self.wfile.write(b"OK")\n    def log_message(self, format, *args):\n        pass\n\nserver = socketserver.TCPServer(("0.0.0.0", PORT), HealthHandler)\nthread = threading.Thread(target=server.serve_forever, daemon=True)\nthread.start()\nprint(f"Health check server started on port {PORT}")\nsys.exit(subprocess.call([sys.executable, "main.py"]))\n' > /app/start.py && chmod +x /app/start.py

# Comando para ejecutar el bot con health check
CMD ["python3", "start.py"]
