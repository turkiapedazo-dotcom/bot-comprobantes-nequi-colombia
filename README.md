# Bot de Comprobantes Telegram

Bot de Telegram para generar comprobantes de Nequi, BRE-B, QR, LLAVES y Bancolombia.

## 🚀 Despliegue en Zeabur

### Requisitos
- Cuenta en [Zeabur](https://zeabur.com)
- Token de bot de Telegram (obtener de [@BotFather](https://t.me/botfather))

### Pasos para desplegar

1. **Conectar repositorio a Zeabur**
   - Crear nuevo proyecto en Zeabur
   - Conectar con tu repositorio Git

2. **Configurar variables de entorno**
   En Zeabur, agregar:
   ```
   TELEGRAM_BOT_TOKEN=tu_token_de_telegram
   ```

3. **Desplegar**
   - Zeabur detectará automáticamente el Dockerfile
   - El bot se desplegará automáticamente

## 📋 Características

- ✅ Comprobantes: Nequi, BRE-B, QR, LLAVES
- ✅ Movimientos automáticos con saldo negativo
- ✅ Ofuscación de nombres según tipo
- ✅ Eliminación automática de tildes
- ✅ Formato Title Case en comprobantes
- ✅ Validación de datos (@ en llaves BRE-B, dígitos, etc.)

## 🛠️ Desarrollo Local

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Crear archivo `.env`:
   ```
   TELEGRAM_BOT_TOKEN=tu_token
   ```

3. Ejecutar:
   ```bash
   python main.py
   ```

## 📁 Estructura

- `main.py` - Bot de Telegram y flujos
- `utils.py` - Generación de comprobantes
- `config.py` - Configuración de plantillas
- `auth_system.py` - Sistema de autenticación
- `img/` - Plantillas de comprobantes
- `fuentes/` - Fuentes para textos
