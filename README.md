# 🤖 Bot Generador de Comprobantes Nequi Colombia

Un bot de Telegram avanzado para generar comprobantes bancarios realistas de diferentes plataformas financieras colombianas.

## 🚀 Características

### 💎 Comprobantes de Alta Calidad
- **Nequi a Nequi**: Transferencias entre cuentas Nequi
- **Llave BRE-B**: Transferencias por llave bancaria
- **Bancolombia**: Comprobantes de Bancolombia
- **Envío Recibido**: Comprobantes de dinero recibido
- **QR Voucher**: Comprobantes de pagos por QR

### 📱 Comprobantes Estándar
- Nequi (transferencias básicas)
- BRE-B (transferencias interbancarias)
- QR Comprobantes
- Llaves bancarias
- Bancolombia a Nequi
- QR Bancolombia
- BC a BC (Bancolombia a Bancolombia)
- DaviPlata y QR DaviPlata
- Llaves DaviPlata
- NQ QR Normal
- Comprobantes anulados

### 🔧 Funcionalidades Técnicas
- **Lectura de QR**: Escaneo automático de códigos QR
- **Formato de dinero**: Formato colombiano (20.000,00)
- **Fechas automáticas**: Fecha y hora de Colombia
- **Referencias únicas**: Generación automática de referencias
- **Conversión HTML a imagen**: Templates HTML convertidos a PNG
- **Sistema de autorización**: Control de acceso por usuarios y grupos
- **Anti-spam**: Protección contra uso excesivo

## 🛠️ Instalación

### Prerrequisitos
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv libzbar0 wkhtmltopdf

# CentOS/RHEL
sudo yum install python3 python3-pip zbar libzbar-dev wkhtmltopdf
```

### Configuración
1. **Clona el repositorio**:
```bash
git clone https://github.com/tu-usuario/bot-comprobantes-nequi.git
cd bot-comprobantes-nequi
```

2. **Crea el entorno virtual**:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

3. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configura las variables de entorno**:
```bash
cp .env.example .env
# Edita .env con tu token de bot
```

5. **Configura los archivos JSON**:
```bash
cp users.json.example users.json
cp groups.json.example groups.json
cp logs.json.example logs.json
```

## ⚙️ Configuración

### Variables de Entorno (.env)
```env
BOT_TOKEN=tu_token_de_telegram_bot_aqui
```

### Archivos de Configuración

#### users.json
```json
{
  "users": [123456789, 987654321]
}
```

#### groups.json
```json
{
  "groups": [-1001234567890]
}
```

## 🚀 Uso

### Iniciar el Bot
```bash
# Desarrollo
python main.py

# Producción con screen
screen -dmS bot python main.py

