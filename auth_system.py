import json
import os
import logging
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)

class AuthSystem:
    def __init__(self, admin_ids: List[int] = [8058901135], allowed_group: int = -1003349066708):
        if not isinstance(admin_ids, (list, tuple)):
            admin_ids = [admin_ids]
        if not all(isinstance(id, int) for id in admin_ids):
            raise ValueError("Todos los admin_ids deben ser enteros")
        self.admin_ids = set(admin_ids)
        self.allowed_groups: Set[int] = {allowed_group}
        self.authorized_users: Set[int] = set()
        self.gratis_mode = False
        self.logger = logging.getLogger(__name__)
        
        # Archivos para persistencia
        self.users_file = "users.json"
        self.groups_file = "groups.json"
        self.settings_file = "settings.json"
        
        self.load_data()

    def load_data(self) -> None:
        """Carga datos de usuarios, grupos y configuraciones desde archivos JSON."""
        try:
            # Cargar usuarios autorizados
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.authorized_users = set(data.get('users', []))
                    self.logger.info(f"Cargados {len(self.authorized_users)} usuarios autorizados desde {self.users_file}")
            else:
                self.logger.warning(f"Archivo {self.users_file} no encontrado, usando lista vacía")

            # Cargar grupos autorizados
            # PRIMERO agregar grupos hardcodeados (siempre deben estar)
            try:
                from main import ALLOWED_GROUPS_HARDCODED
                for group_id in ALLOWED_GROUPS_HARDCODED:
                    self.allowed_groups.add(group_id)
                self.logger.info(f"Grupos hardcodeados agregados: {ALLOWED_GROUPS_HARDCODED}")
            except:
                pass
            
            # Luego cargar grupos adicionales desde JSON
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    grupos_json = set(data.get('groups', []))
                    self.allowed_groups.update(grupos_json)  # Agregar sin sobrescribir
                    if not self.allowed_groups:
                        self.allowed_groups = {-1003349066708}  # Valor por defecto
                    self.logger.info(f"Cargados {len(grupos_json)} grupos adicionales desde {self.groups_file}. Total: {len(self.allowed_groups)} grupos")
            else:
                self.logger.warning(f"Archivo {self.groups_file} no encontrado, usando grupos hardcodeados")

            # Cargar configuraciones (gratis_mode)
            # Prioridad: 1) Variable de entorno, 2) Archivo settings.json, 3) Default False
            env_gratis = os.getenv('GRATIS_MODE', '').lower()
            if env_gratis in ['true', '1', 'yes']:
                self.gratis_mode = True
                self.logger.info(f"gratis_mode=True desde variable de entorno GRATIS_MODE")
            elif env_gratis in ['false', '0', 'no']:
                self.gratis_mode = False
                self.logger.info(f"gratis_mode=False desde variable de entorno GRATIS_MODE")
            elif os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.gratis_mode = data.get('gratis_mode', False)
                    self.logger.info(f"Cargado gratis_mode={self.gratis_mode} desde {self.settings_file}")
            else:
                self.gratis_mode = False
                self.logger.warning(f"gratis_mode no configurado, usando False por defecto")

        except json.JSONDecodeError as e:
            self.logger.error(f"Error de formato en archivos JSON: {e}")
            self.authorized_users = set()
            self.allowed_groups = {-1003349066708}
            self.gratis_mode = False
        except Exception as e:
            self.logger.error(f"Error inesperado cargando datos: {e}")
            self.authorized_users = set()
            self.allowed_groups = {-1003349066708}
            self.gratis_mode = False

    def save_data(self) -> None:
        """Guarda datos de usuarios, grupos y configuraciones en archivos JSON."""
        try:
            # Guardar usuarios autorizados
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({'users': list(self.authorized_users)}, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Usuarios autorizados guardados en {self.users_file}")

            # Guardar grupos autorizados
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump({'groups': list(self.allowed_groups)}, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Grupos autorizados guardados en {self.groups_file}")

            # Guardar configuraciones (gratis_mode)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump({'gratis_mode': self.gratis_mode}, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuraciones guardadas en {self.settings_file}")

        except Exception as e:
            self.logger.error(f"Error guardando datos: {e}")

    def is_admin(self, user_id: int) -> bool:
        """Verifica si un usuario es administrador."""
        result = user_id in self.admin_ids
        self.logger.info(f"Verificando si user_id {user_id} es admin: {result}")
        return result

    def is_authorized(self, user_id: int) -> bool:
        """Verifica si un usuario está autorizado."""
        result = user_id in self.authorized_users
        self.logger.info(f"Verificando si user_id {user_id} está autorizado: {result}")
        return result

    def can_use_bot(self, user_id: int, chat_id: int, is_private: Optional[bool] = None) -> bool:
        """Verifica si un usuario puede usar el bot."""
        user_id = int(user_id)
        chat_id = int(chat_id)
        self.logger.info(f"Verificando acceso para user_id: {user_id}, chat_id: {chat_id}, is_private: {is_private}")

        if self.is_admin(user_id):
            self.logger.info(f"Acceso permitido para user_id {user_id} porque es administrador")
            return True

        if self.gratis_mode:
            self.logger.info(f"Acceso permitido para user_id {user_id} porque gratis_mode está activo")
            return True

        if is_private is None:
            is_private = chat_id > 0
        if is_private:
            authorized = self.is_authorized(user_id)
            if authorized:
                self.logger.info(f"Acceso permitido para user_id {user_id} en chat privado porque está autorizado")
            else:
                self.logger.warning(f"Acceso denegado para user_id {user_id} en chat privado: no autorizado")
            return authorized

        # Grupos hardcodeados siempre permitidos (importar desde main)
        try:
            from main import ALLOWED_GROUPS_HARDCODED
            if chat_id in ALLOWED_GROUPS_HARDCODED:
                self.logger.info(f"Acceso permitido para chat_id {chat_id} porque está en grupos hardcodeados")
                return True
        except:
            pass
        
        if self.allowed_groups:
            allowed = chat_id in self.allowed_groups
            if allowed:
                self.logger.info(f"Acceso permitido para chat_id {chat_id} porque está en grupos permitidos")
            else:
                self.logger.warning(f"Acceso denegado para chat_id {chat_id}: no está en grupos permitidos")
            return allowed

        self.logger.info(f"Acceso permitido por defecto para user_id {user_id}, chat_id {chat_id}")
        return True

    def add_user(self, user_id: int) -> bool:
        """Agrega un usuario a la lista de autorizados."""
        try:
            self.authorized_users.add(user_id)
            self.save_data()
            self.logger.info(f"Usuario {user_id} agregado a lista autorizada")
            return True
        except Exception as e:
            self.logger.error(f"Error agregando usuario {user_id}: {e}")
            return False

    def remove_user(self, user_id: int) -> bool:
        """Elimina un usuario de la lista de autorizados."""
        try:
            if user_id in self.authorized_users:
                self.authorized_users.remove(user_id)
                self.save_data()
                self.logger.info(f"Usuario {user_id} eliminado de lista autorizada")
                return True
            self.logger.warning(f"Usuario {user_id} no estaba en la lista autorizada")
            return False
        except Exception as e:
            self.logger.error(f"Error eliminando usuario {user_id}: {e}")
            return False

    def add_group(self, group_id: int) -> bool:
        """Agrega un grupo a la lista de permitidos."""
        try:
            self.allowed_groups.add(group_id)
            self.save_data()
            self.logger.info(f"Grupo {group_id} agregado a lista permitida")
            return True
        except Exception as e:
            self.logger.error(f"Error agregando grupo {group_id}: {e}")
            return False

    def remove_group(self, group_id: int) -> bool:
        """Elimina un grupo de la lista de permitidos."""
        try:
            if group_id in self.allowed_groups:
                self.allowed_groups.remove(group_id)
                self.save_data()
                self.logger.info(f"Grupo {group_id} eliminado de lista permitida")
                return True
            self.logger.warning(f"Grupo {group_id} no estaba en la lista permitida")
            return False
        except Exception as e:
            self.logger.error(f"Error eliminando grupo {group_id}: {e}")
            return False

    def set_gratis_mode(self, enabled: bool) -> None:
        """Activa o desactiva el modo gratis."""
        try:
            self.gratis_mode = enabled
            self.save_data()
            self.logger.info(f"Modo gratuito {'activado' if enabled else 'desactivado'}")
        except Exception as e:
            self.logger.error(f"Error cambiando modo gratuito: {e}")

    def get_authorized_users(self) -> List[int]:
        """Devuelve la lista de usuarios autorizados."""
        return list(self.authorized_users)

    def get_allowed_groups(self) -> List[int]:
        """Devuelve la lista de grupos permitidos."""
        return list(self.allowed_groups)

    def get_stats(self) -> Dict:
        """Devuelve estadísticas del sistema de autorización."""
        return {
            'total_authorized': len(self.authorized_users),
            'total_allowed_groups': len(self.allowed_groups),
            'gratis_mode': self.gratis_mode,
            'admin_ids': list(self.admin_ids),
            'allowed_groups': list(self.allowed_groups)
        }