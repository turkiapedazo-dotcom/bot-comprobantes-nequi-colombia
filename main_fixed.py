async def nequicol_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando que muestra botones de acceso rápido - Verifica autorización del grupo"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_name = update.effective_user.first_name or update.effective_user.username or "Usuario"
    
    try:
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
        
        # Verificar acceso usando auth_system (incluye modo gratis)
        if not auth_system.can_use_bot(user_id, chat_id, chat_type == 'private'):
            if not auth_system.gratis_mode:
                await update.message.reply_text(
                    f"👋 Querido usuario,\n\n"
                    f"Para usar este bot, únete al grupo de comprobantes totalmente GRATIS:\n\n💎 <a href='{GROUP_INVITE_LINK}'>Unirse al Grupo</a>\n\n"
                    f"Una vez que te unas, podrás usar el bot sin restricciones.",
                    parse_mode='HTML'
                )
            return
        
        # Crear botones de acceso rápido
        keyboard = [
            ["💸 Nequi", "🔄 BRE-B"],
            ["📱 QR Comprobante", "🔑 LLAVES"],
            ["🏦 Nequi a Bancolombia"],
            ["🏦 QR BC", "💳 BC a Nequi"],
            ["🏛️ BC a BC", "🔵 DaviPlata"],
            ["✅ Anulado"],
            ["❌ Cancelar"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        # Mensaje con información de comandos disponibles
        mensaje_comandos = (
            f"👋 Hola {user_name}!\n\n"
            f"💎 Generador de Comprobantes\n"
            f"📌 Selecciona una opción:\n\n"
            f"⚙️ **Comandos de Configuración:**\n"
            f"📅 /fmanual - Activar fecha manual (todos los comprobantes)\n"
            f"📅 /fdesactive - Desactivar fecha manual (usar automática)\n"
            f"🔢 /refe - Activar referencia manual (solo Nequi)\n"
            f"🔢 /refedesactiva - Desactivar referencia manual (usar automática)"
        )
        
        await update.message.reply_text(
            mensaje_comandos,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en nequicol_command: {str(e)}")

