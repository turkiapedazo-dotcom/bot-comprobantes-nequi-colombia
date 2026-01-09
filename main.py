# -*- coding: utf-8 -*-
import asyncio
import random
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

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
ADMIN_IDS = [8465944523, 8485045964]  # IDs de los administradores
ALLOWED_GROUP = -1003122616445  # ID del grupo permitido principal
ALLOWED_GROUPS_HARDCODED = [-1003349066708]  # Grupos siempre permitidos
OWNER = "@ROBERTKIMBDO"
GROUP_INVITE_LINK = "https://t.me/Nequiglitchofficiall"  # Link del grupo

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
disabled_groups = set()  # Grupos donde el bot estÃ¡ deshabilitado con /off
# Anti-spam: guardar Ãºltimo mensaje por usuario/grupo
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
                            logger.warning(f"Estructura JSON invÃ¡lida en {file_path}. Usando valor por defecto.")
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
# COMANDOS
# ------------------------------------------------------------------
async def nequiglitch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando que muestra botones de acceso rÃ¡pido - Verifica autorizaciÃ³n del grupo"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_name = update.effective_user.first_name or update.effective_user.username or "Usuario"
    
    try:
        # Verificar si el bot estÃ¡ deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot estÃ¡ deshabilitado en este grupo
        # Anti-spam: cooldown de 3 segundos por usuario
        import time
        current_time = time.time()
        key = f"nequiglitch_{chat_id}_{user_id}"
        
        if key in last_command_time:
            if current_time - last_command_time[key] < 3:
                return  # Ignorar si fue hace menos de 3 segundos
        
        last_command_time[key] = current_time
        
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            if not auth_system.gratis_mode:
                await update.message.reply_text(
                    "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            return
        
        # Todos los comprobantes disponibles en grupos y privado
        keyboard = [
            ["ðŸ’¸ Nequi", "ðŸ”„ BRE-B"],
            ["ðŸ“± QR Comprobante", "ðŸ”‘ LLAVES"],
            ["ðŸ¦ Nequi a Bancolombia"],
            ["ðŸ¦ QR BC", "ðŸ’³ BC a Nequi"],
            ["ðŸ›ï¸ BC a BC", "ðŸ”µ DaviPlata"],
            ["ðŸ“± QR DaviPlata", "ðŸ’³ Llaves DaviPlata"],
            ["ðŸ“² NQ QR NORMAL"],
            ["âœ… Anulado"],
            ["âŒ Cancelar"]
        ]
        mensaje_comandos = (
            f"ðŸ‘‹ Hola {user_name}!\n\n"
            f"ðŸ’Ž Generador de Comprobantes\n"
            f"ðŸ“Œ Selecciona una opciÃ³n:\n\n"
            f"â„¹ï¸ Para conocer funciones de fechas y referencias manuales, pulsa /masinf"
        )
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            mensaje_comandos,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error en nequiglitch_command: {str(e)}")

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cuando el bot es agregado a un grupo"""
    try:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                # El bot fue agregado al grupo
                user_name = update.effective_user.first_name or update.effective_user.username or "Usuario"
                await update.message.reply_text(
                    f"ðŸŽ‰ Hola {user_name}!\n\n"
                    f"Para iniciar el bot presiona /Nequiglitch\n\n"
                    f"ðŸ’Ž Servicio gratuito de alta calidad"
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
        # Verificar si el bot estÃ¡ deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot estÃ¡ deshabilitado en este grupo

      # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            if not auth_system.gratis_mode:
                await update.message.reply_text(
                "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                parse_mode="HTML",
                 disable_web_page_preview=True
                )


        
        
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
            await update.message.reply_text(f"ðŸ‘‹ Hola {user_name}!\n\nPresiona /Nequiglitch para iniciar")
            return
        
        # En privado: mostrar bienvenida personalizada
        user_display_name = first_name or username or "Usuario"
        username_display = f"@{username}" if username else "Sin username"
        first_name_display = first_name or 'No disponible'
        
        # Verificar autorizaciÃ³n
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            await update.message.reply_text("âš ï¸ Bot en mantenimiento.")
            return
        
        # Usuario autorizado (ya verificÃ³ membresÃ­a), mostrar mensaje de bienvenida
        mensaje_bienvenida = (
            f"ðŸ‘‹ Â¡Bienvenido {user_display_name}!\n\n"
            f"ðŸ“‹ InformaciÃ³n de tu cuenta:\n"
            f"ðŸ†” ID: {user_id}\n"
            f"ðŸ‘¤ Nombre: {first_name_display}\n"
            f"ðŸ“± Username: {username_display}\n\n"
            f"ðŸ’Ž Para usar el bot, escribe /Nequiglitch\n\n"
            f"â„¹ï¸ Para conocer funciones de fechas y referencias manuales, pulsa /masinf"
        )
        await update.message.reply_text(mensaje_bienvenida)
    except Exception as e:
        logger.error(f"Error en comando start: {str(e)}")
        # No enviar mensaje de error en grupos para evitar spam
        if chat_type == 'private':
            await update.message.reply_text("âš ï¸ Error. Intenta /start de nuevo.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Verificar si el bot estÃ¡ deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot estÃ¡ deshabilitado en este grupo
        
        if user_id in user_data_store:
            del user_data_store[user_id]
            await update.message.reply_text(
                "âœ… OperaciÃ³n cancelada correctamente.\n\n"
                "Presiona /Nequiglitch para generar un nuevo comprobante.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "âŒ No hay ninguna operaciÃ³n activa para cancelar.\n\n"
                "Presiona /Nequiglitch para generar un comprobante.",
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        logger.error(f"Error en cancelar: {str(e)}")

# ------------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        chat_type = query.message.chat.type
        username = query.from_user.username
        first_name = query.from_user.first_name
        
        # Verificar si el bot estÃ¡ deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot estÃ¡ deshabilitado en este grupo
        
        # Si se ejecuta en grupo, ignorar
        if chat_type in ['group', 'supergroup']:
            await query.message.reply_text(
                f"ðŸ‘‹ @{username}, usa el bot en privado.",
                parse_mode='Markdown'
            )
            return
        
        # Actualizar informaciÃ³n de admins
        if user_id in ADMIN_IDS:
            context.bot_data.setdefault('admin_info', {})
            context.bot_data['admin_info'][user_id] = {
                'username': username or 'N/A',
                'first_name': first_name or 'N/A'
            }
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            if not auth_system.gratis_mode:
                await update.message.reply_text(
                    "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            return
        
        # Si el usuario es admin del bot, saltar verificaciÃ³n
        if user_id in ADMIN_IDS:
            pass  # Admin del bot, acceso permitido
        # Si el mensaje viene desde el grupo permitido, el usuario ya estÃ¡ ahÃ­
        elif chat_id == ALLOWED_GROUP:
            pass  # Usuario estÃ¡ en el grupo, acceso permitido
        else:
            # Usuario estÃ¡ fuera del grupo, verificar si es miembro
            try:
                member = await context.bot.get_chat_member(ALLOWED_GROUP, user_id)
                # Incluir 'restricted' para admins anÃ³nimos y otros casos especiales
                if member.status not in ['member', 'administrator', 'creator', 'restricted']:
                    await query.message.reply_text(
                        "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                    )
                    return
            except Exception as e:
                logger.warning(f"No se pudo verificar membresÃ­a del usuario {user_id}: {str(e)}")
                # Si falla la verificaciÃ³n pero el usuario es admin anÃ³nimo, puede que get_chat_member falle
                # En ese caso, permitir si viene de un chat que podrÃ­a ser el grupo
                if chat_id < 0:  # Es un grupo, podrÃ­a ser admin anÃ³nimo
                    pass  # Permitir acceso
                else:
                    await query.message.reply_text(
                        "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                    )
                    return
        
        # Verificar modo mantenimiento
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            admin_list = "\n".join(f"â€¢ {uid} (@{info['username']})"
                                   for uid, info in context.bot_data.get('admin_info', {}).items())
            await query.message.reply_text(
                f"âš ï¸ El bot estÃ¡ en mantenimiento. Contacta a los administradores: {OWNER}",
                parse_mode='Markdown'
            )
            return
        tipo = query.data or "default"
        
        # Preservar flags de configuraciÃ³n (fecha_manual, referencia_manual) si existen
        fecha_manual_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
        referencia_manual_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
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
            "comprobante1": "ðŸ‘¤ Ingresa el nombre completo:",
            "comprobante4": "ðŸ‘¤ Ingresa el nombre a enviar:",
            "comprobante_qr": "ðŸ¬ Nombre del negocio:",
            "comprobante_llave": "ðŸ‘¤ Ingresa el nombre a enviar:",
            "bancolombia": "ðŸ‘¤ Ingresa el nombre del destinario:",
            "llaves_daviplata": "ðŸ‘¤ Ingresa el nombre del destinatario:",
            "nq_qr_normal": "ðŸ¬ Ingresa el nombre del negocio:",
            "qr_daviplata": "ðŸ¬ Ingresa el nombre del negocio (Compra en):"
        }
        await query.message.reply_text(
            prompts.get(tipo, "ðŸ” Por favor, inicia ingresando los datos requeridos:"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en button_handler: {str(e)}")
        await query.message.reply_text("âš ï¸ Error al procesar la selecciÃ³n. Intenta de nuevo.", parse_mode='Markdown')

# ------------------------------------------------------------------
# MENSAJES
# ------------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    text = update.message.text.strip()
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        # Verificar si el bot estÃ¡ deshabilitado en este grupo
        if chat_id < 0 and chat_id in disabled_groups:
            return  # No responder si el bot estÃ¡ deshabilitado en este grupo
        # Detectar si el usuario presionÃ³ "âŒ Cancelar"
        if text == "âŒ Cancelar":
            if user_id in user_data_store:
                del user_data_store[user_id]
                await update.message.reply_text(
                    "âœ… OperaciÃ³n cancelada correctamente.\n\n"
                    "Presiona /Nequiglitch para generar un nuevo comprobante.",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    "âŒ No hay ninguna operaciÃ³n activa para cancelar.\n\n"
                    "Presiona /Nequiglitch para generar un comprobante.",
                    reply_markup=ReplyKeyboardRemove()
                )
            return
        
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            if not auth_system.gratis_mode:
                await update.message.reply_text(
                    "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            return
        
        # Si el usuario es admin del bot, saltar verificaciÃ³n
        if user_id in ADMIN_IDS:
            pass  # Admin del bot, acceso permitido
        # Si el mensaje viene desde el grupo permitido, el usuario ya estÃ¡ ahÃ­
        elif chat_id == ALLOWED_GROUP:
            pass  # Usuario estÃ¡ en el grupo, acceso permitido
        else:
            # Usuario estÃ¡ fuera del grupo, verificar si es miembro
            try:
                member = await context.bot.get_chat_member(ALLOWED_GROUP, user_id)
                # Incluir 'restricted' para admins anÃ³nimos y otros casos especiales
                if member.status not in ['member', 'administrator', 'creator', 'restricted']:
                    await update.message.reply_text(
                        "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                    )
                    return
            except Exception as e:
                logger.warning(f"No se pudo verificar membresÃ­a del usuario {user_id}: {str(e)}")
                # Si falla la verificaciÃ³n pero el usuario es admin anÃ³nimo, puede que get_chat_member falle
                # En ese caso, permitir si viene de un chat que podrÃ­a ser el grupo
                if chat_id < 0:  # Es un grupo, podrÃ­a ser admin anÃ³nimo
                    pass  # Permitir acceso
                else:
                    await update.message.reply_text(
                        "ðŸ‘‘ Este bot estÃ¡ restringido en el privado para evitar estafas.\n\n"
                    "Si deseas usarlo gratuitamente sin pagar nada, mÃ¡ndale un mensaje al OWNER ðŸ‘‘ @ROBERTKIMBDO\n\n"
                    "ðŸ‘‰ <a href='https://t.me/Nequiglitchofficiall'>Grupo Oficial</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                    )
                    return
        
        # Detectar si el mensaje es de los botones de acceso rÃ¡pido (antes de ignorar grupos)
        button_mapping = {
            "ðŸ’¸ Nequi": "comprobante1",
            "ðŸ”„ BRE-B": "comprobante4",
            "ðŸ“± QR Comprobante": "comprobante_qr",
            "ðŸ”‘ LLAVES": "comprobante_llave",
            "ðŸ¦ Nequi a Bancolombia": "bancolombia",
            "ðŸ¦ QR BC": "qr_bc",
            "ðŸ’³ BC a Nequi": "bc_nequi",
            "ðŸ›ï¸ BC a BC": "bc_bc",
            "ðŸ”µ DaviPlata": "daviplata",
            "ðŸ“± QR DaviPlata": "qr_daviplata",
            "ðŸ’³ Llaves DaviPlata": "llaves_daviplata",
            "ðŸ“² NQ QR NORMAL": "nq_qr_normal",
            "âœ… Anulado": "comprobante_anulado"
        }
        
        # Permitir todos los comprobantes en grupos y privado
        if text in button_mapping:
            tipo = button_mapping[text]
            
            # Preservar flags de configuraciÃ³n (fecha_manual, referencia_manual) si existen
            fecha_manual_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
            referencia_manual_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
            user_data_store[user_id] = {
                "step": 0, 
                "tipo": tipo, 
                "session_id": str(uuid4()),
                "fecha_manual": fecha_manual_flag,
                "referencia_manual": referencia_manual_flag
            }
            
            # Cerrar el teclado de acceso rÃ¡pido
            prompts = {
                "comprobante1": "ðŸ‘¤ Ingresa el nombre del destinatario:",
                "comprobante4": "ðŸ‘¤ Ingresa el nombre a enviar:",
                "comprobante_qr": "ðŸ¬ Nombre del negocio:",
                "comprobante_llave": "ðŸ‘¤ Ingresa el nombre a enviar:",
                "bancolombia": "ðŸ‘¤ Ingresa el nombre del destinario:",
                "qr_bc": "ðŸ¬ Ingresa el punto de venta:",
                "bc_nequi": "ðŸ“± Ingresa el nÃºmero Nequi (10 dÃ­gitos):",
                "bc_bc": "ðŸ‘¤ Ingresa el nombre:",
                "daviplata": "ðŸ“± Ingresa el nÃºmero DaviPlata (mÃ­nimo 10 dÃ­gitos):",
                "llaves_daviplata": "ðŸ‘¤ Ingresa el nombre del destinatario:",
                "nq_qr_normal": "ðŸ¬ Ingresa el nombre del negocio:",
                "qr_daviplata": "ðŸ¬ Ingresa el nombre del negocio (Compra en):",
                "comprobante_anulado": "ðŸ‘¤ Â¿Nombre de la vÃ­ctima?"
            }
            await update.message.reply_text(
                prompts.get(tipo, "ðŸ” Por favor, inicia ingresando los datos requeridos:"),
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # En grupos: solo responder si el usuario tiene una sesiÃ³n activa
        if chat_type in ['group', 'supergroup']:
            if user_id not in user_data_store:
                return  # Ignorar mensajes aleatorios en grupos
        
        # Actualizar informaciÃ³n de admins
        if user_id in ADMIN_IDS:
            context.bot_data.setdefault('admin_info', {})
            context.bot_data['admin_info'][user_id] = {
                'username': username or 'N/A',
                'first_name': first_name or 'N/A'
            }
        # Verificar modo mantenimiento
        global maintenance_mode
        if maintenance_mode and user_id not in ADMIN_IDS:
            admin_list = "\n".join(f"â€¢ {uid} (@{info['username']})"
                                   for uid, info in context.bot_data.get('admin_info', {}).items())
            await update.message.reply_text(
                f"âš ï¸ El bot estÃ¡ en mantenimiento. Contacta a los administradores:\n{admin_list}",
                parse_mode='Markdown'
            )
            return
        
        if user_id not in user_data_store:
            return  # No responde si el usuario no estÃ¡ en una sesiÃ³n activa
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
        
        # FunciÃ³n auxiliar para limpiar sesiÃ³n preservando flags de configuraciÃ³n
        def limpiar_sesion_preservando_flags():
            """Elimina la sesiÃ³n pero preserva los flags de configuraciÃ³n del usuario"""
            fecha_flag = data.get("fecha_manual", False)
            referencia_flag = data.get("referencia_manual", False)
            del user_data_store[user_id]
            # Restaurar solo los flags de configuraciÃ³n si existen
            if fecha_flag or referencia_flag:
                user_data_store[user_id] = {}
                if fecha_flag:
                    user_data_store[user_id]["fecha_manual"] = True
                if referencia_flag:
                    user_data_store[user_id]["referencia_manual"] = True
        
        # FunciÃ³n auxiliar para verificar y pedir fecha antes de generar (para TODOS)
        async def verificar_fecha_manual():
            """Verifica si necesita pedir fecha manual y la solicita"""
            if fecha_manual and "fecha_manual_value" not in data:
                data["esperando_fecha"] = True
                await update.message.reply_text(
                    "ðŸ“… Fecha Manual\n\n"
                    "ðŸ“ Ingresa la fecha:\n"
                    "Ejemplo: 06 de diciembre de 2025 a las 12:00 a.m."
                )
                return True
            return False
        
        # FunciÃ³n auxiliar para verificar y pedir referencia (solo Nequi)
        async def verificar_referencia_manual():
            """Verifica si necesita pedir referencia manual y la solicita (solo Nequi)"""
            if referencia_manual and "referencia_manual_value" not in data:
                data["esperando_referencia"] = True
                await update.message.reply_text(
                    "ðŸ”¢ Referencia Manual\n\n"
                    "Ingresa solo los 8 dÃ­gitos de la referencia.\n"
                    "La M se colocarÃ¡ automÃ¡ticamente.\n\n"
                    "Ejemplo: 12345678\n\n"
                    "La referencia se formatearÃ¡ como: M12345678"
                )
                return True
            return False
        
        # Si estÃ¡ esperando fecha, procesarla primero (ANTES de cualquier paso del comprobante)
        if data.get("esperando_fecha", False):
            data["fecha_manual_value"] = text
            data["esperando_fecha"] = False
            # Continuar con referencia si estÃ¡ activada (solo Nequi)
            if await verificar_referencia_manual():
                return
            # Si no hay referencia manual, continuar con la generaciÃ³n del comprobante
            # Marcar que la fecha fue recibida para continuar con la generaciÃ³n
            data["fecha_recibida"] = True
            # Continuar con el flujo normal del comprobante (no retornar)
        
        # Si estÃ¡ esperando referencia (solo Nequi), procesarla primero
        if data.get("esperando_referencia", False):
            # Validar que sean exactamente 8 dÃ­gitos
            if not text.isdigit() or len(text) != 8:
                await update.message.reply_text(
                    "âš ï¸ La referencia debe tener exactamente 8 dÃ­gitos.\n"
                    "Ejemplo: 12345678"
                )
                return
            data["referencia_manual_value"] = f"M{text}"
            data["esperando_referencia"] = False
            # Marcar que la referencia fue recibida para continuar con la generaciÃ³n
            data["fecha_recibida"] = True
            # Continuar con el flujo normal del comprobante (no retornar)
        
        async def send_document(output_path: str, caption: str) -> bool:
            # Asegurar que el archivo exista antes de enviarlo
            try:
                if output_path is None or not os.path.exists(output_path):
                    logger.error(f"Documento no encontrado o None: {output_path}")
                    await update.message.reply_text(
                        "âš ï¸ Error: No se pudo generar el comprobante.",
                        parse_mode='Markdown'
                    )
                    return False
                
                # Verificar tamaÃ±o del archivo (Telegram lÃ­mite: 50MB, pero archivos grandes pueden fallar)
                file_size = os.path.getsize(output_path)
                file_size_mb = file_size / (1024 * 1024)
                logger.info(f"Enviando documento: {output_path}, TamaÃ±o: {file_size_mb:.2f} MB")
                
                if file_size > 50 * 1024 * 1024:  # 50MB
                    logger.error(f"Archivo demasiado grande: {file_size_mb:.2f} MB")
                    await update.message.reply_text(
                        f"âš ï¸ Error: El archivo generado es demasiado grande ({file_size_mb:.2f} MB). LÃ­mite: 50 MB.",
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
                    f"âš ï¸ Error al enviar el comprobante.\n\nDetalle: {str(e)}",
                    parse_mode='Markdown'
                )
                return False
        
        async def generar_qr_daviplata_final(update, data, fecha_manual, send_document, limpiar_sesion_preservando_flags):
            """FunciÃ³n auxiliar para generar el comprobante QR DaviPlata"""
            # Si tiene fecha manual, usarla
            if fecha_manual and "fecha_manual_value" in data:
                data["fecha"] = data["fecha_manual_value"]
            # Limpiar flag de fecha_recibida
            data.pop("fecha_recibida", None)
            
            try:
                output_path = generar_comprobante_qr_daviplata(data, COMPROBANTE_QR_DAVIPLATA_CONFIG)
                if output_path is None:
                    await update.message.reply_text(
                        "âš ï¸ Error al generar el comprobante QR DaviPlata.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Enviar como documento
                await send_document(output_path, "âœ… Comprobante QR DaviPlata generado")
            except Exception as e:
                logger.error(f"Error generando QR DaviPlata: {str(e)}")
                await update.message.reply_text("âš ï¸ Error al generar el comprobante QR DaviPlata.")
            limpiar_sesion_preservando_flags()
        
        # --- NEQUI ---
        if tipo == "comprobante1":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "ðŸ“± Ingresa el nÃºmero de telÃ©fono (solo dÃ­gitos):",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.isdigit():
                    await update.message.reply_text(
                        "âš ï¸ El nÃºmero debe contener solo dÃ­gitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["telefono"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "ðŸ’° Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 2 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "âš ï¸ El valor debe ser numÃ©rico.",
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
                # Verificar que el valor estÃ© guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ el valor. Por favor, intenta de nuevo.",
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
                        "âš ï¸ Error al generar el comprobante Nequi.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                               # Enviar comprobante como foto (no como documento)
                try:
                    with open(output_path, "rb") as f:
                        await update.message.reply_photo(photo=f, caption="âœ… Comprobante Nequi generado")
                    os.remove(output_path)
                    comprobante_enviado = True
                except Exception as e:
                    logger.error(f"Error al enviar comprobante Nequi como foto: {e}")
                    await update.message.reply_text("âš ï¸ Error al enviar el comprobante.")
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
                            "âš ï¸ Error al generar el movimiento Nequi.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov, "ðŸ“„ Movimiento generado")
                limpiar_sesion_preservando_flags()
        # --- BRE-B ---
        elif tipo == "comprobante4":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "ðŸ”‘ Ingresa la llave (debe iniciar con @):",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.startswith("@"):
                    await update.message.reply_text(
                        "âš ï¸ La llave debe iniciar con @. Ejemplo: @miusuario",
                        parse_mode='Markdown'
                    )
                    return
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "ðŸ¦ Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )
            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "ðŸ“± Ingresa el nÃºmero de envÃ­o:",
                    parse_mode='Markdown'
                )
            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "âš ï¸ El nÃºmero debe contener solo dÃ­gitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "ðŸ’° Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "âš ï¸ El valor debe ser numÃ©rico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor estÃ© guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ el valor. Por favor, intenta de nuevo.",
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
                        "âš ï¸ Error al generar el comprobante BRE-B.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "âœ… Comprobante BRE-B generado"):
                    # Movimiento negativo BRE-B (la ofuscaciÃ³n se aplica en utils.py)
                    data_mov2 = {
                        "nombre": data["nombre"],
                        "valor": -abs(data["valor"])
                    }
                    output_path_mov2 = generar_comprobante(data_mov2, COMPROBANTE_MOVIMIENTO2_CONFIG)
                    if output_path_mov2 is None:
                        await update.message.reply_text(
                            "âš ï¸ Error al generar el movimiento BRE-B.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov2, "ðŸ“„ Movimiento BRE-B generado")
                limpiar_sesion_preservando_flags()
        # --- QR COMPROBANTE ---
        elif tipo == "comprobante_qr":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "ðŸ”‘ Ingresa la llave banco a destino:",
                    parse_mode='Markdown'
                )
            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "ðŸ¦ Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )
            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "ðŸ“± Ingresa el nÃºmero de envÃ­o:",
                    parse_mode='Markdown'
                )
            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "âš ï¸ El nÃºmero debe contener solo dÃ­gitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "ðŸ’° Ingresa el valor:",
                    parse_mode='Markdown'
                )
            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "âš ï¸ El valor debe ser numÃ©rico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor estÃ© guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ el valor. Por favor, intenta de nuevo.",
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
                        "âš ï¸ Error al generar el comprobante QR.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "âœ… Comprobante QR generado"):
                    # Movimiento adicional
                    data_mov_qr = {
                        "nombre": data["nombre"].upper(),
                        "valor": -abs(data["valor"])
                    }
                    output_path_movqr = generar_comprobante(data_mov_qr, COMPROBANTE_MOVIMIENTO3_CONFIG)
                    if output_path_movqr is None:
                        await update.message.reply_text(
                            "âš ï¸ Error al generar el movimiento QR.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_movqr, "ðŸ“„ Movimiento QR generado")
                limpiar_sesion_preservando_flags()
                      # --- LLAVES ---
        elif tipo == "comprobante_llave":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "ðŸ”‘ Ingresa la llave:",
                    parse_mode='Markdown'
                )

            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text(
                    "ðŸ¦ Ingresa el banco de destino:",
                    parse_mode='Markdown'
                )

            elif step == 2:
                data["banco_destino"] = text
                data["step"] = 3
                await update.message.reply_text(
                    "ðŸ“± Ingresa el nÃºmero de envÃ­o:",
                    parse_mode='Markdown'
                )

            elif step == 3:
                if not text.isdigit():
                    await update.message.reply_text(
                        "âš ï¸ El nÃºmero debe contener solo dÃ­gitos.",
                        parse_mode='Markdown'
                    )
                    return
                data["numero_envio"] = text
                data["step"] = 4
                await update.message.reply_text(
                    "ðŸ’° Ingresa el valor:",
                    parse_mode='Markdown'
                )

            elif step == 4 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "âš ï¸ El valor debe ser numÃ©rico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor estÃ© guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ el valor. Por favor, intenta de nuevo.",
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
                        "âš ï¸ Error al generar el comprobante Llave.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return

                if await send_document(output_path, "âœ… Comprobante Llave generado"):
                    # --- Generar tambiÃ©n el movimiento negativo de Llaves ---
                    data_mov_llave = {
                        "nombre": data["nombre"].upper(),
                        "valor": -abs(data["valor"])
                    }
                    output_path_mov_llave = generar_comprobante(data_mov_llave, MOVIMIENTO_LLAVE_CONFIG)
                    if output_path_mov_llave is None:
                        await update.message.reply_text(
                            "âš ï¸ Error al generar el movimiento de Llaves.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov_llave, "ðŸ“„ Movimiento Llaves generado")
                # limpiar sesiÃ³n
                limpiar_sesion_preservando_flags()


                
        # --- BANCOLOMBIA ---
        elif tipo == "bancolombia":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text(
                    "ðŸ’° Ingresa la cantidad a enviar:",
                    parse_mode='Markdown'
                )
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text(
                        "âš ï¸ La cantidad debe ser numÃ©rica.",
                        parse_mode='Markdown'
                    )
                    return
                data["valor"] = int(text)
                data["step"] = 2
                await update.message.reply_text(
                    "ðŸ¦ Ingresa el nÃºmero de cuenta:",
                    parse_mode='Markdown'
                )
            elif step == 2 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, la cuenta ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.isdigit() or len(text) < 11:
                        await update.message.reply_text(
                            "âš ï¸ El nÃºmero de cuenta debe ser **11 dÃ­gitos**.",
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
                # Verificar que la cuenta estÃ© guardada antes de continuar
                if "cuenta" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ la cuenta. Por favor, intenta de nuevo.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                # Si tiene fecha manual, usarla; si no, dejar que generar_comprobante la genere automÃ¡ticamente
                if fecha_manual and "fecha_manual_value" in data:
                    data["fecha"] = data["fecha_manual_value"]
                # Si no hay fecha manual, no establecer data["fecha"] para que generar_comprobante la genere automÃ¡ticamente
                # Si tiene referencia manual, usarla; si no, generar automÃ¡tica con 8 dÃ­gitos
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
                        "âš ï¸ Error al generar el comprobante Bancolombia.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                if await send_document(output_path, "âœ… Comprobante Bancolombia generado"):
                    # Movimiento negativo
                    data_mov_bancol = data.copy()
                    data_mov_bancol["nombre"] = data["nombre"].upper()
                    data_mov_bancol["valor"] = -abs(data["valor"])
                    output_path_mov_bancol = generar_comprobante(data_mov_bancol, BANCOL_MOVIMIENTO_CONFIG)
                    if output_path_mov_bancol is None:
                        await update.message.reply_text(
                            "âš ï¸ Error al generar el movimiento Bancolombia.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov_bancol, "ðŸ“„ Movimiento Bancolombia generado")
                limpiar_sesion_preservando_flags()
        
        # --- QR BC (Bancolombia QR) - ConfiguraciÃ³n original ---
        elif tipo == "qr_bc":
            from utils import generar_comprobante_qr_bc
            if step == 0:
                punto_venta_limpio = text.replace('\n', ' ').replace('\r', ' ').strip()
                while '  ' in punto_venta_limpio:
                    punto_venta_limpio = punto_venta_limpio.replace('  ', ' ')
                data["punto_venta"] = punto_venta_limpio
                data["step"] = 1
                await update.message.reply_text("ðŸ‘¤ Ingresa a quiÃ©n envÃ­as:")
            elif step == 1:
                enviado_a_limpio = text.replace('\n', ' ').replace('\r', ' ').strip()
                while '  ' in enviado_a_limpio:
                    enviado_a_limpio = enviado_a_limpio.replace('  ', ' ')
                data["enviado_a"] = enviado_a_limpio
                data["step"] = 2
                await update.message.reply_text("ðŸ’° Ingresa la cantidad:")
            elif step == 2:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("âš ï¸ La cantidad debe ser numÃ©rica.")
                    return
                data["cantidad"] = int(text)
                data["step"] = 3
                await update.message.reply_text("ðŸ”¢ Ingresa los Ãºltimos 4 dÃ­gitos de la cuenta:")
            elif step == 3:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("âš ï¸ Deben ser exactamente 4 dÃ­gitos.")
                    return
                data["ultimos_4"] = text
                try:
                    output_path = generar_comprobante_qr_bc(
                        data["punto_venta"],
                        data["enviado_a"],
                        data["cantidad"],
                        data["ultimos_4"]
                    )
                    if output_path and await send_document(output_path, "âœ… Comprobante QR BC generado"):
                        # Generar movimiento QR BC usando qr.jpg
                        try:
                            data_mov_qr_bc = {
                                "valor": -abs(data["cantidad"])
                            }
                            output_path_mov_qr_bc = generar_movimiento_qr_bc(data_mov_qr_bc, MOVIMIENTO_QR_BC_CONFIG)
                            if output_path_mov_qr_bc:
                                await send_document(output_path_mov_qr_bc, "ðŸ“„ Movimiento QR BC generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento QR BC: {str(e_mov)}")
                    else:
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante QR BC.")
                except Exception as e:
                    logger.error(f"Error generando QR BC: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante QR BC.")
                # Preservar flags antes de eliminar sesiÃ³n
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- BC a Nequi (configuraciÃ³n original) ---
        elif tipo == "bc_nequi":
            from utils import generar_comprobante_bc_nequi, generar_movimientos_bc_nequi
            if step == 0:
                if not text.isdigit() or len(text) != 10:
                    await update.message.reply_text("âš ï¸ El nÃºmero debe tener exactamente 10 dÃ­gitos.")
                    return
                data["numero"] = text
                data["step"] = 1
                await update.message.reply_text("ðŸ’° Ingresa el valor:")
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("âš ï¸ El valor debe ser numÃ©rico.")
                    return
                data["valor"] = text
                # Generar directamente sin pedir nombre (configuraciÃ³n original)
                try:
                    output_path = generar_comprobante_bc_nequi(
                        data["numero"],
                        data["valor"],
                        ""  # Sin nombre
                    )
                    if output_path:
                        await send_document(output_path, "âœ… Comprobante BC a Nequi generado")
                        # Generar movimiento siempre
                        try:
                            cuenta_ahorros = f"Ahorros *{data['numero'][-4:]}"
                            output_mov = generar_movimientos_bc_nequi(cuenta_ahorros, data["valor"])
                            if output_mov:
                                await send_document(output_mov, "ðŸ“„ Movimiento BC a Nequi generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento BC a Nequi: {str(e_mov)}")
                    else:
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a Nequi.")
                except Exception as e:
                    logger.error(f"Error generando BC a Nequi: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a Nequi.")
                # Preservar flags antes de eliminar sesiÃ³n
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- BC a BC (Bancolombia a Bancolombia) - Usa configuraciÃ³n de Ahorros (bc_a_bc.png) ---
        elif tipo == "bc_bc":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("ðŸ¦ Ingresa el nÃºmero de cuenta:")
            elif step == 1:
                # Validar que tenga 11 dÃ­gitos
                digitos = "".join(ch for ch in text if ch.isdigit())
                if len(digitos) != 11:
                    await update.message.reply_text("âš ï¸ El nÃºmero de cuenta debe tener exactamente 11 dÃ­gitos.\nEjemplo: 12345678912")
                    return
                data["numero_cuenta"] = digitos
                data["step"] = 2
                await update.message.reply_text("ðŸ’° Ingresa el valor:")
            elif step == 2:
                valor_limpio = text.replace(".", "").replace(",", "").replace(" ", "")
                if not valor_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ El valor debe ser numÃ©rico.")
                    return
                valor = int(valor_limpio)
                if valor < 1000:
                    await update.message.reply_text("âš ï¸ El valor mÃ­nimo es $1,000. Intenta de nuevo.")
                    return
                data["valor"] = valor
                data["step"] = 3
                await update.message.reply_text("ðŸ’¸ Â¿Deseas colocar costo de transferencia?\n\nResponde: sÃ­ o no")
            elif step == 3:
                respuesta = text.lower().strip()
                if respuesta in ["sÃ­", "si", "yes", "s", "y"]:
                    data["step"] = 4
                    await update.message.reply_text("ðŸ’° Ingresa el costo de transferencia:\n\nEjemplo: 50, 1000, etc.")
                elif respuesta in ["no", "n"]:
                    data["costo_transferencia"] = 0
                    data["step"] = 5
                    await update.message.reply_text("ðŸ”¢ Â¿Deseas colocar referencia de transferencia?\n\nResponde: sÃ­ o no")
                else:
                    await update.message.reply_text("âš ï¸ Por favor responde: sÃ­ o no")
            elif step == 4:
                costo_limpio = text.replace(".", "").replace(",", "").replace(" ", "").replace("$", "")
                if not costo_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ El costo debe ser numÃ©rico.")
                    return
                costo = int(costo_limpio)
                data["costo_transferencia"] = costo
                data["step"] = 5
                await update.message.reply_text("ðŸ”¢ Â¿Deseas colocar referencia de transferencia?\n\nResponde: sÃ­ o no")
            elif step == 5:
                respuesta = text.lower().strip()
                if respuesta in ["sÃ­", "si", "yes", "s", "y"]:
                    data["step"] = 6
                    await update.message.reply_text("ðŸ”¢ Ingresa los 4 dÃ­gitos de la referencia:\n\nEjemplo: 7423 (se agregarÃ¡ * automÃ¡ticamente)")
                elif respuesta in ["no", "n"]:
                    # Generar referencia aleatoria automÃ¡ticamente (4 dÃ­gitos)
                    referencia_aleatoria = "".join([str(random.randint(0, 9)) for _ in range(4)])
                    data["referencia_transferencia"] = referencia_aleatoria
                    # Generar comprobante directamente
                    try:
                        output_path = generar_comprobante_ahorros(data, COMPROBANTE_AHORROS_CONFIG)
                        if output_path and await send_document(output_path, "âœ… Comprobante BC a BC generado"):
                            # Generar movimiento BC a BC usando ahorros.jpg
                            try:
                                data_mov_ahorros = {
                                    "valor": -abs(data["valor"])
                                }
                                output_path_mov_ahorros = generar_movimiento_ahorros(data_mov_ahorros, MOVIMIENTO_AHORROS_CONFIG)
                                if output_path_mov_ahorros:
                                    await send_document(output_path_mov_ahorros, "ðŸ“„ Movimiento BC a BC generado")
                            except Exception as e_mov:
                                logger.error(f"Error generando movimiento BC a BC: {str(e_mov)}")
                        else:
                            await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a BC.")
                    except Exception as e:
                        logger.error(f"Error generando BC a BC: {str(e)}")
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a BC.")
                    # Preservar flags antes de eliminar sesiÃ³n
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
                    await update.message.reply_text("âš ï¸ Por favor responde: sÃ­ o no")
            elif step == 6:
                # Validar que sean exactamente 4 dÃ­gitos
                digitos = "".join(ch for ch in text if ch.isdigit())
                if len(digitos) != 4:
                    await update.message.reply_text("âš ï¸ La referencia debe tener exactamente 4 dÃ­gitos.\n\nEjemplo: 7423")
                    return
                data["referencia_transferencia"] = digitos
                try:
                    # Usar COMPROBANTE_AHORROS_CONFIG (bc_a_bc.png) para BC a BC
                    output_path = generar_comprobante_ahorros(data, COMPROBANTE_AHORROS_CONFIG)
                    if output_path and await send_document(output_path, "âœ… Comprobante BC a BC generado"):
                        # Generar movimiento BC a BC usando ahorros.jpg
                        try:
                            data_mov_ahorros = {
                                "valor": -abs(data["valor"])
                            }
                            output_path_mov_ahorros = generar_movimiento_ahorros(data_mov_ahorros, MOVIMIENTO_AHORROS_CONFIG)
                            if output_path_mov_ahorros:
                                await send_document(output_path_mov_ahorros, "ðŸ“„ Movimiento BC a BC generado")
                        except Exception as e_mov:
                            logger.error(f"Error generando movimiento BC a BC: {str(e_mov)}")
                    else:
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a BC.")
                except Exception as e:
                    logger.error(f"Error generando BC a BC: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante BC a BC.")
                # Preservar flags antes de eliminar sesiÃ³n
                fecha_flag = user_data_store.get(user_id, {}).get("fecha_manual", False)
                referencia_flag = user_data_store.get(user_id, {}).get("referencia_manual", False)
                del user_data_store[user_id]
                if fecha_flag or referencia_flag:
                    user_data_store[user_id] = {}
                    if fecha_flag:
                        user_data_store[user_id]["fecha_manual"] = True
                    if referencia_flag:
                        user_data_store[user_id]["referencia_manual"] = True
        
        # --- DaviPlata (configuraciÃ³n original, solo con color #333333 y fuente Manrope-Bold) ---
        elif tipo == "daviplata":
            from utils import generar_comprobante_daviplata
            if step == 0:
                if not text.isdigit() or len(text) < 10:
                    await update.message.reply_text("âš ï¸ El nÃºmero DaviPlata debe tener mÃ­nimo 10 dÃ­gitos (puedes usar 10, 11, 12, 14, etc.).")
                    return
                data["numero_daviplata"] = text
                data["step"] = 1
                await update.message.reply_text("ðŸ’° Ingresa la cantidad:")
            elif step == 1:
                # Remover puntos y comas si el usuario las incluye
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ La cantidad debe ser solo nÃºmeros, sin puntos ni comas. Ejemplo: 32000")
                    return
                data["valor"] = int(valor_limpio)
                data["step"] = 2
                await update.message.reply_text("ðŸ”¢ Ingresa los Ãºltimos 4 dÃ­gitos de tu cuenta:")
            elif step == 2:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("âš ï¸ Deben ser exactamente 4 dÃ­gitos.")
                    return
                data["ultimos_4"] = text
                try:
                    output_path = generar_comprobante_daviplata(
                        data["numero_daviplata"],
                        data["ultimos_4"],
                        data["valor"]
                    )
                    if output_path and await send_document(output_path, "âœ… Comprobante DaviPlata generado"):
                        pass
                    else:
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante DaviPlata.")
                except Exception as e:
                    logger.error(f"Error generando DaviPlata: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante DaviPlata.")
                # Preservar flags antes de eliminar sesiÃ³n
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
                await update.message.reply_text("ðŸ’° Ingresa la cantidad:")
            elif step == 1:
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ La cantidad debe ser solo nÃºmeros. Ejemplo: 32000")
                    return
                data["cantidad"] = int(valor_limpio)
                data["step"] = 2
                await update.message.reply_text("ðŸ“± Ingresa los 10 dÃ­gitos de quien envÃ­a:")
            elif step == 2:
                if not text.isdigit() or len(text) != 10:
                    await update.message.reply_text("âš ï¸ Deben ser exactamente 10 dÃ­gitos.")
                    return
                data["numero_envio"] = text
                data["desde"] = f"DaviPlata - ******{text[-4:]}"
                data["step"] = 3
                # Mostrar botones rÃ¡pidos para costo
                keyboard = [
                    ["âœ… SÃ­", "âŒ No"]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text(
                    "ðŸ’¸ Â¿Deseas colocar costo a la transacciÃ³n?",
                    reply_markup=reply_markup
                )
            elif step == 3:
                respuesta = text.lower().strip()
                if respuesta in ["âœ… sÃ­", "âœ… si", "sÃ­", "si", "yes", "s", "y"]:
                    data["step"] = 4
                    await update.message.reply_text(
                        "ðŸ’° Ingresa el costo de la transacciÃ³n:",
                        reply_markup=ReplyKeyboardRemove()
                    )
                elif respuesta in ["âŒ no", "no", "n"]:
                    data["costo"] = "$ 0"
                    # Continuar a generar el comprobante
                    await generar_qr_daviplata_final(update, data, fecha_manual, send_document, limpiar_sesion_preservando_flags)
                else:
                    await update.message.reply_text("âš ï¸ Por favor responde: SÃ­ o No")
            elif step == 4 or data.get("fecha_recibida", False):
                if not data.get("fecha_recibida", False):
                    costo_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                    if not costo_limpio.isdigit():
                        await update.message.reply_text("âš ï¸ El costo debe ser numÃ©rico. Ejemplo: 500")
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
                await update.message.reply_text("ðŸ”‘ Ingresa la llave a enviar:")
            elif step == 1:
                data["llave"] = text
                data["step"] = 2
                await update.message.reply_text("ðŸ’° Ingresa la cantidad a enviar:")
            elif step == 2:
                # Remover puntos y comas si el usuario las incluye
                valor_limpio = text.replace(".", "").replace(",", "").replace("$", "").strip()
                if not valor_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ La cantidad debe ser solo nÃºmeros, sin puntos ni comas. Ejemplo: 32000")
                    return
                data["valor"] = int(valor_limpio)
                data["step"] = 3
                await update.message.reply_text("ðŸ”¢ Ingresa los Ãºltimos 4 dÃ­gitos de tu cuenta:")
            elif step == 3:
                if not text.isdigit() or len(text) != 4:
                    await update.message.reply_text("âš ï¸ Deben ser exactamente 4 dÃ­gitos.")
                    return
                data["ultimos_4"] = text
                # Generar "desde" con formato DaviPlata - ******ultimos_4
                data["desde"] = f"DaviPlata - ******{text}"
                data["step"] = 4
                await update.message.reply_text("ðŸ¦ Selecciona el banco:\n\nâ€¢ Nequi\nâ€¢ Dale\nâ€¢ Davivienda\n\nO escribe el nombre del banco:")
            elif step == 4 or data.get("fecha_recibida", False):
                if not data.get("fecha_recibida", False):
                    data["entidad_destino"] = text
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que todos los datos estÃ©n guardados antes de continuar
                if "valor" not in data or "nombre" not in data or "llave" not in data or "entidad_destino" not in data or "desde" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: Faltan datos. Por favor, intenta de nuevo.",
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
                            "âš ï¸ Error al generar el comprobante Llaves DaviPlata.",
                            parse_mode='Markdown'
                        )
                        limpiar_sesion_preservando_flags()
                        return
                    # Enviar como foto para que se muestre directamente en el chat
                    try:
                        if output_path and os.path.exists(output_path):
                            with open(output_path, "rb") as f:
                                await update.message.reply_photo(photo=f, caption="âœ… Comprobante Llaves DaviPlata generado")
                            os.remove(output_path)
                            logger.info(f"Foto enviada exitosamente: {output_path}")
                        else:
                            await update.message.reply_text("âš ï¸ Error al enviar el comprobante Llaves DaviPlata.")
                    except Exception as e:
                        logger.error(f"Error enviando foto Llaves DaviPlata: {str(e)}")
                        await update.message.reply_text("âš ï¸ Error al enviar el comprobante Llaves DaviPlata.")
                except Exception as e:
                    logger.error(f"Error generando Llaves DaviPlata: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante Llaves DaviPlata.")
                # Preservar flags antes de eliminar sesiÃ³n
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
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("ðŸ’° Ingresa el valor:")
            elif step == 1 or data.get("fecha_recibida", False):
                # Si viene de fecha_recibida, el valor ya estÃ¡ en data
                if not data.get("fecha_recibida", False):
                    if not text.replace("-", "", 1).isdigit():
                        await update.message.reply_text(
                            "âš ï¸ El valor debe ser numÃ©rico.",
                            parse_mode='Markdown'
                        )
                        return
                    data["valor"] = int(text)
                    # Verificar si necesita pedir fecha manual (para TODOS)
                    if await verificar_fecha_manual():
                        return
                # Verificar que el valor estÃ© guardado antes de continuar
                if "valor" not in data:
                    await update.message.reply_text(
                        "âš ï¸ Error: No se encontrÃ³ el valor. Por favor, intenta de nuevo.",
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
                        "âš ï¸ Error al generar el comprobante NQ QR Normal.",
                        parse_mode='Markdown'
                    )
                    limpiar_sesion_preservando_flags()
                    return
                
                # Enviar comprobante como documento
                if await send_document(output_path, "âœ… Comprobante NQ QR Normal generado"):
                    # Generar movimiento negativo
                    data_mov = data.copy()
                    data_mov["nombre"] = data["nombre"].upper()
                    data_mov["valor"] = -abs(data["valor"])
                    output_path_mov = generar_comprobante(data_mov, MOVIMIENTO_NQ_QR_NORMAL_CONFIG)
                    if output_path_mov is None:
                        await update.message.reply_text(
                            "âš ï¸ Error al generar el movimiento NQ QR Normal.",
                            parse_mode='Markdown'
                        )
                    else:
                        await send_document(output_path_mov, "ðŸ“„ Movimiento NQ QR Normal generado")
                
                limpiar_sesion_preservando_flags()
        
        # --- COMPROBANTE ANULADO ---
        elif tipo == "comprobante_anulado":
            if step == 0:
                # Limpiar input del usuario (quitar saltos de lÃ­nea y espacios extra)
                text = text.replace('\n', ' ').replace('\r', ' ').strip()
                text = ' '.join(text.split())
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("ðŸ’° Ingresa el valor:")
            elif step == 1:
                valor_limpio = text.replace(".", "").replace(",", "").replace(" ", "")
                if not valor_limpio.isdigit():
                    await update.message.reply_text("âš ï¸ El valor debe ser numÃ©rico.")
                    return
                valor = int(valor_limpio)
                if valor < 1000:
                    await update.message.reply_text("âš ï¸ El valor mÃ­nimo es $1,000. Intenta de nuevo.")
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
                    if output_path and await send_document(output_path, "ðŸš« ANULADO"):
                        pass
                    else:
                        await update.message.reply_text("âš ï¸ Error al generar el comprobante anulado.")
                except Exception as e:
                    logger.error(f"Error generando comprobante anulado: {str(e)}")
                    await update.message.reply_text("âš ï¸ Error al generar el comprobante anulado.")
                # Preservar flags antes de eliminar sesiÃ³n
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
            "âš ï¸ Error al procesar los datos. Intenta de nuevo.",
            parse_mode='Markdown'
        )

# ------------------------------------------------------------------
# ADMIN COMMANDS
# ------------------------------------------------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    help_text = (
        "ðŸ“œ **Comandos de Administrador**\n\n"
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
        "/stats - Muestra estadÃ­sticas del bot"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    global maintenance_mode
    maintenance_mode = True
    await update.message.reply_text(
        "ðŸ”§ Modo mantenimiento activado. Solo admins pueden usar el bot.",
        parse_mode='Markdown'
    )

async def off_maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    global maintenance_mode
    maintenance_mode = False
    await update.message.reply_text(
        "âœ… Modo mantenimiento desactivado.",
        parse_mode='Markdown'
    )

async def agregar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "â“ Uso: /agregar <id_usuario>",
                parse_mode='Markdown'
            )
            return
        target_user_id = int(context.args[0])
        if target_user_id not in authorized_users:
            authorized_users.append(target_user_id)
            auth_system.add_user(target_user_id)
            save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"âœ… Usuario {target_user_id} autorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"âš ï¸ El usuario {target_user_id} ya estÃ¡ autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "âš ï¸ ID de usuario invÃ¡lido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en agregar_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al agregar usuario.",
            parse_mode='Markdown'
        )

async def eliminar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "â“ Uso: /eliminar <id_usuario>",
                parse_mode='Markdown'
            )
            return
        target_user_id = int(context.args[0])
        if auth_system.remove_user(target_user_id):
            if target_user_id in authorized_users:
                authorized_users.remove(target_user_id)
                save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"âœ… Usuario {target_user_id} desautorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"âš ï¸ Usuario {target_user_id} no estaba autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "âš ï¸ ID de usuario invÃ¡lido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en eliminar_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al eliminar usuario.",
            parse_mode='Markdown'
        )

async def agregar_grupo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        if not context.args:
            await update.message.reply_text(
                "â“ Uso: /agregargrupo <id_grupo>",
                parse_mode='Markdown'
            )
            return
        group_id = int(context.args[0])
        if group_id not in authorized_groups:
            authorized_groups.append(group_id)
            auth_system.add_group(group_id)
            save_data(authorized_users, authorized_groups, logs)
            await update.message.reply_text(
                f"âœ… Grupo {group_id} autorizado.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"âš ï¸ El grupo {group_id} ya estÃ¡ autorizado.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "âš ï¸ ID de grupo invÃ¡lido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en agregar_grupo_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al agregar grupo.",
            parse_mode='Markdown'
        )

async def gratis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        auth_system.set_gratis_mode(True)
        await update.message.reply_text(
            "âœ… Modo GRATIS activado: Todos pueden usar el bot.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en gratis_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al activar modo gratis.",
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
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        
        # Si es un grupo, deshabilitar el bot en ese grupo (solo admin)
        if chat_type in ['group', 'supergroup']:
            global disabled_groups
            disabled_groups.add(chat_id)
            await update.message.reply_text(
                "ðŸ”’ Bot Apagado\n\n"
                "ðŸ’Ž Compra tu acceso V.I.P para disfrutar los beneficios\n"
                f"ðŸ›’ Ãšnico vendedor: {OWNER}"
            )
            logger.info(f"Bot deshabilitado en grupo {chat_id} por admin {user_id}")
            return
        
        # Si es privado, desactivar el modo gratis
        auth_system.set_gratis_mode(False)
        await update.message.reply_text(
            "âœ… Modo OFF activado: Solo usuarios autorizados.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en off_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al ejecutar comando /off.",
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
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        
        # Solo funciona en grupos
        if chat_type in ['group', 'supergroup']:
            global disabled_groups
            if chat_id in disabled_groups:
                disabled_groups.remove(chat_id)
                await update.message.reply_text(
                    "ðŸ”” Bot reactivado en este grupo.",
                    parse_mode='Markdown'
                )
                logger.info(f"Bot reactivado en grupo {chat_id} por usuario {user_id}")
            else:
                await update.message.reply_text(
                    "â„¹ï¸ El bot ya estÃ¡ activo en este grupo.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "âš ï¸ Este comando solo funciona en grupos.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en on_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al ejecutar comando /on.",
            parse_mode='Markdown'
        )

async def ver_grupos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if authorized_groups:
            groups_list = "\n".join(f"â€¢ {gid}" for gid in authorized_groups)
            await update.message.reply_text(
                f"ðŸ  Grupos autorizados:\n{groups_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "âŒ No hay grupos autorizados.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en ver_grupos_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al mostrar grupos.",
            parse_mode='Markdown'
        )

async def ver_usuarios_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if authorized_users:
            users_list = "\n".join(f"â€¢ {uid}" for uid in authorized_users)
            await update.message.reply_text(
                f"ðŸ‘¤ Usuarios autorizados:\n{users_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "âŒ No hay usuarios autorizados.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en ver_usuarios_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al mostrar usuarios.",
            parse_mode='Markdown'
        )

async def registros_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if logs:
            logs_list = "\n".join(
                f"â€¢ ID: {log['user_id']} (@{log['username']} / {log['first_name']}) - {log['command']} ({log['timestamp']})"
                for log in logs
            )
            await update.message.reply_text(
                f"ðŸ“‹ Registros de uso:\n{logs_list}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "âŒ No hay registros de uso.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error en registros_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al mostrar registros.",
            parse_mode='Markdown'
        )

async def eliminar_registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        if not context.args:
            await update.message.reply_text(
                "â“ Uso: /eliminarregistro <id_usuario>",
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
                f"âœ… Registros del usuario {target_user_id} eliminados.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"âš ï¸ No se encontraron registros para el usuario {target_user_id}.",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text(
            "âš ï¸ ID de usuario invÃ¡lido.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en eliminar_registro_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al eliminar registros.",
            parse_mode='Markdown'
        )

async def reiniciar_registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_system.is_admin(user_id):
        await update.message.reply_text(
            "ðŸš« Solo los administradores pueden usar este comando.",
            parse_mode='Markdown'
        )
        return
    try:
        global logs
        logs = []
        save_data(authorized_users, authorized_groups, logs)
        await update.message.reply_text(
            "âœ… Todos los registros han sido eliminados.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en reiniciar_registro_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al reiniciar registros.",
            parse_mode='Markdown'
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        if not auth_system.is_admin(user_id):
            await update.message.reply_text(
                "ðŸš« Solo los administradores pueden usar este comando.",
                parse_mode='Markdown'
            )
            return
        stats = auth_system.get_stats()
        message = (
            f"ðŸ“Š **EstadÃ­sticas del Bot**\n\n"
            f"ðŸ‘¥ Usuarios autorizados: {stats['total_authorized']}\n"
            f"ðŸ†“ Modo gratis: {'Activado' if stats['gratis_mode'] else 'Desactivado'}\n"
            f"ðŸ“± Grupo permitido: {stats['allowed_group']}\n"
            f"ðŸ”§ Modo mantenimiento: {'Activado' if maintenance_mode else 'Desactivado'}\n\n"
        )
        if authorized_users:
            message += "ðŸ‘¤ Usuarios autorizados:\n" + "\n".join(f" â€¢ {uid}" for uid in authorized_users)
        else:
            message += "âŒ No hay usuarios autorizados."
        if authorized_groups:
            message += "\n\nðŸ  Grupos autorizados:\n" + "\n".join(f" â€¢ {gid}" for gid in authorized_groups)
        else:
            message += "\n\nâŒ No hay grupos autorizados."
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en stats_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al obtener estadÃ­sticas.",
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
            "âœ… Fecha manual activada\n\n"
            "ðŸ“ Formato: 06 de diciembre de 2025 a las 12:00 a.m.\n\n"
            "ðŸ”„ /Nequiglitch para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en fmanual_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al activar fecha manual."
        )

async def fdesactive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Desactiva el modo de fecha manual"""
    user_id = update.effective_user.id
    try:
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]["fecha_manual"] = False
        await update.message.reply_text(
            "âœ… Modo fecha automÃ¡tica activado\n\n"
            "ðŸ“… La fecha se generarÃ¡ automÃ¡ticamente con la fecha y hora actual.\n\n"
            "ðŸ”„ Pulsa /Nequiglitch nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en fdesactive_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al desactivar fecha manual.",
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
            "âœ… Modo referencia manual activado\n\n"
            "ðŸ”¢ Cuando generes un comprobante de Nequi, se te pedirÃ¡ que ingreses la referencia manualmente.\n\n"
            "ðŸ“ Solo debes colocar los 8 dÃ­gitos. La M se colocarÃ¡ automÃ¡ticamente.\n\n"
            "ðŸ’¡ Para desactivar y usar referencia automÃ¡tica, usa /refedesactiva\n\n"
            "ðŸ”„ Pulsa /Nequiglitch nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en refe_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al activar referencia manual.",
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
            "âœ… Modo referencia automÃ¡tica activado\n\n"
            "ðŸ”¢ La referencia se generarÃ¡ automÃ¡ticamente con formato M + 8 dÃ­gitos aleatorios.\n\n"
            "ðŸ”„ Pulsa /Nequiglitch nuevamente para comenzar"
        )
    except Exception as e:
        logger.error(f"Error en refedesactiva_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al desactivar referencia manual.",
            parse_mode='Markdown'
        )