# Con Docker
docker build -t bot-comprobantes .
docker run -d --name bot-comprobantes bot-comprobantes
```

### Comandos del Bot
- `/start` - Iniciar el bot
- `/nequicol` - Mostrar menú principal
- `/cancelar` - Cancelar operación actual
- `/masinf` - Información sobre funciones avanzadas

### Comandos de Administrador
- `/adduser <user_id>` - Agregar usuario autorizado
- `/removeuser <user_id>` - Remover usuario
- `/addgroup <group_id>` - Agregar grupo autorizado
- `/removegroup <group_id>` - Remover grupo
- `/users` - Listar usuarios autorizados
- `/groups` - Listar grupos autorizados
- `/logs` - Ver registros de uso
- `/stats` - Estadísticas del bot
- `/maintenance` - Activar/desactivar mantenimiento
- `/broadcast <mensaje>` - Enviar mensaje a todos los usuarios

## 🏗️ Arquitectura

### Estructura del Proyecto
```
bot-comprobantes-nequi/
├── main.py                 # Archivo principal del bot
├── auth_system.py          # Sistema de autorización
├── config.py              # Configuraciones de comprobantes
├── utils.py               # Utilidades y generadores
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Configuración Docker
├── .env.example           # Ejemplo de variables de entorno
├── vouchers_html/         # Templates HTML de alta calidad
│   ├── 1_nequi_a_nequi (2).html
│   ├── 2_llave_breb (2).html
│   ├── 4_bancolombia (2).html
│   ├── 5_envio_recibido (2).html
│   └── 6_qr_vouch_pago_qr (2).html
├── img/                   # Imágenes y plantillas
├── fuentes/              # Fuentes tipográficas
└── upload_fix.py         # Script de actualización
```

### Tecnologías Utilizadas
- **Python 3.8+**: Lenguaje principal
- **python-telegram-bot**: API de Telegram
- **Pillow (PIL)**: Procesamiento de imágenes
- **pyzbar**: Lectura de códigos QR
- **wkhtmltopdf**: Conversión HTML a imagen
- **APScheduler**: Tareas programadas
- **python-dotenv**: Variables de entorno

## 🔒 Seguridad

### Sistema de Autorización
- Control de acceso por usuario y grupo
- Lista blanca de usuarios autorizados
- Verificación de membresía en grupos
- Modo mantenimiento para administradores

### Anti-Spam
- Cooldown entre comandos
- Límite de operaciones por usuario
- Detección de uso excesivo

### Validaciones
- Validación de entrada de datos
- Sanitización de nombres y números
- Verificación de formatos de imagen

## 📊 Monitoreo

### Logs del Sistema
- Registro de todos los comandos ejecutados
- Tracking de usuarios y grupos
- Estadísticas de uso por tipo de comprobante
- Detección de errores y excepciones

### Métricas Disponibles
- Usuarios activos por día/semana/mes
- Comprobantes generados por tipo
- Grupos más activos
- Errores más frecuentes

## 🐳 Docker

### Construcción
```bash
docker build -t bot-comprobantes .
```

### Ejecución
```bash
docker run -d \
  --name bot-comprobantes \
  -e BOT_TOKEN=tu_token_aqui \
  -v $(pwd)/data:/app/data \
  bot-comprobantes
```

### Docker Compose
```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=tu_token_aqui
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## 🔧 Desarrollo

### Agregar Nuevos Comprobantes
1. Crear configuración en `config.py`
2. Implementar generador en `utils.py`
3. Agregar botón en `main.py`
4. Crear template HTML si es de alta calidad

### Estructura de Configuración
```python
NUEVO_COMPROBANTE_CONFIG = {
    'template_path': 'img/plantilla_nueva.jpg',
    'positions': {
        'nombre': (x, y),
        'valor': (x, y),
        'fecha': (x, y),
        'referencia': (x, y)
    },
    'font_sizes': {
        'nombre': 24,
        'valor': 28,
        'fecha': 20,
        'referencia': 18
    }
}
```

## 📝 Changelog

### v2.0.0 (Actual)
- ✅ Comprobantes de alta calidad con templates HTML
- ✅ Corrección de formato de fechas
- ✅ Formato de dinero colombiano (20.000,00)
- ✅ Optimización de velocidad de generación
- ✅ Sistema de autorización mejorado
- ✅ Anti-spam y cooldowns

### v1.0.0
- ✅ Comprobantes básicos con imágenes
- ✅ Sistema de autorización básico
- ✅ Lectura de códigos QR
- ✅ Comandos de administración

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Disclaimer

Este bot está diseñado únicamente para fines educativos y de demostración. No debe ser utilizado para crear documentos fraudulentos o engañar a terceros. Los desarrolladores no se hacen responsables del mal uso de esta herramienta.

## 📞 Soporte

- **Telegram**: @Axondevui
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/bot-comprobantes-nequi/issues)
- **Grupo Oficial**: [Nequi Colombia Free](https://t.me/Nequicolombiafreee)

---

**Desarrollado con ❤️ para la comunidad colombiana**