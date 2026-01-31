import json
import os
import logging
import re
import asyncio
from io import BytesIO
from typing import Set, Dict, Any

# Configurar logging mínimo para inicio rápido
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

# Imports directos sin try/except para inicio más rápido
from PIL import Image
from pyzbar.pyzbar import decode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update

# --- Configuración ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'TELEGRAM_BOT_TOKEN')
ADMIN_IDS = {8575033873, 8485045964}
GRUPO_OFICIAL = -1003438094357
DB_AUTORIZADOS = "usuarios_autorizados_qr.json"
DB_MODO = "modo_estado_qr.json"
DB_REGISTROS = "usuarios_registrados_qr.json"
DB_GRUPOS = "grupos_permitidos_qr.json"

# --- Owners del bot ---
OWNER_PRINCIPAL = "@stevenappsshops"
OWNER_SECUNDARIO = "@AXONDEVUI"

# --- Estado ---
# Diccionario para rastrear usuarios y chats que han activado /qrnequiusa
# Estructura: {(user_id, chat_id): True}
usuarios_qrnequiusa_activos = {}

# Estado de grupos (on/off por grupo)
DB_GRUPOS_ESTADO = "grupos_estado_qr.json"

def cargar_grupos_estado() -> Dict[int, bool]:
    try:
        if not os.path.exists(DB_GRUPOS_ESTADO):
            with open(DB_GRUPOS_ESTADO, "w") as f:
                json.dump({}, f, indent=4)
        with open(DB_GRUPOS_ESTADO, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except Exception as e:
        logging.error(f"Error al cargar estado de grupos: {e}")
        return {}

def guardar_grupos_estado(estados: Dict[int, bool]) -> None:
    try:
        with open(DB_GRUPOS_ESTADO, "w") as f:
            json.dump(estados, f, indent=4)
    except Exception as e:
        logging.error(f"Error al guardar estado de grupos: {e}")

grupos_estado = cargar_grupos_estado()

def cargar_estado() -> Dict[str, bool]:
    try:
        if os.path.exists(DB_MODO):
            with open(DB_MODO, "r") as f:
                data = json.load(f)
                return {"apagado": data.get("apagado", False), "gratis": data.get("gratis", False)}
        return {"apagado": False, "gratis": False}
    except Exception as e:
        logging.error(f"Error al cargar estado: {e}")
        return {"apagado": False, "gratis": False}

def guardar_estado(estado: Dict[str, bool]) -> None:
    try:
        with open(DB_MODO, "w") as f:
            json.dump(estado, f, indent=4)
    except Exception as e:
        logging.error(f"Error al guardar estado: {e}")

# --- Autorizados ---
def cargar_autorizados() -> Set[int]:
    try:
        if not os.path.exists(DB_AUTORIZADOS):
            with open(DB_AUTORIZADOS, "w") as f:
                json.dump(list(ADMIN_IDS), f, indent=4)
        with open(DB_AUTORIZADOS, "r") as f:
            return set(json.load(f))
    except Exception as e:
        logging.error(f"Error al cargar autorizados: {e}")
        return set(ADMIN_IDS)

def guardar_autorizados(usuarios: Set[int]) -> None:
    try:
        with open(DB_AUTORIZADOS, "w") as f:
            json.dump(list(usuarios), f, indent=4)
    except Exception as e:
        logging.error(f"Error al guardar autorizados: {e}")

# --- Grupos ---
def cargar_grupos() -> Set[int]:
    try:
        if not os.path.exists(DB_GRUPOS):
            with open(DB_GRUPOS, "w") as f:
                json.dump([GRUPO_OFICIAL], f, indent=4)
        with open(DB_GRUPOS, "r") as f:
            return set(json.load(f))
    except Exception as e:
        logging.error(f"Error al cargar grupos: {e}")
        return {GRUPO_OFICIAL}

def guardar_grupos(grupos: Set[int]) -> None:
    try:
        with open(DB_GRUPOS, "w") as f:
            json.dump(list(grupos), f, indent=4)
    except Exception as e:
        logging.error(f"Error al guardar grupos: {e}")

# --- Registros ---
def cargar_registros() -> Dict[int, Dict[str, Any]]:
    try:
        if not os.path.exists(DB_REGISTROS):
            with open(DB_REGISTROS, "w") as f:
                json.dump({}, f, indent=4)
        with open(DB_REGISTROS, "r") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except Exception as e:
        logging.error(f"Error al cargar registros: {e}")
        return {}

def guardar_registros(registros: Dict[int, Dict[str, Any]]) -> None:
    try:
        with open(DB_REGISTROS, "w") as f:
            json.dump(registros, f, indent=4, default=str)
    except Exception as e:
        logging.error(f"Error al guardar registros: {e}")

# --- Cargar datos ---
autorizados = cargar_autorizados()
grupos_permitidos = cargar_grupos()
registrados = cargar_registros()

def es_autorizado(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in autorizados

def es_grupo_permitido(chat_id: int) -> bool:
    return chat_id in grupos_permitidos

async def verificar_miembro_grupo(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Verifica si el usuario es miembro del grupo oficial"""
    try:
        member = await context.bot.get_chat_member(chat_id=GRUPO_OFICIAL, user_id=user_id)
        # Estados válidos: member, administrator, creator
        es_miembro = member.status in ['member', 'administrator', 'creator']
        logging.info(f"Usuario {user_id} - Estado en grupo: {member.status} - Es miembro: {es_miembro}")
        return es_miembro
    except Exception as e:
        logging.error(f"Error al verificar membresía del usuario {user_id}: {e}")
        # Si hay error verificando, permitir acceso para evitar bloqueos
        logging.warning(f"Permitiendo acceso al usuario {user_id} por error en verificación")
        return True

# --- Comandos admin ---
async def help_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    texto = (
        "📜 Comandos de administrador QR:\n\n"
        "🔹 **Gestión de usuarios:**\n"
        "/registros - Ver usuarios que usaron /qrnequiusa\n"
        "/agregar <id> - Agregar usuario autorizado\n"
        "/eliminarusuario <id> - Eliminar usuario\n\n"
        "🔹 **Gestión de grupos:**\n"
        "/agregargrupo <id> - Agregar grupo permitido\n"
        "/eliminargrupo <id> - Eliminar grupo\n"
        "/ongrupo - Encender bot en el grupo actual\n"
        "/offgrupo - Apagar bot en el grupo actual\n\n"
        "🔹 **Control del bot:**\n"
        "/on - Activar bot (encender)\n"
        "/off - Apagar bot completamente\n"
        "/gratis - Activar modo gratis para todos\n"
        "/premium - Desactivar modo gratis\n\n"
        f"👑 Owner Principal: {OWNER_PRINCIPAL}\n"
        f"👤 Owner Secundario: {OWNER_SECUNDARIO}\n\n"
        "/help - Ver este menú"
    )
    await update.message.reply_text(texto)

async def registros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not registrados:
        await update.message.reply_text("📄 No hay usuarios registrados.")
        return

    texto = "📄 **Usuarios que han usado /qrnequiusa:**\n\n"
    for uid, info in registrados.items():
        username = info.get("username")
        nombre = info.get("nombre") or "Sin nombre"
        fecha = info.get("fecha") or "Sin fecha"
        
        # Formatear username
        user_str = f"@{username}" if username else "Sin username"
        
        texto += f"👤 **Usuario:** {user_str}\n"
        texto += f"🆔 **ID:** `{uid}`\n"
        texto += f"📝 **Nombre:** {nombre}\n"
        texto += f"📅 **Última vez:** {fecha}\n"
        texto += "─" * 30 + "\n\n"

    await update.message.reply_text(texto, parse_mode='Markdown')

async def agregargrupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /agregargrupo <id>")
        return
    try:
        gid = int(context.args[0])
        grupos_permitidos.add(gid)
        guardar_grupos(grupos_permitidos)
        await update.message.reply_text(f"✅ Grupo {gid} agregado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")

async def eliminargrupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /eliminargrupo <id>")
        return
    try:
        gid = int(context.args[0])
        if gid in grupos_permitidos:
            grupos_permitidos.remove(gid)
            guardar_grupos(grupos_permitidos)
            await update.message.reply_text(f"🗑️ Grupo {gid} eliminado.")
        else:
            await update.message.reply_text("❌ Grupo no encontrado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")

async def agregarusuario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /agregar <id>")
        return
    try:
        uid = int(context.args[0])
        autorizados.add(uid)
        guardar_autorizados(autorizados)
        await update.message.reply_text(f"✅ Usuario {uid} agregado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")

async def eliminarusuario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /eliminarusuario <id>")
        return
    try:
        uid = int(context.args[0])
        if uid in autorizados:
            autorizados.remove(uid)
            guardar_autorizados(autorizados)
            await update.message.reply_text(f"🗑️ Usuario {uid} eliminado.")
        else:
            await update.message.reply_text("❌ Usuario no encontrado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")

async def on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    estado = cargar_estado()
    estado["apagado"] = False
    guardar_estado(estado)
    await update.message.reply_text("✅ Bot QR activado y funcionando.")

async def off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    estado = cargar_estado()
    estado["apagado"] = True
    guardar_estado(estado)
    await update.message.reply_text("⛔ Bot QR apagado completamente.")

async def gratis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    estado = cargar_estado()
    estado["gratis"] = True
    estado["apagado"] = False
    guardar_estado(estado)
    await update.message.reply_text("✅ Bot QR activado en modo gratis para todos.")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    estado = cargar_estado()
    estado["gratis"] = False
    guardar_estado(estado)
    await update.message.reply_text("✅ Modo gratis desactivado. Solo usuarios autorizados.")

# --- Comandos de grupo ---
async def ongrupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    
    if chat_type not in ("group", "supergroup"):
        await update.message.reply_text("❌ Este comando solo funciona en grupos.")
        return
    
    grupos_estado[chat_id] = True
    guardar_grupos_estado(grupos_estado)
    await update.message.reply_text("✅ Bot QR activado en este grupo.")

async def offgrupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos.")
        return
    
    if chat_type not in ("group", "supergroup"):
        await update.message.reply_text("❌ Este comando solo funciona en grupos.")
        return
    
    grupos_estado[chat_id] = False
    guardar_grupos_estado(grupos_estado)
    await update.message.reply_text(f"⛔ Bot QR apagado en este grupo.\n\n💎 Para acceso V.I.P contacta a {OWNER_PRINCIPAL}")

# --- Start con registro y bloqueo ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.effective_chat.type
    user = update.effective_user
    user_id = user.id

    logging.info(f"Comando /start recibido de usuario {user_id} (@{user.username})")

    if chat_type != "private":
        logging.info(f"Ignorando /start en chat tipo {chat_type}")
        return

    username = user.username or ""
    nombre = f"{user.first_name or ''} {user.last_name or ''}".strip()
    fecha_actual = str(update.message.date)

    registrados[user_id] = {
        "username": username or None,
        "nombre": nombre or "Sin nombre",
        "fecha": fecha_actual
    }
    guardar_registros(registrados)

    # Verificar si el usuario es miembro del grupo (excepto admins, solo en chats privados)
    if user_id not in ADMIN_IDS and chat_type == "private":
        es_miembro = await verificar_miembro_grupo(context, user_id)
        if not es_miembro:
            mensaje = (
                "👋 ¡Bienvenido al Bot QR!\n\n"
                "📌 Para usar este bot, primero debes unirte a nuestro grupo oficial:\n\n"
                "[👉 NEQUI USA](https://t.me/nequiusa)\n\n"
                "✅ Una vez que te unas, presiona /qrnequiusa para comenzar."
            )
            await update.message.reply_text(mensaje, parse_mode='Markdown', disable_web_page_preview=True)
            return

    estado = cargar_estado()
    if estado.get("apagado") and user_id not in ADMIN_IDS:
        await update.message.reply_text(f"⛔ Bot Apagado. Compra tu acceso V.I.P con {OWNER_PRINCIPAL}")
        return

    if not es_autorizado(user_id) and not estado.get("gratis"):
        await update.message.reply_text(f"⛔ Acceso denegado. Adquiere tu acceso con el owner 👑{OWNER_PRINCIPAL}")
        return

    await update.message.reply_text("👋 ¡Bienvenido! Presiona /qrnequiusa para comenzar.")

# --- QRnequiusa ---
async def qrnequiusa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user = update.effective_user
    estado = cargar_estado()

    logging.info(f"Comando /qrnequiusa recibido de usuario {user_id} (@{user.username}) en chat {chat_id}")

    # Registrar usuario que usa /qrnequiusa (independientemente de permisos)
    username = user.username or ""
    nombre = f"{user.first_name or ''} {user.last_name or ''}".strip()
    fecha_actual = str(update.message.date)
    
    registrados[user_id] = {
        "username": username or None,
        "nombre": nombre or "Sin nombre",
        "fecha": fecha_actual
    }
    guardar_registros(registrados)

    # Verificar membresía del grupo (excepto admins y si ya está en grupos permitidos)
    # Si el comando se usa en un grupo permitido o el grupo oficial, no verificar
    if user_id not in ADMIN_IDS and chat_type == "private":
        es_miembro = await verificar_miembro_grupo(context, user_id)
        if not es_miembro:
            mensaje = (
                "⛔ Debes unirte a nuestro grupo oficial para usar el bot:\n\n"
                "[👉 NEQUI USA](https://t.me/nequiusa)\n\n"
                "✅ Una vez que te unas, vuelve a intentarlo."
            )
            await update.message.reply_text(mensaje, parse_mode='Markdown', disable_web_page_preview=True)
            return

    if estado.get("apagado") and user_id not in ADMIN_IDS:
        await update.message.reply_text(f"⛔ Bot Apagado. Compra tu acceso V.I.P con {OWNER_PRINCIPAL}")
        return

    # Verificar estado del grupo si es un grupo
    if chat_type in ("group", "supergroup"):
        # Si el grupo está apagado (False o no existe en el diccionario)
        if not grupos_estado.get(chat_id, True):
            if user_id not in ADMIN_IDS:
                await update.message.reply_text(f"⛔ Bot apagado en este grupo.\n\n💎 Para acceso V.I.P contacta a {OWNER_PRINCIPAL}")
                return

    if chat_type == "private" and not es_autorizado(user_id) and not estado.get("gratis"):
        await update.message.reply_text(f"⛔ Acceso denegado. Adquiere tu acceso con el owner 👑{OWNER_PRINCIPAL}")
        return

    if chat_type in ("group", "supergroup"):
        if not (estado.get("gratis") or es_autorizado(user_id) or es_grupo_permitido(chat_id)):
            await update.message.reply_text("⛔ Este grupo no está autorizado para usar el bot QR.")
            return

    # Marcar usuario como activo para recibir fotos QR en este chat específico
    usuarios_qrnequiusa_activos[(user_id, chat_id)] = True
    await update.message.reply_text("📷 Envía una imagen con código QR de Nequi, Bancolombia, Davivienda o Daviplata.")

# --- EMV y QR logic (sin cambios) ---
def parse_emv(data: str) -> dict:
    i = 0
    result = {}
    while i < len(data):
        tag = data[i:i+2]
        i += 2
        if i >= len(data):
            break
        len_str = data[i:i+2]
        i += 2
        if i >= len(data):
            break
        try:
            length = int(len_str)
        except ValueError:
            logging.error(f"Invalid length in EMV data: {len_str}")
            break
        value = data[i:i+length]
        i += length
        result[tag] = value
    return result

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    estado = cargar_estado()

    # Solo procesar fotos si el usuario ha enviado /qrnequiusa primero en este chat específico
    if (user_id, chat_id) not in usuarios_qrnequiusa_activos or not usuarios_qrnequiusa_activos[(user_id, chat_id)]:
        return  # Quedarse callado, no hacer spam

    if estado.get("apagado") and user_id not in ADMIN_IDS:
        await update.message.reply_text(f"⛔ Bot Apagado. Compra tu acceso V.I.P con {OWNER_PRINCIPAL}")
        return

    # Verificar estado del grupo si es un grupo
    if chat_type in ("group", "supergroup"):
        if not grupos_estado.get(chat_id, True):
            if user_id not in ADMIN_IDS:
                await update.message.reply_text(f"⛔ Bot apagado en este grupo.\n\n💎 Para acceso V.I.P contacta a {OWNER_PRINCIPAL}")
                return

    if not (estado.get("gratis") or es_autorizado(user_id) or es_grupo_permitido(chat_id)):
        await update.message.reply_text(f"⛔ Acceso denegado. Adquiere tu acceso con el owner 👑{OWNER_PRINCIPAL}")
        return

    scanning_msg = await update.message.reply_text("📦 Escaneando la imagen...")
    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(BytesIO(photo_bytes))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        decoded_objects = decode(image)
        if not decoded_objects:
            # Borrar mensaje y enviar error
            try:
                await asyncio.sleep(1.5)  # Pausa para ver animación
                await scanning_msg.delete()
            except:
                pass
            await update.message.reply_text("❌ No se detectó código QR en la imagen.")
            return
        data = decoded_objects[0].data.decode('utf-8', errors='ignore')

        platform = 'Desconocida'
        number = 'N/A'
        name = 'N/A'
        location = 'Bogotá'
        dni = 'N/A'
        lower_data = data.lower()
        phone_regex = r'(?:(?:\+57|57)|0)?3[0-9]{9}\b'
        account_regex = r'\b\d{10,16}\b'
        dni_regex = r'\b\d{7,10}\b'
        if 'nequi' in lower_data:
            platform = 'Nequi'
        elif 'bancolombia' in lower_data:
            platform = 'Bancolombia'
            account_match = re.search(account_regex, data)
            if account_match:
                number = account_match.group(0)
        elif 'davivienda' in lower_data:
            platform = 'Davivienda'
            if 'negocio' in lower_data or 'business' in lower_data:
                number = 'N/A (QR de negocio)'
            else:
                account_match = re.search(account_regex, data)
                if account_match:
                    number = account_match.group(0)
        elif 'daviplata' in lower_data:
            platform = 'Daviplata'
            phone_match = re.search(phone_regex, data)
            if phone_match:
                number = phone_match.group(0)

        try:
            emv_data = parse_emv(data)
            if '59' in emv_data:
                name = emv_data['59']
            if '60' in emv_data and emv_data['60']:
                location = emv_data['60']
            if '62' in emv_data:
                sub_data = parse_emv(emv_data['62'])
                if '01' in sub_data and re.match(dni_regex, sub_data['01']):
                    dni = sub_data['01']
                if '02' in sub_data:
                    number = sub_data['02']
                for sub_tag in ['03', '04', '05']:
                    if sub_tag in sub_data and re.match(dni_regex, sub_data[sub_tag]):
                        dni = sub_data[sub_tag]
            for t in range(26, 52):
                ts = f'{t:02d}'
                if ts in emv_data:
                    sub_data = parse_emv(emv_data[ts])
                    if '00' in sub_data:
                        guid = sub_data['00'].lower()
                        if 'nequi' in guid:
                            platform = 'Nequi'
                        elif 'bancolombia' in guid:
                            platform = 'Bancolombia'
                        elif 'davivienda' in guid:
                            platform = 'Davivienda'
                        elif 'daviplata' in guid:
                            platform = 'Daviplata'
                    if '01' in sub_data:
                        number = sub_data['01']
                        if platform in ['Nequi', 'Daviplata'] and not re.match(phone_regex, number):
                            number = 'N/A'
                    for sub_tag in ['02', '03']:
                        if sub_tag in sub_data and platform in ['Nequi', 'Daviplata']:
                            if re.match(phone_regex, sub_data[sub_tag]):
                                number = sub_data[sub_tag]
                    for sub_tag in ['04', '05']:
                        if sub_tag in sub_data and re.match(dni_regex, sub_data[sub_tag]):
                            dni = sub_data[sub_tag]
        except Exception as e:
            logging.error(f"Error parsing EMV data: {e}")

        response = (
            f'🏦 **Plataforma**: {platform}\n'
            f'📱 **Número**: {number}\n'
            f'👤 **Nombre**: {name}\n'
            f'📍 **Ubicación**: {location}\n'
            f'🪪 **DNI**: {dni}'
        )
        # Borrar mensaje de "Escaneando..." con animación de Telegram
        try:
            await asyncio.sleep(1.5)  # Pausa para ver la animación de desaparición
            await scanning_msg.delete()
        except Exception as e:
            logging.warning(f"No se pudo borrar mensaje de escaneo: {e}")
        # Enviar información del QR como mensaje nuevo (este sí se queda)
        await update.message.reply_text(response, parse_mode='Markdown')
        # Desactivar después de procesar para que deba enviar /qrnequiusa de nuevo en este chat
        usuarios_qrnequiusa_activos[(user_id, chat_id)] = False
    except Exception as e:
        logging.error(f"Error en handle_photo: {e}")
        # Borrar mensaje con animación de Telegram
        try:
            await asyncio.sleep(1.5)  # Pausa para ver animación
            await scanning_msg.delete()
        except:
            pass
        await update.message.reply_text("❌ Error al procesar la imagen.")

# --- Main ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("qrnequiusa", qrnequiusa))
    application.add_handler(CommandHandler("help", help_admin))
    application.add_handler(CommandHandler("registros", registros))
    application.add_handler(CommandHandler("agregargrupo", agregargrupo))
    application.add_handler(CommandHandler("eliminargrupo", eliminargrupo))
    application.add_handler(CommandHandler("agregar", agregarusuario))
    application.add_handler(CommandHandler("eliminarusuario", eliminarusuario))
    application.add_handler(CommandHandler("on", on))
    application.add_handler(CommandHandler("off", off))
    application.add_handler(CommandHandler("ongrupo", ongrupo))
    application.add_handler(CommandHandler("offgrupo", offgrupo))
    application.add_handler(CommandHandler("gratis", gratis))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Bot iniciado")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()