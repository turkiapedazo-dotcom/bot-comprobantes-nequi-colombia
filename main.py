# -*- coding: utf-8 -*-
import asyncio
import random
import json
import logging
import os
import re
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
from io import BytesIO

# Cargar variables de entorno
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
from pyzbar.pyzbar import decode

from auth_system import AuthSystem
from config import (
    COMPROBANTE1_CONFIG,
    COMPROBANTE4_CONFIG,
    COMPROBANTE_MOVIMIENTO_CONFIG,
    COMPROBANTE_MOVIMIENTO2_CONFIG,
    COMPROBANTE_MOVIMIENTO3_CONFIG,
    COMPROBANTE_QR_CONFIG,
    COMPROBANTE_LLAVE,
    COMPROBANTE_NEQUI_BC_CONFIG,
    COMPROBANTE_BC_NQ_T_CONFIG,
    COMPROBANTE_NEQUI_AHORROS_CONFIG,
    COMPROBANTE_AHORROS_CONFIG,
    COMPROBANTE_AHORROS2_CONFIG,
    BANCOL_MOVIMIENTO_CONFIG,
    MOVIMIENTO_LLAVE_CONFIG,
    COMPROBANTE_ANULADO_CONFIG,
    MOVIMIENTO_AHORROS_CONFIG,
    MOVIMIENTO_QR_BC_CONFIG,
    COMPROBANTE_LLAVES_DAVIPLATA_CONFIG,
    COMPROBANTE_NQ_QR_NORMAL_CONFIG,
    MOVIMIENTO_NQ_QR_NORMAL_CONFIG,
    COMPROBANTE_QR_DAVIPLATA_CONFIG
)
from utils import generar_comprobante, ofuscar_nombre, generar_comprobante_nequi_bc, generar_comprobante_bc_nq_t, generar_comprobante_bc_qr, generar_comprobante_nequi_ahorros, generar_comprobante_ahorros, generar_comprobante_bc_nequi, generar_movimientos_bc_nequi, generar_comprobante_qr_bc, generar_comprobante_anulado, generar_movimiento_ahorros, generar_movimiento_qr_bc, generar_comprobante_llaves_daviplata, generar_comprobante_qr_daviplata

# Configuration
ADMIN_IDS = [8485045964]  # IDs de los administradores
ALLOWED_GROUP = -1003122616445  # ID del grupo permitido principal
ALLOWED_GROUPS_HARDCODED = [-1003349066708]  # Grupos siempre permitidos

# Función para verificar si un grupo está autorizado
def is_group_authorized(chat_id):
    """Verifica si un grupo está autorizado para usar el bot"""
    if chat_id > 0:  # Chat privado, siempre permitido
        return True
    
    # Verificar grupos autorizados
    authorized_groups = {ALLOWED_GROUP} | set(ALLOWED_GROUPS_HARDCODED)
    return chat_id in authorized_groups
OWNER = "@Axondevui"
GROUP_INVITE_LINK = "https://t.me/Nequicolombiafreee"  # Link del grupo oficial

# Archivos para persistencia de datos
USERS_FILE = "users.json"
GROUPS_FILE = "groups.json"
LOGS_FILE = "logs.json"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize authorization system
auth_system = AuthSystem(ADMIN_IDS, ALLOWED_GROUP)
# Agregar grupos hardcodeados a la lista de grupos permitidos
for group_id in ALLOWED_GROUPS_HARDCODED:
    auth_system.allowed_groups.add(group_id)
auth_system.save_data()  # Guardar para persistencia
user_data_store = {}
maintenance_mode = False  # Variable para modo mantenimiento
disabled_groups = set()  # Grupos donde el bot está deshabilitado con /off
# Anti-spam: guardar último mensaje por usuario/grupo
last_command_time = {}

# Cargar datos de usuarios, grupos y registros
def load_data():
    """Carga datos de usuarios, grupos y registros desde archivos JSON."""
    try:
        authorized_users = []
        authorized_groups = []
        logs = []
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(USERS_FILE) or '.', exist_ok=True)
        
        for file_path, key, default in [
            (USERS_FILE, 'users', []),
            (GROUPS_FILE, 'groups', []),
            (LOGS_FILE, 'logs', [])
        ]:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if not isinstance(data, dict) or key not in data:
                            logger.warning(f"Estructura JSON inválida en {file_path}. Usando valor por defecto.")
                            continue
                        if file_path == USERS_FILE:
                            authorized_users = data.get(key, default)
                        elif file_path == GROUPS_FILE:
                            authorized_groups = data.get(key, default)
                        elif file_path == LOGS_FILE:
                            logs = data.get(key, default)
                except json.JSONDecodeError:
                    logger.error(f"JSON corrupto en {file_path}. Usando valor por defecto.")
                except Exception as e:
                    logger.error(f"Error al leer {file_path}: {str(e)}")
        
        return authorized_users, authorized_groups, logs
    except Exception as e:
        logger.error(f"Error fatal al cargar datos: {str(e)}")
        return [], [], []