async def masinf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra informaciÃ³n detallada sobre fechas y referencias manuales"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    try:
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            return
        
        mensaje_info = (
            "âš™ï¸ **Comandos:**\n\n"
            "ðŸ“… **Fechas:**\n"
            "â€¢ /fmanual - Activar\n"
            "â€¢ /fdesactive - Desactivar\n"
            "Formato: `06 de diciembre de 2025 a las 12:00 a.m.`\n\n"
            "ðŸ”¢ **Referencias (solo Nequi):**\n"
            "â€¢ /refe - Activar\n"
            "â€¢ /refedesactiva - Desactivar\n"
            "Formato: 8 dÃ­gitos (ej: `12345678` â†’ `M12345678`)"
        )
        
        await update.message.reply_text(
            mensaje_info,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en masinf_command: {str(e)}")
        await update.message.reply_text(
            "âš ï¸ Error al mostrar informaciÃ³n.",
            parse_mode='Markdown'
        )

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
# Token desde variable de entorno
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def main() -> None:
    try:
        logger.info("Inicializando la aplicaciÃ³n del bot...")
        
        if not BOT_TOKEN:
            logger.error("âŒ TELEGRAM_BOT_TOKEN no estÃ¡ configurado en las variables de entorno")
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado. ConfigÃºralo en el archivo .env")
        
        bot_token = BOT_TOKEN
        app = Application.builder().token(bot_token).job_queue(None).build()
        
        # Registrar manejadores
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("nequiglitch", nequiglitch_command))
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
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Iniciando el polling del bot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error fatal en main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