# Guardar datos de usuarios, grupos y registros
def save_data(authorized_users, authorized_groups, logs):
    """Guarda datos de usuarios, grupos y registros en archivos JSON."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(USERS_FILE) or '.', exist_ok=True)
        
        for file_path, data in [
            (USERS_FILE, {'users': authorized_users}),
            (GROUPS_FILE, {'groups': authorized_groups}),
            (LOGS_FILE, {'logs': logs})
        ]:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error al escribir en {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error fatal al guardar datos: {str(e)}")

# Cargar datos iniciales
authorized_users, authorized_groups, logs = load_data()

# Actualizar auth_system con usuarios y grupos cargados
for user_id in authorized_users:
    auth_system.add_user(user_id)
for group_id in authorized_groups:
    auth_system.add_group(group_id)

# ------------------------------------------------------------------
# FUNCIONES PARA LEER QR
# ------------------------------------------------------------------
def parse_emv(data: str) -> dict:
    """Parsea datos EMV del QR"""
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
            logger.error(f"Invalid length in EMV data: {len_str}")
            break
        value = data[i:i+length]
        i += length
        result[tag] = value
    return result

async def leer_qr_nequi(photo_bytes: bytes) -> dict:
    """Lee un QR de Nequi y extrae la información"""
    try:
        image = Image.open(BytesIO(photo_bytes))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        decoded_objects = decode(image)
        if not decoded_objects:
            return {"error": "No se detectó código QR en la imagen"}
        
        data = decoded_objects[0].data.decode('utf-8', errors='ignore')
        
        # Extraer información del QR
        platform = 'Desconocida'
        name = 'N/A'
        lower_data = data.lower()
        
        # Detectar plataforma
        if 'nequi' in lower_data:
            platform = 'Nequi'
        elif 'bancolombia' in lower_data:
            platform = 'Bancolombia'
        elif 'davivienda' in lower_data:
            platform = 'Davivienda'
        elif 'daviplata' in lower_data:
            platform = 'Daviplata'
        
        # Parsear EMV para obtener el nombre
        try:
            emv_data = parse_emv(data)
            if '59' in emv_data:
                name = emv_data['59']
            
            # Buscar en tags adicionales
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
        except Exception as e:
            logger.error(f"Error parsing EMV data: {e}")
        
        return {
            "platform": platform,
            "name": name,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error al leer QR: {str(e)}")
        return {"error": f"Error al procesar la imagen: {str(e)}"}

# ------------------------------------------------------------------
# COMANDOS
# ------------------------------------------------------------------
async def nequicol_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando que muestra botones de acceso rápido - Verifica autorización del grupo"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_name = update.effective_user.first_name or update.effective_user.username or "Usuario"
    
    try:
        # VERIFICACIÓN ESTRICTA: Solo grupos autorizados
        if not is_group_authorized(chat_id):
            await update.message.reply_text(
                "🚫 Este bot no está autorizado en este grupo.\n\n"
                f"👑 Contacta al owner: {OWNER}\n"
                f"📱 Grupo oficial: {GROUP_INVITE_LINK}",
                disable_web_page_preview=True
            )
            return
        
        # Verificar si el bot está deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot está deshabilitado en este grupo
        # Anti-spam: cooldown de 3 segundos por usuario
        import time
        current_time = time.time()
        key = f"nequicol_{chat_id}_{user_id}"
        
        if key in last_command_time:
            if current_time - last_command_time[key] < 3:
                return  # Ignorar si fue hace menos de 3 segundos
        
        last_command_time[key] = current_time
        
        # Si es un grupo, permitir siempre (la restricción es solo para privado)
        is_group = chat_type in ['group', 'supergroup']
        
        # Verificar acceso: en grupos siempre permitido, en privado verificar autorización
        if not is_group:
            # Solo verificar en privado
            if not auth_system.can_use_bot(user_id, chat_id, True):
                if not auth_system.gratis_mode:
                    await update.message.reply_text(
                        "👑 Este bot está restringido en el privado para evitar estafas.\n\n"
                        "Si deseas usarlo gratuitamente sin pagar nada, mándale un mensaje al OWNER 👑 @Axondevui\n\n"
                        "👉 <a href='https://t.me/Nequicolofficiall'>Grupo Oficial</a>",
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                return
        
        # Todos los comprobantes disponibles en grupos y privado
        keyboard = [
            [
                InlineKeyboardButton("💰 Nequi", callback_data="comprobante1"),
                InlineKeyboardButton("🔄 BRE-B", callback_data="comprobante4")
            ],
            [
                InlineKeyboardButton("📱 QR Comprobante", callback_data="comprobante_qr"),
                InlineKeyboardButton("🔑 LLAVES", callback_data="comprobante_llave")
            ],
            [
                InlineKeyboardButton("🏦 Nequi a Bancolombia", callback_data="bancolombia")
            ],
            [
                InlineKeyboardButton("🏦 QR BC", callback_data="qr_bc"),
                InlineKeyboardButton("💳 BC a Nequi", callback_data="bc_nequi")
            ],
            [
                InlineKeyboardButton("🏛️ BC a BC", callback_data="bc_bc"),
                InlineKeyboardButton("🔵 DaviPlata", callback_data="daviplata")
            ],
            [
                InlineKeyboardButton("📱 QR DaviPlata", callback_data="qr_daviplata"),
                InlineKeyboardButton("💳 Llaves DaviPlata", callback_data="llaves_daviplata")
            ],
            [
                InlineKeyboardButton("📲 NQ QR NORMAL", callback_data="nq_qr_normal")
            ],
            [
                InlineKeyboardButton("✅ Anulado", callback_data="comprobante_anulado")
            ]
        ]
        mensaje_comandos = (
            f"👋 Hola {user_name}!\n\n"
            f"💎 Generador de Comprobantes\n"
            f"📌 Selecciona una opción:\n\n"
            f"ℹ️ Para conocer funciones de fechas y referencias manuales, pulsa /masinf"
        )
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            mensaje_comandos,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error en nequicol_command: {str(e)}")

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cuando el bot es agregado a un grupo"""
    try:
        chat_id = update.effective_chat.id
        
        # VERIFICACIÓN ESTRICTA: Solo grupos autorizados
        if not is_group_authorized(chat_id):
            await update.message.reply_text(
                "🚫 Este bot no está autorizado en este grupo.\n\n"
                f"👑 Para usar el bot, contacta al owner: {OWNER}\n"
                f"� Grupo oficcial: {GROUP_INVITE_LINK}",
                disable_web_page_preview=True
            )
            # Salir del grupo no autorizado
            try:
                await update.get_bot().leave_chat(chat_id)
            except:
                pass
            return
        
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                # El bot fue agregado al grupo
                user_name = update.effective_user.first_name or update.effective_user.username or "Usuario"
                await update.message.reply_text(
                    f"🎉 Hola {user_name}!\n\n"
                    f"Para iniciar el bot presiona /Nequicol\n\n"
                    f"💎 Servicio gratuito de alta calidad"
                )
    except Exception as e:
        logger.error(f"Error en new_chat_member: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    
    try:
        # VERIFICACIÓN ESTRICTA: Solo grupos autorizados
        if not is_group_authorized(chat_id):
            if chat_type in ['group', 'supergroup']:
                await update.message.reply_text(
                    "🚫 Este bot no está autorizado en este grupo.\n\n"
                    f"👑 Contacta al owner: {OWNER}\n"
                    f"📱 Grupo oficial: {GROUP_INVITE_LINK}",
                    disable_web_page_preview=True
                )
            return
        
        # Verificar si el bot está deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot está deshabilitado en este grupo

    

        
        
        # En grupos: anti-spam con cooldown de 2 segundos
        if chat_type in ['group', 'supergroup']:
            import time
            current_time = time.time()
            key = f"start_{chat_id}_{user_id}"
            
            if key in last_command_time:
                if current_time - last_command_time[key] < 2:
                    return  # Ignorar si fue hace menos de 2 segundos
            
            last_command_time[key] = current_time
            user_name = first_name or username or "Usuario"
            await update.message.reply_text(f"👋 Hola {user_name}!\n\nPresiona /Nequicol para iniciar")
            return
        
        # En privado: mostrar bienvenida personalizada
        user_display_name = first_name or username or "Usuario"
        username_display = f"@{username}" if username else "Sin username"
        first_name_display = first_name or 'No disponible'
        
        # Verificar autorización
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            await update.message.reply_text("⚠️ Bot en mantenimiento.")
            return
        
        # Usuario autorizado (ya verificó membresía), mostrar mensaje de bienvenida
        mensaje_bienvenida = (
            f"👋 ¡Bienvenido {user_display_name}!\n\n"
            f"📋 Información de tu cuenta:\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Nombre: {first_name_display}\n"
            f"📱 Username: {username_display}\n\n"
            f"💎 Para usar el bot, escribe /nequicol\n\n"
            f"ℹ️ Para conocer funciones de fechas y referencias manuales, pulsa /masinf"
        )
        await update.message.reply_text(mensaje_bienvenida)
    except Exception as e:
        logger.error(f"Error en comando start: {str(e)}")
        # No enviar mensaje de error en grupos para evitar spam
        if chat_type == 'private':
            await update.message.reply_text("⚠️ Error. Intenta /start de nuevo.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Verificar si el bot está deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot está deshabilitado en este grupo
        
        if user_id in user_data_store:
            del user_data_store[user_id]
            await update.message.reply_text(
                "✅ Operación cancelada correctamente.\n\n"
                "Presiona /nequicol para generar un nuevo comprobante.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "❌ No hay ninguna operación activa para cancelar.\n\n"
                "Presiona /nequicol para generar un comprobante.",
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        logger.error(f"Error en cancelar: {str(e)}")

# ------------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Error al responder callback query: {str(e)}")
        # Continuar aunque falle el answer
    
    try:
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        chat_type = query.message.chat.type
        username = query.from_user.username
        first_name = query.from_user.first_name
        
        # VERIFICACIÓN ESTRICTA: Solo grupos autorizados
        if not is_group_authorized(chat_id):
            await query.message.reply_text(
                "🚫 Este bot no está autorizado en este grupo.\n\n"
                f"👑 Contacta al owner: {OWNER}\n"
                f"📱 Grupo oficial: {GROUP_INVITE_LINK}",
                disable_web_page_preview=True
            )
            return
        
        # Verificar si el bot está deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot está deshabilitado en este grupo
        
        # Actualizar información de admins
        if user_id in ADMIN_IDS:
            context.bot_data.setdefault('admin_info', {})
            context.bot_data['admin_info'][user_id] = {
                'username': username or 'N/A',
                'first_name': first_name or 'N/A'
            }
        
        # Si es un grupo, permitir siempre (la restricción es solo para privado)
        is_group = chat_type in ['group', 'supergroup']
        
        # Verificar acceso: en grupos siempre permitido, en privado verificar autorización
        if not is_group:
            # Solo verificar en privado
            if not auth_system.can_use_bot(user_id, chat_id, True):
                if not auth_system.gratis_mode:
                    await query.message.reply_text(
                        "👑 Este bot está restringido en el privado para evitar estafas.\n\n"
                        "Si deseas usarlo gratuitamente sin pagar nada, mándale un mensaje al OWNER 👑 @Axondevui\n\n"
                        "👉 <a href='https://t.me/Nequicolofficiall'>Grupo Oficial</a>",
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                return
        
        # Verificar modo mantenimiento
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            admin_list = "\n".join(f"• {uid} (@{info['username']})"
                                   for uid, info in context.bot_data.get('admin_info', {}).items())
            await query.message.reply_text(
                f"⚠️ El bot está en mantenimiento. Contacta a los administradores: {OWNER}",
                parse_mode='Markdown'
            )
            return
        tipo = query.data or "default"
        
        # Preservar flags de configuración (fecha_manual, referencia_manual) si existen
        fecha_manual_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
        referencia_manual_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
        
        # Para QR BC, auto-rellenar el punto de venta con "QR" y empezar en step 1
        if tipo == "qr_bc":
            user_data_store[user_id] = {
                "step": 1,  # Empezar en step 1 (pedir a quién envías)
                "tipo": tipo, 
                "session_id": str(uuid4()),
                "fecha_manual": fecha_manual_flag,
                "referencia_manual": referencia_manual_flag,
                "punto_venta": "QR"  # Auto-rellenar con "QR"
            }
        else:
            user_data_store[user_id] = {
                "step": 0, 
                "tipo": tipo, 
                "session_id": str(uuid4()),
                "fecha_manual": fecha_manual_flag,
                "referencia_manual": referencia_manual_flag
            }
        
        # Registrar uso
        logs.append({
            'user_id': user_id,
            'username': username or 'N/A',
            'first_name': first_name or 'N/A',
            'command': f'button_{tipo}',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(authorized_users, authorized_groups, logs)
        
        prompts = {
            "comprobante1": "👤 Ingresa el nombre del destinatario:",
            "comprobante4": "👤 Ingresa el nombre a enviar:",
            "comprobante_qr": "🏬 Ingresa el nombre del negocio:",
            "comprobante_llave": "👤 Ingresa el nombre a enviar:",
            "bancolombia": "👤 Ingresa el nombre del destinario:",
            "qr_bc": "👤 Ingresa a quién envías:",
            "bc_nequi": "📱 Ingresa el número Nequi (10 dígitos):",
            "bc_bc": "👤 Ingresa el nombre:",
            "daviplata": "📱 Ingresa el número DaviPlata (mínimo 10 dígitos):",
            "llaves_daviplata": "👤 Ingresa el nombre del destinatario:",
            "nq_qr_normal": "📷 Envía la foto del QR a generar:",
            "qr_daviplata": "🏬 Ingresa el nombre del negocio (Compra en):",
            "comprobante_anulado": "👤 ¿Nombre de la víctima?"
        }
        
        await query.message.reply_text(
            prompts.get(tipo, "🔍 Por favor, inicia ingresando los datos requeridos:"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en button_handler: {str(e)}")
        await query.message.reply_text("⚠️ Error al procesar la selección. Intenta de nuevo.", parse_mode='Markdown')

# ------------------------------------------------------------------
# MENSAJES
# ------------------------------------------------------------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja fotos enviadas por el usuario (para QR Normal)"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Solo procesar si el usuario está en una sesión activa
        if user_id not in user_data_store:
            return
        
        data = user_data_store[user_id]
        tipo = data.get("tipo")
        step = data.get("step", 0)
        
        # Solo procesar fotos para nq_qr_normal en step 0
        if tipo != "nq_qr_normal" or step != 0:
            return
        
        # Mostrar mensaje de escaneo
        scanning_msg = await update.message.reply_text("📦 Escaneando el QR...")
        
        try:
            # Descargar la foto
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            
            # Leer el QR
            qr_info = await leer_qr_nequi(bytes(photo_bytes))
            
            # Borrar mensaje de escaneo
            await asyncio.sleep(1)
            await scanning_msg.delete()
            
            if "error" in qr_info:
                await update.message.reply_text(f"❌ {qr_info['error']}\n\nIntenta con otra imagen.")
                return
            
            # Guardar el nombre extraído del QR
            nombre_qr = qr_info.get("name", "N/A")
            if nombre_qr == "N/A":
                await update.message.reply_text("❌ No se pudo extraer el nombre del QR.\n\nIntenta con otra imagen.")
                return
            
            # Guardar datos y avanzar al siguiente paso
            data["nombre"] = nombre_qr
            data["step"] = 1
            
            await update.message.reply_text(
                f"✅ QR escaneado correctamente\n\n"
                f"👤 Nombre: {nombre_qr}\n\n"
                f"💰 Ahora ingresa el valor:"
            )
            
        except Exception as e:
            logger.error(f"Error procesando foto QR: {str(e)}")
            await scanning_msg.delete()
            await update.message.reply_text("❌ Error al procesar la imagen. Intenta de nuevo.")
            
    except Exception as e:
        logger.error(f"Error en handle_photo: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    text = update.message.text.strip()
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        # VERIFICACIÓN ESTRICTA: Solo grupos autorizados
        if not is_group_authorized(chat_id):
            # En grupos no autorizados, solo responder si es admin
            if user_id not in ADMIN_IDS:
                return  # Ignorar completamente
            else:
                await update.message.reply_text(
                    "🚫 Este bot no está autorizado en este grupo.\n\n"
                    f"👑 Contacta al owner: {OWNER}\n"
                    f"📱 Grupo oficial: {GROUP_INVITE_LINK}",
                    disable_web_page_preview=True
                )
                return
        
        # Verificar si el bot está deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot está deshabilitado en este grupo
        
        # Detectar si el usuario presionó "❌ Cancelar"
        if text == "❌ Cancelar":
            if user_id in user_data_store:
                del user_data_store[user_id]
                await update.message.reply_text(
                    "✅ Operación cancelada correctamente.\n\n"
                    "Presiona /Nequicol para generar un nuevo comprobante.",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    "❌ No hay ninguna operación activa para cancelar.\n\n"
                    "Presiona /Nequicol para generar un comprobante.",
                    reply_markup=ReplyKeyboardRemove()
                )
            return
        
        # Si es un grupo, permitir siempre (la restricción es solo para privado)
        is_group = chat_type in ['group', 'supergroup']
        
        # Verificar acceso: en grupos siempre permitido, en privado verificar autorización
        if not is_group:
            # Solo verificar en privado
            if not auth_system.can_use_bot(user_id, chat_id, True):
                if not auth_system.gratis_mode:
                    await update.message.reply_text(
                        "👑 Este bot está restringido en el privado para evitar estafas.\n\n"
                        "Si deseas usarlo gratuitamente sin pagar nada, mándale un mensaje al OWNER 👑 @Axondevui\n\n"
                        "👉 <a href='https://t.me/Nequicolofficiall'>Grupo Oficial</a>",
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                return
        
        # En grupos: solo responder si el usuario tiene una sesión activa
        if chat_type in ['group', 'supergroup']:
            if user_id not in user_data_store:
                return  # Ignorar mensajes aleatorios en grupos
        
        # En privado: también verificar sesión activa
        if chat_type == 'private':
            if user_id not in user_data_store:
                return  # No responde si el usuario no está en una sesión activa
        
        # Actualizar información de admins
        if user_id in ADMIN_IDS:
            context.bot_data.setdefault('admin_info', {})
            context.bot_data['admin_info'][user_id] = {
                'username': username or 'N/A',
                'first_name': first_name or 'N/A'
            }
        # Verificar modo mantenimiento
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            admin_list = "\n".join(f"• {uid} (@{info['username']})"
                                   for uid, info in context.bot_data.get('admin_info', {}).items())
            await update.message.reply_text(
                f"⚠️ El bot está en mantenimiento. Contacta a los administradores:\n{admin_list}",
                parse_mode='Markdown'
            )
            return
        
        # Registrar uso
        logs.append({
            'user_id': user_id,
            'username': username or 'N/A',
            'first_name': first_name or 'N/A',
            'command': 'message',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_data(authorized_users, authorized_groups, logs)
        data = user_data_store[user_id]
        tipo = data["tipo"]
        step = data["step"]
        
        # Verificar si necesita pedir fecha manual (para TODOS los comprobantes)
        fecha_manual = data.get("fecha_manual", False)
        # Referencia manual solo para Nequi y Nequi a Bancolombia
        referencia_manual = data.get("referencia_manual", False) if tipo in ["comprobante1", "bancolombia"] else False
        
        # Función auxiliar para limpiar sesión preservando flags de configuración
        def limpiar_sesion_preservando_flags():
            """Elimina la sesión pero preserva los flags de configuración del usuario"""
            fecha_flag = data.get("fecha_manual", False)
            referencia_flag = data.get("referencia_manual", False)
            del user_data_store[user_id]
            # Restaurar solo los flags de configuración si existen
            if fecha_flag or referencia_flag:
                user_data_store[user_id] = {}
                if fecha_flag:
                    user_data_store[user_id]["fecha_manual"] = True
                if referencia_flag:
                    user_data_store[user_id]["referencia_manual"] = True
        
        # Función auxiliar para verificar y pedir fecha antes de generar (para TODOS)
        async def verificar_fecha_manual():
            """Verifica si necesita pedir fecha manual y la solicita"""
            if fecha_manual and "fecha_manual_value" not in data:
                data["esperando_fecha"] = True
                await update.message.reply_text(
                    "📅 Fecha Manual\n\n"
                    "📝 Ingresa la fecha:\n"
                    "Ejemplo: 06 de diciembre de 2025 a las 12:00 a.m."
                )
                return True
            return False
        
        # Función auxiliar para verificar y pedir referencia (solo Nequi)
        async def verificar_referencia_manual():
            """Verifica si necesita pedir referencia manual y la solicita (solo Nequi)"""
            if referencia_manual and "referencia_manual_value" not in data:
                data["esperando_referencia"] = True
                await update.message.reply_text(
                    "🔢 Referencia Manual\n\n"
                    "Ingresa solo los 8 dígitos de la referencia.\n"
                    "La M se colocará automáticamente.\n\n"
                    "Ejemplo: 12345678\n\n"
                    "La referencia se formateará como: M12345678"
                )
                return True
            return False
        
        # Si está esperando fecha, procesarla primero (ANTES de cualquier paso del comprobante)
        if data.get("esperando_fecha", False):
            data["fecha_manual_value"] = text
            data["esperando_fecha"] = False
            # Continuar con referencia si está activada (solo Nequi)
            if await verificar_referencia_manual():
                return
            # Si no hay referencia manual, continuar con la generación del comprobante
            # Marcar que la fecha fue recibida para continuar con la generación
            data["fecha_recibida"] = True
            # Continuar con el flujo normal del comprobante (no retornar)
        
        # Si está esperando referencia (solo Nequi), procesarla primero
        if data.get("esperando_referencia", False):
            # Validar que sean exactamente 8 dígitos
            if not text.isdigit() or len(text) != 8:
                await update.message.reply_text(
                    "⚠️ La referencia debe tener exactamente 8 dígitos.\n"
                    "Ejemplo: 12345678"
                )
                return
            data["referencia_manual_value"] = f"M{text}"
            data["esperando_referencia"] = False
            # Marcar que la referencia fue recibida para continuar con la generación
            data["fecha_recibida"] = True
            # Continuar con el flujo normal del comprobante (no retornar)
        
        async def send_document(output_path: str, caption: str) -> bool:
            # Asegurar que el archivo exista antes de enviarlo
            try:
                if output_path is None or not os.path.exists(output_path):
                    logger.error(f"Documento no encontrado o None: {output_path}")
                    await update.message.reply_text(
                        "⚠️ Error: No se pudo generar el comprobante.",
                        parse_mode='Markdown'
                    )
                    return False
                
                # Verificar tamaño del archivo (Telegram límite: 50MB, pero archivos grandes pueden fallar)
                file_size = os.path.getsize(output_path)
                file_size_mb = file_size / (1024 * 1024)
                logger.info(f"Enviando documento: {output_path}, Tamaño: {file_size_mb:.2f} MB")
                
                if file_size > 50 * 1024 * 1024:  # 50MB
                    logger.error(f"Archivo demasiado grande: {file_size_mb:.2f} MB")
                    await update.message.reply_text(
                        f"⚠️ Error: El archivo generado es demasiado grande ({file_size_mb:.2f} MB). Límite: 50 MB.",
                        parse_mode='Markdown'
                    )
                    os.remove(output_path)
                    return False
                
                with open(output_path, "rb") as f:
                    await update.message.reply_document(document=f, caption=caption)
                os.remove(output_path)
                logger.info(f"Documento enviado exitosamente: {output_path}")
                return True
            except Exception as e:
                import traceback
                logger.error(f"Error al enviar documento: {str(e)}")
                logger.error(traceback.format_exc())
                # Intentar eliminar el archivo si existe
                try:
                    if output_path and os.path.exists(output_path):
                        os.remove(output_path)
                except:
                    pass
                await update.message.reply_text(
                    f"⚠️ Error al enviar el comprobante.\n\nDetalle: {str(e)}",
                    parse_mode='Markdown'
                )
                return False
        
        async def generar_qr_daviplata_final(update, data, fecha_manual, send_document, limpiar_sesion_preservando_flags):
            """Función auxiliar para generar el comprobante QR DaviPlata"""
            # Si tiene fecha manual, usarla
            if fecha_manual and "fecha_manual_value" in data:
                data["fecha"] = data["fecha_manual_value"]
            # Limpiar flag de fecha_recibida
            data.pop("fecha_recibida", None)
            
            try:
                output_path = generar_comprobante_qr_daviplata(data, COMPROBANTE_QR_DAVIPLATA_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante QR DaviPlata.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Enviar como documento
                await send_document(output_path, "✅ Comprobante QR DaviPlata generado")
            except Exception as e:
                logger.error(f"Error generando QR DaviPlata: {str(e)}")
                await update.message.reply_text("⚠️ Error al generar el comprobante QR DaviPlata.")
            limpiar_sesion_preservando_flags()
        
        # --- NEQUI ---
        if tipo == "comprobante1":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "📱 Ingresa el número de teléfono (solo dígitos):",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.isdigit():
                    await update.message.reply_text(
                        "⚠️ El número debe contener solo dígitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["telefono"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "💰 Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 2 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "⚠️ El valor debe ser numérico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                    # Verificar referencia manual (solo Nequi)
                    if await verificar_referencia_manual():
                        return
                # Verificar que el valor esté guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró el valor. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Si tiene referencia manual, usarla (solo Nequi)
                if referencia_manual and "referencia_manual_value" in data:
                    data["referencia"] = data["referencia_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                output_path = generar_comprobante(data, COMPROBANTE1_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante Nequi.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                               # Enviar comprobante como foto (no como documento)
                try:
                    with open(output_path, "rb") as f:
                        await update.message.reply_photo(photo=f, caption="✅ Comprobante Nequi generado")
                    os.remove(output_path)
                    comprobante_enviado = True
                except Exception as e:
                    logger.error(f"Error al enviar comprobante Nequi como foto: {e}")
                    await update.message.reply_text("⚠️ Error al enviar el comprobante.")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    comprobante_enviado = False

                if comprobante_enviado:
                    # Movimiento negativo
                    data_mov = data.copy()
                    data_mov["nombre"] = data["nombre"].upper()
                    data_mov["valor"] = -abs(data["valor"])
                    output_path_mov = generar_comprobante(data_mov, COMPROBANTE_MOVIMIENTO_CONFIG)
                    if output_path_mov is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento Nequi.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov, "📄 Movimiento generado")
                limpiar_sesion_preservando_flags()
        # --- BRE-B ---
        elif tipo == "comprobante4":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "🔑 Ingresa la llave (debe iniciar con @):",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.startswith("@"):
                    await update.message.reply_text(
                        "⚠️ La llave debe iniciar con @. Ejemplo: @miusuario",
                        parse_mode='Markdown'
                    )
                    return
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "🏦 Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )
            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "📱 Ingresa el número de envío:",
                    parse_mode='Markdown'
                )
            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "⚠️ El número debe contener solo dígitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "💰 Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "⚠️ El valor debe ser numérico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor esté guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró el valor. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                output_path = generar_comprobante(data, COMPROBANTE4_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante BRE-B.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "✅ Comprobante BRE-B generado"):
                    # Movimiento negativo BRE-B (la ofuscación se aplica en utils.py)
                    data_mov2 = {
                        "nombre": data["nombre"],
                        "valor": -abs(data["valor"])
                    }
                    output_path_mov2 = generar_comprobante(data_mov2, COMPROBANTE_MOVIMIENTO2_CONFIG)
                    if output_path_mov2 is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento BRE-B.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov2, "📄 Movimiento BRE-B generado")
                limpiar_sesion_preservando_flags()
        # --- QR COMPROBANTE ---
        elif tipo == "comprobante_qr":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "🔑 Ingresa la llave banco a destino:",
                    parse_mode='Markdown'
                )
            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "🏦 Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )
            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "📱 Ingresa el número de envío:",
                    parse_mode='Markdown'
                )
            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "⚠️ El número debe contener solo dígitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "💰 Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "⚠️ El valor debe ser numérico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor esté guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró el valor. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                output_path = generar_comprobante(data, COMPROBANTE_QR_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante QR.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "✅ Comprobante QR generado"):
                    # Movimiento adicional
                    data_mov_qr = {
                        "nombre": data["nombre"].upper(),
                        "valor": -abs(data["valor"])
                    }
                    output_path_movqr = generar_comprobante(data_mov_qr, COMPROBANTE_MOVIMIENTO3_CONFIG)
                    if output_path_movqr is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento QR.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_movqr, "📄 Movimiento QR generado")
                limpiar_sesion_preservando_flags()
                      # --- LLAVES ---
        elif tipo == "comprobante_llave":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "🔑 Ingresa la llave:",
                    parse_mode='Markdown'
                )

            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "🏦 Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )

            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "📱 Ingresa el número de envío:",
                    parse_mode='Markdown'
                )

            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "⚠️ El número debe contener solo dígitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "💰 Ingresa el valor:",
                    parse_mode='Markdown'
                )

            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "⚠️ El valor debe ser numérico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor esté guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró el valor. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)

                # --- Generar comprobante Llave ---
                output_path = generar_comprobante(data, COMPROBANTE_LLAVE)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante Llave.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return

                if await send_document(output_path, "✅ Comprobante Llave generado"):
                    # --- Generar también el movimiento negativo de Llaves ---
                    data_mov_llave = {
                        "nombre": data["nombre"].upper(),
                        "valor": -abs(data["valor"])
                    }
                    output_path_mov_llave = generar_comprobante(data_mov_llave, MOVIMIENTO_LLAVE_CONFIG)
                    if output_path_mov_llave is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento de Llaves.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov_llave, "📄 Movimiento Llaves generado")
                # limpiar sesión
                limpiar_sesion_preservando_flags()


                
        # --- BANCOLOMBIA ---
        elif tipo == "bancolombia":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "💰 Ingresa la cantidad a enviar:",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text(
                        "⚠️ La cantidad debe ser numérica.",
                        parse_mode='Markdown'
                    )
                    return
                data["valor"] = int(text)
                data["step"] = 2
                await update.message.reply_text(
                    "🏦 Ingresa el número de cuenta:",
                    parse_mode='Markdown'
                )
            elif step == 2 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, la cuenta ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.isdigit() or len(text) < 11:
                        await update.message.reply_text(
                            "⚠️ El número de cuenta debe ser **11 dígitos**.",
                            parse_mode='Markdown'
                        )
                        return
                    data["cuenta"] = text
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                    # Verificar referencia manual (solo Nequi a Bancolombia)
                    if await verificar_referencia_manual():
                        return
                # Verificar que la cuenta esté guardada antes de continuar
                if "cuenta" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró la cuenta. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla; si no, dejar que generar_comprobante la genere automáticamente
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Si no hay fecha manual, no establecer data["fecha"] para que generar_comprobante la genere automáticamente
                # Si tiene referencia manual, usarla; si no, generar automática con 8 dígitos
                if referencia_manual and "referencia_manual_value" in data:
                    data["referencia"] = data["referencia_manual_value"]
                else:
                    data["referencia"] = f"M{random.randint(10000000, 99999999)}"
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                # No necesitamos numero_cuenta, usamos "cuenta" directamente
                output_path = generar_comprobante_nequi_bc(data, COMPROBANTE_NEQUI_BC_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante Bancolombia.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "✅ Comprobante Bancolombia generado"):
                    # Movimiento negativo
                    data_mov_bancol = data.copy()
                    data_mov_bancol["nombre"] = data["nombre"].upper()
                    data_mov_bancol["valor"] = -abs(data["valor"])
                    output_path_mov_bancol = generar_comprobante(data_mov_bancol, BANCOL_MOVIMIENTO_CONFIG)
                    if output_path_mov_bancol is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento Bancolombia.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov_bancol, "📄 Movimiento Bancolombia generado")
                limpiar_sesion_preservando_flags()
        
        # --- QR BC (Bancolombia QR) - Configuración original ---
        elif tipo == "qr_bc":
            from utils import generar_comprobante_qr_bc
            if step == 0:
                punto_venta_limpio = text.replace('\n', ' ').replace('\r', ' ').strip()
                while '  ' in punto_venta_limpio:
                    punto_venta_limpio = punto_venta_limpio.replace('  ', ' ')
                data["punto_venta"] = punto_venta_limpio
                data["step"] = 1
                await update.message.reply_text("👤 Ingresa a quién envías:")
            elif step == 1:
                enviado_a_limpio = text.replace('\n', ' ').replace('\r', ' ').strip()
                while '  ' in enviado_a_limpio:
                    enviado_a_limpio = enviado_a_limpio.replace('  ', ' ')
                data["enviado_a"] = enviado_a_limpio
                data["step"] = 2
                await update.message.reply_text("💰 Ingresa la cantidad:")
            elif step == 2:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("⚠️ La cantidad debe ser numérica.")
                    return
                data["cantidad"] = int(text)
                data["step"] = 3
                await update.message.reply_text("🔢 Ingresa los últimos 4 dígitos de la cuenta:")
            elif step == 3:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("⚠️ Deben ser exactamente 4 dígitos.")
                    return
                data["ultimos_4"] = text
                try:
                    output_path = generar_comprobante_qr_bc(
                        data["punto_venta"],
                        data["enviado_a"],
                        data["cantidad"],
                        data["ultimos_4"]
                    )
                    if output_path and await send_document(output_path, "✅ Comprobante QR BC generado"):
                        # Generar movimiento QR BC usando qr.jpg
                        try:
                            data_mov_qr_bc = {
                                "valor": -abs(data["cantidad"])
                            }
                            output_path_mov_qr_bc = generar_movimiento_qr_bc(data_mov_qr_bc, MOVIMIENTO_QR_BC_CONFIG)
                            if output_path_mov_qr_bc:
                                await send_document(output_path_mov_qr_bc, "📄 Movimiento QR BC generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento QR BC: {str(e_mov)}")
                    else:
                        await update.message.reply_text("⚠️ Error al generar el comprobante QR BC.")
                except Exception as e:
                    logger.error(f"Error generando QR BC: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante QR BC.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- BC a Nequi (configuración original) ---
        elif tipo == "bc_nequi":
            from utils import generar_comprobante_bc_nequi, generar_movimientos_bc_nequi
            if step == 0:
                if not text.isdigit() or len(text) != 10:
                    await update.message.reply_text("⚠️ El número debe tener exactamente 10 dígitos.")
                    return
                data["numero"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                data["valor"] = text
                # Generar directamente sin pedir nombre (configuración original)
                try:
                    output_path = generar_comprobante_bc_nequi(
                        data["numero"],
                        data["valor"],
                        ""  # Sin nombre
                    )
                    if output_path:
                        await send_document(output_path, "✅ Comprobante BC a Nequi generado")
                        # Generar movimiento siempre
                        try:
                            cuenta_ahorros = f"Ahorros *{data['numero'][-4:]}"
                            output_mov = generar_movimientos_bc_nequi(cuenta_ahorros, data["valor"])
                            if output_mov:
                                await send_document(output_mov, "📄 Movimiento BC a Nequi generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento BC a Nequi: {str(e_mov)}")
                    else:
                        await update.message.reply_text("⚠️ Error al generar el comprobante BC a Nequi.")
                except Exception as e:
                    logger.error(f"Error generando BC a Nequi: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante BC a Nequi.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- BC a BC (Bancolombia a Bancolombia) - Usa configuración de Ahorros (bc_a_bc.png) ---
        elif tipo == "bc_bc":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("🏦 Ingresa el número de cuenta:")
            elif step == 1:
                # Validar que tenga 11 dígitos
                digitos = "".join(ch for ch in text if ch.isdigit())
                if len(digitos) != 11:
                    await update.message.reply_text("⚠️ El número de cuenta debe tener exactamente 11 dígitos.\nEjemplo: 12345678912")
                    return
                data["numero_cuenta"] = digitos
                data["step"] = 2
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 2:
                valor_limpio = text.replace(".", "").replace(",", "").replace(" ", "")
                if not valor_limpio.isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                valor = int(valor_limpio)
                if valor < 1000:
                    await update.message.reply_text("⚠️ El valor mínimo es $1,000. Intenta de nuevo.")
                    return
                data["valor"] = valor
                data["step"] = 3
                await update.message.reply_text("💸 ¿Deseas colocar costo de transferencia?\n\nResponde: sí o no")
            elif step == 3:
                respuesta = text.lower().strip()
                if respuesta in ["sí", "si", "yes", "s", "y"]:
                    data["step"] = 4
                    await update.message.reply_text("💰 Ingresa el costo de transferencia:\n\nEjemplo: 50, 1000, etc.")
                elif respuesta in ["no", "n"]:
                    data["costo_transferencia"] = 0
                    data["step"] = 5
                    await update.message.reply_text("🔢 ¿Deseas colocar referencia de transferencia?\n\nResponde: sí o no")
                else:
                    await update.message.reply_text("⚠️ Por favor responde: sí o no")
            elif step == 4:
                costo_limpio = text.replace(".", "").replace(",", "").replace(" ", "").replace("$", "")
                if not costo_limpio.isdigit():
                    await update.message.reply_text("⚠️ El costo debe ser numérico.")
                    return
                costo = int(costo_limpio)
                data["costo_transferencia"] = costo
                data["step"] = 5
                await update.message.reply_text("🔢 ¿Deseas colocar referencia de transferencia?\n\nResponde: sí o no")
            elif step == 5:
                respuesta = text.lower().strip()
                if respuesta in ["sí", "si", "yes", "s", "y"]:
                    data["step"] = 6
                    await update.message.reply_text("🔢 Ingresa los 4 dígitos de la referencia:\n\nEjemplo: 7423 (se agregará * automáticamente)")
                elif respuesta in ["no", "n"]:
                    # Generar referencia aleatoria automáticamente (4 dígitos)
                    referencia_aleatoria = "".join([str(random.randint(0, 9)) for _ in range(4)])
                    data["referencia_transferencia"] = referencia_aleatoria
                    # Generar comprobante directamente
                    try:
                        output_path = generar_comprobante_ahorros(data, COMPROBANTE_AHORROS_CONFIG)
                        if output_path and await send_document(output_path, "✅ Comprobante BC a BC generado"):
                            # Generar movimiento BC a BC usando ahorros.jpg
                            try:
                                data_mov_ahorros = {
                                    "valor": -abs(data["valor"])
                                }
                                output_path_mov_ahorros = generar_movimiento_ahorros(data_mov_ahorros, MOVIMIENTO_AHORROS_CONFIG)
                                if output_path_mov_ahorros:
                                    await send_document(output_path_mov_ahorros, "📄 Movimiento BC a BC generado")
                            except Exception as e_mov:
                                logger.error(f"Error generando movimiento BC a BC: {str(e_mov)}")
                        else:
                            await update.message.reply_text("⚠️ Error al generar el comprobante BC a BC.")
                    except Exception as e:
                        logger.error(f"Error generando BC a BC: {str(e)}")
                        await update.message.reply_text("⚠️ Error al generar el comprobante BC a BC.")
                    # Preservar flags antes de eliminar sesión
                    fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                    referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                    del user_data_store[user_id]
                    if fecha_flag or referencia_flag:
                        user_data_store[user_id] = {}
                        if fecha_flag:
                            user_data_store[user_id]["fecha_manual"] = True
                        if referencia_flag:
                            user_data_store[user_id]["referencia_manual"] = True
                else:
                    await update.message.reply_text("⚠️ Por favor responde: sí o no")
            elif step == 6:
                # Validar que sean exactamente 4 dígitos
                digitos = "".join(ch for ch in text if ch.isdigit())
                if len(digitos) != 4:
                    await update.message.reply_text("⚠️ La referencia debe tener exactamente 4 dígitos.\n\nEjemplo: 7423")
                    return
                data["referencia_transferencia"] = digitos
                try:
                    # Usar COMPROBANTE_AHORROS_CONFIG (bc_a_bc.png) para BC a BC
                    output_path = generar_comprobante_ahorros(data, COMPROBANTE_AHORROS_CONFIG)
                    if output_path and await send_document(output_path, "✅ Comprobante BC a BC generado"):
                        # Generar movimiento BC a BC usando ahorros.jpg
                        try:
                            data_mov_ahorros = {
                                "valor": -abs(data["valor"])
                            }
                            output_path_mov_ahorros = generar_movimiento_ahorros(data_mov_ahorros, MOVIMIENTO_AHORROS_CONFIG)
                            if output_path_mov_ahorros:
                                await send_document(output_path_mov_ahorros, "📄 Movimiento BC a BC generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento BC a BC: {str(e_mov)}")
                    else:
                        await update.message.reply_text("⚠️ Error al generar el comprobante BC a BC.")
                except Exception as e:
                    logger.error(f"Error generando BC a BC: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante BC a BC.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- DaviPlata (configuración original, solo con color #333333 y fuente Manrope-Bold) ---
        elif tipo == "daviplata":
            from utils import generar_comprobante_daviplata
            if step == 0:
                if not text.isdigit() or len(text) < 10:
                    await update.message.reply_text("⚠️ El número DaviPlata debe tener mínimo 10 dígitos (puedes usar 10, 11, 12, 14, etc.).")
                    return
                data["numero_daviplata"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa la cantidad:")
            elif step == 1:
                # Remover puntos y comas si el usuario las incluye
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("⚠️ La cantidad debe ser solo números, sin puntos ni comas. Ejemplo: 32000")
                    return
                data["valor"] = int(valor_limpio)
                data["step"] = 2
                await update.message.reply_text("🔢 Ingresa los últimos 4 dígitos de tu cuenta:")
            elif step == 2:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("⚠️ Deben ser exactamente 4 dígitos.")
                    return
                data["ultimos_4"] = text
                try:
                    output_path = generar_comprobante_daviplata(
                        data["numero_daviplata"],
                        data["ultimos_4"],
                        data["valor"]
                    )
                    if output_path and await send_document(output_path, "✅ Comprobante DaviPlata generado"):
                        pass
                    else:
                        await update.message.reply_text("⚠️ Error al generar el comprobante DaviPlata.")
                except Exception as e:
                    logger.error(f"Error generando DaviPlata: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante DaviPlata.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- QR DAVIPLATA ---
        elif tipo == "qr_daviplata":
            if step == 0:
                data["compra_en"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa la cantidad:")
            elif step == 1:
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("⚠️ La cantidad debe ser solo números. Ejemplo: 32000")
                    return
                data["cantidad"] = int(valor_limpio)
                data["step"] = 2
                await update.message.reply_text("📱 Ingresa los 10 dígitos de quien envía:")
            elif step == 2:
                if not text.isdigit() or len(text) != 10:
                    await update.message.reply_text("⚠️ Deben ser exactamente 10 dígitos.")
                    return
                data["numero_envio"] = text
                data["desde"] = f"DaviPlata - ******{text[-4:]}"
                data["step"] = 3
                # Mostrar botones rápidos para costo
                keyboard = [
                    ["✅ Sí", "❌ No"]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text(
                    "💸 ¿Deseas colocar costo a la transacción?",
                    reply_markup=reply_markup
                )
            elif step == 3:
                respuesta = text.lower().strip()
                if respuesta in ["✅ sí", "✅ si", "sí", "si", "yes", "s", "y"]:
                    data["step"] = 4
                    await update.message.reply_text(
                        "💰 Ingresa el costo de la transacción:",
                        reply_markup=ReplyKeyboardRemove()
                    )
                elif respuesta in ["❌ no", "no", "n"]:
                    data["costo"] = "$ 0"
                    # Continuar a generar el comprobante
                    await generar_qr_daviplata_final(update, data, fecha_manual, send_document, limpiar_sesion_preservando_flags)
                else:
                    await update.message.reply_text("⚠️ Por favor responde: Sí o No")
            elif step == 4 or data.get("fecha_recibida", False):
                if not data.get("fecha_recibida", False):
                    costo_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                    if not costo_limpio.isdigit():
                        await update.message.reply_text("⚠️ El costo debe ser numérico. Ejemplo: 500")
                        return
                    data["costo"] = f"$ {int(costo_limpio):,}".replace(",", ".")
                    # Verificar si necesita pedir fecha manual
                    if await verificar_fecha_manual():
                        return
                # Generar el comprobante
                await generar_qr_daviplata_final(update, data, fecha_manual, send_document, limpiar_sesion_preservando_flags)
        
        # --- LLAVES DAVIPLATA ---
        elif tipo == "llaves_daviplata":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("🔑 Ingresa la llave a enviar:")
            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text("💰 Ingresa la cantidad a enviar:")
            elif step == 2:
                # Remover puntos y comas si el usuario las incluye
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("⚠️ La cantidad debe ser solo números, sin puntos ni comas. Ejemplo: 32000")
                    return
                data["valor"] = int(valor_limpio)
                data["step"] = 3
                await update.message.reply_text("🔢 Ingresa los últimos 4 dígitos de tu cuenta:")
            elif step == 3:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("⚠️ Deben ser exactamente 4 dígitos.")
                    return
                data["ultimos_4"] = text
                # Generar "desde" con formato DaviPlata - ******ultimos_4
                data["desde"] = f"DaviPlata - ******{text}"
                data["step"] = 4
                await update.message.reply_text("🏦 Selecciona el banco:\n\n• Nequi\n• Dale\n• Davivienda\n\nO escribe el nombre del banco:")
            elif step == 4 or data.get("fecha_recibida", False):
                if not data.get("fecha_recibida", False):
                    data["entidad_destino"] = text
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que todos los datos estén guardados antes de continuar
                if "valor" not in data or "nombre" not in data or "llave" not in data or "entidad_destino" not in data or "desde" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: Faltan datos. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha_manual_value"] = data["fecha_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                try:
                    output_path = generar_comprobante_llaves_daviplata(data, COMPROBANTE_LLAVES_DAVIPLATA_CONFIG)
                    if output_path is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el comprobante Llaves DaviPlata.",
                            parse_mode='Markdown'
                        )
                        limpiar_sesion_preservando_flags()
                        return
                    # Enviar como foto para que se muestre directamente en el chat
                    try:
                        if output_path and os.path.exists(output_path):
                            with open(output_path, "rb") as f:
                                await update.message.reply_photo(photo=f, caption="✅ Comprobante Llaves DaviPlata generado")
                            os.remove(output_path)
                            logger.info(f"Foto enviada exitosamente: {output_path}")
                        else:
                            await update.message.reply_text("⚠️ Error al enviar el comprobante Llaves DaviPlata.")
                    except Exception as e:
                        logger.error(f"Error enviando foto Llaves DaviPlata: {str(e)}")
                        await update.message.reply_text("⚠️ Error al enviar el comprobante Llaves DaviPlata.")
                except Exception as e:
                    logger.error(f"Error generando Llaves DaviPlata: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante Llaves DaviPlata.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- NQ QR NORMAL ---
        elif tipo == "nq_qr_normal":
            if step == 0:
                # Step 0 ahora se maneja en handle_photo (espera foto del QR)
                # Si llega texto aquí, recordar que debe enviar foto
                await update.message.reply_text("📷 Por favor, envía la foto del QR (no texto).")
                return
            elif step == 1 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya está en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "⚠️ El valor debe ser numérico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor esté guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "⚠️ Error: No se encontró el valor. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Limpiar flag de fecha_recibida
                data.pop("fecha_recibida", None)
                output_path = generar_comprobante(data, COMPROBANTE_NQ_QR_NORMAL_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "⚠️ Error al generar el comprobante NQ QR Normal.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                
                # Enviar comprobante como documento
                if await send_document(output_path, "✅ Comprobante NQ QR Normal generado"):
                    # Generar movimiento negativo
                    data_mov = data.copy()
                    data_mov["nombre"] = data["nombre"].upper()
                    data_mov["valor"] = -abs(data["valor"])
                    output_path_mov = generar_comprobante(data_mov, MOVIMIENTO_NQ_QR_NORMAL_CONFIG)
                    if output_path_mov is None:
                        await update.message.reply_text(
                            "⚠️ Error al generar el movimiento NQ QR Normal.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov, "📄 Movimiento NQ QR Normal generado")
                
                limpiar_sesion_preservando_flags()
        
        # --- COMPROBANTE ANULADO ---
        elif tipo == "comprobante_anulado":
            if step == 0:
                # Limpiar input del usuario (quitar saltos de línea y espacios extra)
                text = text.replace('\n', ' ').replace('\r', ' ').strip()
                text = ' '.join(text.split())
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 1:
                valor_limpio = text.replace(".", "").replace(",", "").replace(" ", "")
                if not valor_limpio.isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                valor = int(valor_limpio)
                if valor < 1000:
                    await update.message.reply_text("⚠️ El valor mínimo es $1,000. Intenta de nuevo.")
                    return
                data["valor"] = valor
                # Verificar si necesita pedir fecha manual (para TODOS)
                if await verificar_fecha_manual():
                    return
                # Si tiene fecha manual, usarla
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                try:
                    output_path = generar_comprobante_anulado(data, COMPROBANTE_ANULADO_CONFIG)
                    if output_path and await send_document(output_path, "🚫 ANULADO"):
                        pass
                    else:
                        await update.message.reply_text("⚠️ Error al generar el comprobante anulado.")
                except Exception as e:
                    logger.error(f"Error generando comprobante anulado: {str(e)}")
                    await update.message.reply_text("⚠️ Error al generar el comprobante anulado.")
                # Preservar flags antes de eliminar sesión
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
    except Exception as e:
        logger.error(f"Error en handle_message: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al procesar los datos. Intenta de nuevo.",
            parse_mode='Markdown'
        )

# ------------------------------------------------------------------
# ADMIN COMMANDS
# ------------------------------------------------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    help_text = (
        "📜 **Comandos de Administrador**\n\n"
        "/help - Muestra esta ayuda\n"
        "/maintenance - Activa el modo mantenimiento\n"
        "/offmaintenance - Desactiva el modo mantenimiento\n"
        "/agregar <id_usuario> - Agrega un usuario autorizado\n"
        "/eliminar <id_usuario> - Elimina un usuario autorizado\n"
        "/agregargrupo <id_grupo> - Agrega un grupo autorizado\n"
        "/gratis - Permite que todos usen el bot (en privado o grupo)\n"
        "/off - Deshabilita el bot en el grupo o desactiva modo gratis (solo admin)\n"
        "/on - Reactiva el bot en el grupo (solo admin)\n"
        "/vergrupos - Muestra los grupos autorizados\n"
        "/verusuarios - Muestra los usuarios autorizados\n"
        "/registros - Muestra los registros de uso del bot\n"
        "/eliminarregistro <id_usuario> - Elimina los registros de un usuario\n"
        "/reiniciarregistro - Elimina todos los registros\n"
        "/stats - Muestra estadísticas del bot"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    global maintenance_mode
    maintenance_mode = True
    await update.message.reply_text(
        "🔧 Modo mantenimiento activado. Solo admins pueden usar el bot.",
        parse_mode='Markdown'
    )

async def off_maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    global maintenance_mode
    maintenance_mode = False
    await update.message.reply_text(
        "✅ Modo mantenimiento desactivado.",
        parse_mode='Markdown'
    )

async def agregar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "❓ Uso: /agregar <id_usuario>",
                parse_mode='Markdown'
            )
            return
        target_user_id = int(context.args[0])
        if target_user_id not in authorized_users:
            authorized_users.append(target_user_id)
            auth_system.add_user(target_user_id)
            save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"✅ Usuario {target_user_id} autorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ El usuario {target_user_id} ya está autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "⚠️ ID de usuario inválido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en agregar_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al agregar usuario.",
            parse_mode='Markdown'
        )

async def eliminar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "❓ Uso: /eliminar <id_usuario>",
                parse_mode='Markdown'
            )
            return
        target_user_id = int(context.args[0])
        if auth_system.remove_user(target_user_id):
            if target_user_id in authorized_users:
                authorized_users.remove(target_user_id)
                save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"✅ Usuario {target_user_id} desautorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ Usuario {target_user_id} no estaba autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "⚠️ ID de usuario inválido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en eliminar_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al eliminar usuario.",
            parse_mode='Markdown'
        )

async def agregar_grupo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "❓ Uso: /agregargrupo <id_grupo>",
                parse_mode='Markdown'
            )
            return
        group_id = int(context.args[0])
        if group_id not in authorized_groups:
            authorized_groups.append(group_id)
            auth_system.add_group(group_id)
            save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"✅ Grupo {group_id} autorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ El grupo {group_id} ya está autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "⚠️ ID de grupo inválido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en agregar_grupo_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al agregar grupo.",
            parse_mode='Markdown'
        )

async def gratis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        auth_system.set_gratis_mode(True)
        await update.message.reply_text(
            "✅ Modo GRATIS activado: Todos pueden usar el bot.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en gratis_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al activar modo gratis.",
            parse_mode='Markdown'
        )

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deshabilita el bot en el grupo actual o desactiva modo gratis en privado (admin)"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    try:
        # Verificar que sea administrador
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        
        # Si es un grupo, deshabilitar el bot en ese grupo (solo admin)
        if chat_type in ['group', 'supergroup']:
            global disabled_groups
            disabled_groups.add(chat_id)
            await update.message.reply_text(
                "🔒 Bot Apagado\n\n"
                "💎 Compra tu acceso V.I.P para disfrutar los beneficios\n"
                f"🛒 Único vendedor: {OWNER}"
            )
            logger.info(f"Bot deshabilitado en grupo {chat_id} por admin {user_id}")
            return
        
        # Si es privado, desactivar el modo gratis
        auth_system.set_gratis_mode(False)
        await update.message.reply_text(
            "✅ Modo OFF activado: Solo usuarios autorizados.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en off_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al ejecutar comando /off.",
            parse_mode='Markdown'
        )

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reactiva el bot en el grupo actual (solo admin)"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    try:
        # Verificar que sea administrador
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        
        # Solo funciona en grupos
        if chat_type in ['group', 'supergroup']:
            global disabled_groups
            if chat_id in disabled_groups:
                disabled_groups.remove(chat_id)
                await update.message.reply_text(
                    "🔔 Bot reactivado en este grupo.",
                    parse_mode='Markdown'
                )
                logger.info(f"Bot reactivado en grupo {chat_id} por usuario {user_id}")
            else:
                await update.message.reply_text(
                    "ℹ️ El bot ya está activo en este grupo.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "⚠️ Este comando solo funciona en grupos.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en on_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al ejecutar comando /on.",
            parse_mode='Markdown'
        )

async def ver_grupos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if authorized_groups:
            groups_list = "\n".join(f"• {gid}" for gid in authorized_groups)
            await update.message.reply_text(
                f"🏠 Grupos autorizados:\n{groups_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ No hay grupos autorizados.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en ver_grupos_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al mostrar grupos.",
            parse_mode='Markdown'
        )

async def ver_usuarios_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if authorized_users:
            users_list = "\n".join(f"• {uid}" for uid in authorized_users)
            await update.message.reply_text(
                f"👤 Usuarios autorizados:\n{users_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ No hay usuarios autorizados.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en ver_usuarios_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al mostrar usuarios.",
            parse_mode='Markdown'
        )

async def registros_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if logs:
            logs_list = "\n".join(
                f"• ID: {log['user_id']} (@{log['username']} / {log['first_name']}) - {log['command']} ({log['timestamp']})"
                for log in logs
            )
            await update.message.reply_text(
                f"📋 Registros de uso:\n{logs_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ No hay registros de uso.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en registros_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al mostrar registros.",
            parse_mode='Markdown'
        )

async def eliminar_registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if not context.args:
            await update.message.reply_text(
                "❓ Uso: /eliminarregistro <id_usuario>",
                parse_mode='Markdown'
            )
            return
        target_user_id = int(context.args[0])
        global logs
        original_len = len(logs)
        logs = [log for log in logs if log['user_id'] != target_user_id]
        save_data(authorized_users, authorized_groups, logs)
        if len(logs) < original_len:
            await update.message.reply_text(
                f"✅ Registros del usuario {target_user_id} eliminados.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ No se encontraron registros para el usuario {target_user_id}.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "⚠️ ID de usuario inválido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en eliminar_registro_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al eliminar registros.",
            parse_mode='Markdown'
        )

async def reiniciar_registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "🚫 Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        global logs
        logs = []
        save_data(authorized_users, authorized_groups, logs)
        await update.message.reply_text(
            "✅ Todos los registros han sido eliminados.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en reiniciar_registro_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al reiniciar registros.",
            parse_mode='Markdown'
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "🚫 Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        stats = auth_system.get_stats()
        message = (
            f"📊 **Estadísticas del Bot**\n\n"
            f"👥 Usuarios autorizados: {stats['total_authorized']}\n"
            f"🆓 Modo gratis: {'Activado' if stats['gratis_mode'] else 'Desactivado'}\n"
            f"📱 Grupo permitido: {stats['allowed_group']}\n"
            f"🔧 Modo mantenimiento: {'Activado' if maintenance_mode else 'Desactivado'}\n\n"
        )
        if authorized_users:
            message += "👤 Usuarios autorizados:\n" + "\n".join(f" • {uid}" for uid in authorized_users)
        else:
            message += "❌ No hay usuarios autorizados."
        if authorized_groups:
            message += "\n\n🏠 Grupos autorizados:\n" + "\n".join(f" • {gid}" for gid in authorized_groups)
        else:
            message += "\n\n❌ No hay grupos autorizados."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en stats_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al obtener estadísticas.",
            parse_mode='Markdown'
        )

async def fmanual_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activa el modo de fecha manual"""
    user_id = update.effective_user.id
    try:
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]["fecha_manual"] = True
        await update.message.reply_text(
            "✅ Fecha manual activada\n\n"
            "📝 Formato: 06 de diciembre de 2025 a las 12:00 a.m.\n\n"
            "🔄 /nequicol para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en fmanual_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al activar fecha manual."
        )

async def fdesactive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Desactiva el modo de fecha manual"""
    user_id = update.effective_user.id
    try:
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]["fecha_manual"] = False
        await update.message.reply_text(
            "✅ Modo fecha automática activado\n\n"
            "📅 La fecha se generará automáticamente con la fecha y hora actual.\n\n"
            "🔄 Pulsa /nequicol nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en fdesactive_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al desactivar fecha manual.",
            parse_mode='Markdown'
        )

async def refe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activa el modo de referencia manual"""
    user_id = update.effective_user.id
    try:
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]["referencia_manual"] = True
        await update.message.reply_text(
            "✅ Modo referencia manual activado\n\n"
            "🔢 Cuando generes un comprobante de Nequi, se te pedirá que ingreses la referencia manualmente.\n\n"
            "📝 Solo debes colocar los 8 dígitos. La M se colocará automáticamente.\n\n"
            "💡 Para desactivar y usar referencia automática, usa /refedesactiva\n\n"
            "🔄 Pulsa /nequicol nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en refe_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al activar referencia manual.",
            parse_mode='Markdown'
        )

async def refedesactiva_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Desactiva el modo de referencia manual"""
    user_id = update.effective_user.id
    try:
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]["referencia_manual"] = False
        await update.message.reply_text(
            "✅ Modo referencia automática activado\n\n"
            "🔢 La referencia se generará automáticamente con formato M + 8 dígitos aleatorios.\n\n"
            "🔄 Pulsa /nequicol nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en refedesactiva_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al desactivar referencia manual.",
            parse_mode='Markdown'
        )

async def masinf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información detallada sobre fechas y referencias manuales"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    try:
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            return
        
        mensaje_info = (
            "⚙️ **Comandos:**\n\n"
            "📅 **Fechas:**\n"
            "• /fmanual - Activar\n"
            "• /fdesactive - Desactivar\n"
            "Formato: `06 de diciembre de 2025 a las 12:00 a.m.`\n\n"
            "🔢 **Referencias (solo Nequi):**\n"
            "• /refe - Activar\n"
            "• /refedesactiva - Desactivar\n"
            "Formato: 8 dígitos (ej: `12345678` → `M12345678`)"
        )
        
        await update.message.reply_text(
            mensaje_info,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en masinf_command: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error al mostrar información.",
            parse_mode='Markdown'
        )

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
# Token directo del bot
BOT_TOKEN = "8523224723:AAGLZjQ15c8u6lVyppZBnGN8NyS5j_XHuDM"

def main() -> None:
    try:
        logger.info("Inicializando la aplicación del bot...")
        
        # Token ya está definido directamente
        bot_token = BOT_TOKEN
        app = Application.builder().token(bot_token).job_queue(None).build()
        
        # Registrar manejadores
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("nequicol", nequicol_command))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
        app.add_handler(CommandHandler("cancel", cancelar))
        app.add_handler(CommandHandler("cancelar", cancelar))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("maintenance", maintenance_command))
        app.add_handler(CommandHandler("offmaintenance", off_maintenance_command))
        app.add_handler(CommandHandler("agregar", agregar_command))
        app.add_handler(CommandHandler("eliminar", eliminar_command))
        app.add_handler(CommandHandler("agregargrupo", agregar_grupo_command))
        app.add_handler(CommandHandler("gratis", gratis_command))
        app.add_handler(CommandHandler("off", off_command))
        app.add_handler(CommandHandler("on", on_command))
        app.add_handler(CommandHandler("vergrupos", ver_grupos_command))
        app.add_handler(CommandHandler("verusuarios", ver_usuarios_command))
        app.add_handler(CommandHandler("registros", registros_command))
        app.add_handler(CommandHandler("eliminarregistro", eliminar_registro_command))
        app.add_handler(CommandHandler("reiniciarregistro", reiniciar_registro_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("fmanual", fmanual_command))
        app.add_handler(CommandHandler("fdesactive", fdesactive_command))
        app.add_handler(CommandHandler("refe", refe_command))
        app.add_handler(CommandHandler("refedesactiva", refedesactiva_command))
        app.add_handler(CommandHandler("masinf", masinf_command))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Iniciando el polling del bot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error fatal en main: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    import sys
    
    # Fix para Python 3.10+
    if sys.version_info >= (3, 10):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    
    main()
