from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import uuid
import locale
import random
import pytz
import logging
import os

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurar idioma español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Primario para Linux/Zeabur
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Colombia.1252')  # Fallback para Windows
    except:
        logger.warning("No se pudo configurar locale, usando formato por defecto")

def draw_text_with_outline(draw, position, text, font, fill, outline_fill, outline_width):
    """Dibuja texto con contorno para mejorar legibilidad."""
    try:
        x, y = position
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_fill)
        draw.text((x, y), text, font=font, fill=fill)
    except Exception as e:
        logger.error(f"Error al dibujar texto con contorno: {str(e)}")
        raise

def draw_text_professional(draw, position, text, font, fill):
    """Dibuja texto con efecto profesional: múltiples capas de sombra suave para profundidad."""
    try:
        x, y = position
        # Múltiples capas de sombra para efecto profesional más pronunciado
        # Sombra 1: muy suave, lejos (gris muy claro) - más desplazada
        shadow1_color = (255, 255, 255)  # Blanco para contraste
        draw.text((x + 3, y + 3), text, font=font, fill=shadow1_color)
        # Sombra 2: suave, media distancia (gris muy claro)
        shadow2_color = (250, 250, 250)
        draw.text((x + 2, y + 2), text, font=font, fill=shadow2_color)
        # Sombra 3: más visible, cerca (gris claro)
        shadow3_color = (240, 240, 240)
        draw.text((x + 1, y + 1), text, font=font, fill=shadow3_color)
        # Sombra 4: intermedia (gris medio-claro)
        shadow4_color = (230, 230, 230)
        draw.text((x + 1, y + 1), text, font=font, fill=shadow4_color)
        # Texto principal encima con el color original
        draw.text((x, y), text, font=font, fill=fill)
    except Exception as e:
        logger.error(f"Error al dibujar texto profesional: {str(e)}")
        raise

def dibujar_valor_movimiento(draw, base_style, valor, font_path, ancho_imagen, decimal_style=None, es_alineacion_derecha=False):
    """Formatea y dibuja valores monetarios para comprobantes de movimiento."""
    try:
        valor_formateado = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        valor_str = f"-$ {valor_formateado}" if valor < 0 else f"$ {valor_formateado}"
        entero, decimal = valor_str[:-3], valor_str[-3:]
        pos_y = base_style["pos"][1]
        
        if es_alineacion_derecha:
            # BRE-B y QR: Alineación derecha especial
            limite_derecho = base_style["pos"][0]
            limite_izquierdo = 120
            margen_derecho = 0  # Sin margen para que llegue al borde
            
            size_entero = base_style["size"]
            size_decimal = int(size_entero * 0.70)
            font_entero = ImageFont.truetype(base_style.get("font", font_path), size_entero)
            font_decimal = ImageFont.truetype(decimal_style.get("font", font_path) if decimal_style else font_path, size_decimal)
            ancho_entero = draw.textlength(entero, font=font_entero)
            ancho_decimal = draw.textlength(decimal, font=font_decimal)
            
            # Alinear a la derecha
            x_decimal = limite_derecho - margen_derecho
            x_entero = x_decimal - ancho_decimal - ancho_entero
            
            if x_entero < limite_izquierdo:
                x_entero = limite_izquierdo
                x_decimal = x_entero + ancho_entero
        else:
            # Otras plantillas: comportamiento original
            limite_izquierdo = 100
            margen_derecho = 20
            limite_derecho = 550
            
            size_entero = base_style["size"]
            size_decimal = int(size_entero * 0.70)
            font_entero = ImageFont.truetype(base_style.get("font", font_path), size_entero)
            font_decimal = ImageFont.truetype(decimal_style.get("font", font_path) if decimal_style else font_path, size_decimal)
            ancho_entero = draw.textlength(entero, font=font_entero)
            ancho_decimal = draw.textlength(decimal, font=font_decimal)
            
            while (ancho_entero + ancho_decimal) > (limite_derecho - limite_izquierdo - margen_derecho) and size_entero > 8:
                size_entero -= 1
                size_decimal = int(size_entero * 0.70)
                font_entero = ImageFont.truetype(base_style.get("font", font_path), size_entero)
                font_decimal = ImageFont.truetype(decimal_style.get("font", font_path) if decimal_style else font_path, size_decimal)
                ancho_entero = draw.textlength(entero, font=font_entero)
                ancho_decimal = draw.textlength(decimal, font=font_decimal)
            
            x_decimal = limite_derecho - margen_derecho
            x_entero = x_decimal - ancho_entero
            if x_entero < limite_izquierdo:
                x_entero = limite_izquierdo
                x_decimal = x_entero + ancho_entero
            x_entero -= 13
            x_decimal -= 13
        
        bbox_entero = font_entero.getbbox("0")
        bbox_decimal = font_decimal.getbbox("0")
        offset_y = bbox_entero[3] - bbox_decimal[3]
        decimal_y = pos_y + offset_y
        
        draw_text_with_outline(draw, (x_entero, pos_y), entero, font_entero, fill=base_style["color"], outline_fill="white", outline_width=2)
        draw.text((x_entero + ancho_entero, decimal_y), decimal, font=font_decimal, fill=decimal_style.get("color", base_style["color"]) if decimal_style else base_style["color"])
    except Exception as e:
        logger.error(f"Error al dibujar valor de movimiento: {str(e)}")
        raise

def eliminar_tildes(texto):
    """Elimina tildes/acentos del texto para comprobantes.
    á → a, é → e, í → i, ó → o, ú → u
    Mantiene la ñ y otros caracteres especiales."""
    tildes = {
        'á': 'a', 'Á': 'A',
        'é': 'e', 'É': 'E',
        'í': 'i', 'Í': 'I',
        'ó': 'o', 'Ó': 'O',
        'ú': 'u', 'Ú': 'U',
        'ü': 'u', 'Ü': 'U'
    }
    resultado = ""
    for char in texto:
        resultado += tildes.get(char, char)
    return resultado

def ofuscar_nombre(nombre):
    """Ofusca un nombre reemplazando partes con asteriscos (usado para COMPROBANTE_LLAVE)."""
    try:
        palabras = nombre.strip().split()
        nombre_ofuscado = []
        for palabra in palabras:
            if len(palabra) > 3:
                nombre_ofuscado.append(palabra[:3] + "*" * (len(palabra) - 3))
            else:
                nombre_ofuscado.append(palabra + "*" * (3 - len(palabra)))
        return " ".join(nombre_ofuscado)
    except Exception as e:
        logger.error(f"Error al ofuscar nombre: {str(e)}")
        return nombre

def ofuscar_nombre_uniforme(nombre, mayusculas=False):
    """
    Ofusca un nombre mostrando solo las primeras 3 letras de cada palabra + asteriscos.
    Formato uniforme para QR de Nequi, Llaves, BRE-B y Bancolombia.
    Ejemplo: "mariana martinez" -> "Mar**** Mar*****" (title) o "MAR**** MAR*****" (mayúsculas)
    """
    try:
        # Normalizar: eliminar tildes, espacios extras, y convertir a título para normalizar
        nombre_limpio = eliminar_tildes(nombre.strip())
        palabras = nombre_limpio.split()
        nombre_ofuscado = []
        
        for palabra in palabras:
            # Si la palabra tiene más de 3 letras: primeras 3 + asteriscos
            if len(palabra) > 3:
                primera_parte = palabra[:3]
                resto = "*" * (len(palabra) - 3)
                nombre_ofuscado.append(primera_parte + resto)
            else:
                # Si tiene 3 o menos: palabra completa + asteriscos hasta tener mínimo 4 caracteres
                asteriscos_necesarios = max(1, 4 - len(palabra))
                nombre_ofuscado.append(palabra + "*" * asteriscos_necesarios)
        
        resultado = " ".join(nombre_ofuscado)
        
        # Aplicar formato según el parámetro
        if mayusculas:
            return resultado.upper()
        else:
            # Title case: primera letra mayúscula, resto minúscula
            return resultado.title()
    except Exception as e:
        logger.error(f"Error al ofuscar nombre uniforme: {str(e)}")
        return nombre.upper() if mayusculas else nombre.title()

def ofuscar_nombre_primeras_letras(nombre):
    """Ofusca un nombre mostrando solo las primeras tres letras de cada palabra,
    rellenando el resto con asteriscos (ej: RAFAEL -> RAF***, GONZALEZ -> GON*****)."""
    # Usar la función uniforme en mayúsculas para compatibilidad
    return ofuscar_nombre_uniforme(nombre, mayusculas=True)

def ofuscar_nombre_qr(nombre):
    """Ofusca un nombre para QR con lógica inteligente:
    - Nombres cortos (ej: 'Pet cue'): NO ofusca
    - Nombres normales (ej: 'K MAX ALANDEZ'): ofusca últimos 4 → 'K MAX ALA****'
    - Nombres largos con palabras (ej: 'POLLO CROLLO ALAPARRILLA'): cada palabra con 3 letras + asteriscos → 'POL** CRO****** ALA********'
    """
    try:
        nombre_limpio = " ".join(nombre.strip().split())
        
        # Nombres cortos (≤10 caracteres): NO ofuscar
        if len(nombre_limpio) <= 10:
            return nombre_limpio
        
        # Verificar si tiene espacios (múltiples palabras)
        tiene_espacios = " " in nombre_limpio
        
        if tiene_espacios:
            palabras = nombre_limpio.split()
            # Si tiene muchas palabras o es muy largo (>20 caracteres), ofuscar cada palabra
            if len(nombre_limpio) > 20 or len(palabras) >= 3:
                # Ofuscar cada palabra: 3 primeras letras + asteriscos
                palabras_ofuscadas = []
                for palabra in palabras:
                    if len(palabra) > 3:
                        palabras_ofuscadas.append(palabra[:3] + "*" * (len(palabra) - 3))
                    else:
                        palabras_ofuscadas.append(palabra)
                return " ".join(palabras_ofuscadas)
            else:
                # Nombres medianos: ofuscar últimos 4 caracteres del total
                return nombre_limpio[:-4] + "****"
        else:
            # Una sola palabra sin espacios
            if len(nombre_limpio) > 15:
                # Palabra muy larga: mostrar 3 primeras letras + asteriscos
                return nombre_limpio[:3] + "*" * (len(nombre_limpio) - 3)
            elif len(nombre_limpio) > 4:
                # Palabra mediana: ofuscar últimos 4
                return nombre_limpio[:-4] + "****"
            else:
                # Palabra muy corta: no ofuscar
                return nombre_limpio
    except Exception as e:
        logger.error(f"Error al ofuscar nombre QR: {str(e)}")
        return nombre

def generar_comprobante(data, config):
    """Genera una imagen de comprobante con los datos y configuración proporcionados."""
    try:
        template_path = config["template"]
        output_path = f"gen_{uuid.uuid4().hex}.png"
        styles = config["styles"]
        font_path = config["font"]

        # Validar existencia de plantilla y fuente
        if not os.path.exists(template_path):
            logger.error(f"Plantilla no encontrada: {template_path}")
            return None
        if not os.path.exists(font_path):
            logger.error(f"Fuente no encontrada: {font_path}")
            return None

        image = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        tipo_movimiento = ("valor1" in styles and "nombre" in styles and "valor_decimal" in styles)
        es_comprobante_qr = config["output"] == "comprobante_qr_generado.png"
        es_comprobante4 = config["output"] == "comprobante4_generado.png"
        es_comprobante_llave = config["output"] == "comprobante_llave_generado.png"
        es_bancolombia = config["output"] == "comprobante_movimiento_generado.png" or config["output"] == "comprobante_nequi_bc_generado.png" or config["template"] == "img/nequi_a_bancol.jpg"

        if tipo_movimiento:
            try:
                decimal_style = styles.get("valor_decimal")
                # Identificar si es movimiento BRE-B o QR para alineación especial
                es_movimiento_especial = config["template"] in ["img/movements_bre-b.jpg", "img/movements_qr.jpg", "img/comprobante_movimiento3.jpg"]
                
                # Validar que el valor esté presente
                if "valor" not in data:
                    logger.error(f"Error: 'valor' no encontrado en data para movimiento. Data keys: {list(data.keys())}")
                    return None
                
                logger.info(f"[DEBUG] Generando movimiento - Template: {config['template']}, Valor: {data['valor']}, Nombre: {data.get('nombre', 'N/A')}")
                dibujar_valor_movimiento(draw, styles["valor1"], data["valor"], font_path, image.width, decimal_style, es_movimiento_especial)
                # Aplicar ofuscación adecuada según el tipo de comprobante
                # Eliminar tildes primero
                nombre = eliminar_tildes(data.get("nombre", "Nombre no proporcionado"))
                
                # Ofuscar nombres según el tipo de plantilla (del proyecto original)
                if config["template"] in ["img/nequi_a_bancol.jpg", "img/bancol_movement.jpg"]:
                    nombre = ofuscar_nombre_primeras_letras(nombre)
                elif config["template"] == "img/movements_bre-b.jpg":
                    # Movimiento BRE-B: NO ofuscar, solo mayúsculas
                    nombre = nombre.upper()
                elif config["template"] in ["img/movements_qr.jpg", "img/comprobante_movimiento3.jpg"]:
                    # Movimiento QR: ofuscación inteligente
                    nombre = ofuscar_nombre_qr(nombre.upper())
                elif config["template"] == "img/movement.jpg":
                    # Movimiento Nequi: solo mayúsculas
                    nombre = nombre.upper()
                else:
                    nombre = nombre.upper()

                font_nombre = ImageFont.truetype(styles["nombre"].get("font", font_path), styles["nombre"]["size"])
                draw_text_with_outline(draw, styles["nombre"]["pos"], nombre, font=font_nombre, fill=styles["nombre"]["color"], outline_fill="white", outline_width=2)
                logger.info(f"[DEBUG] Movimiento dibujado correctamente - Nombre: {nombre}")
            except Exception as e:
                logger.error(f"Error al generar movimiento: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return None
        else:
            meses_es = {
                "january": "enero", "february": "febrero", "march": "marzo", "april": "abril",
                "may": "mayo", "june": "junio", "july": "julio", "august": "agosto",
                "september": "septiembre", "october": "octubre", "november": "noviembre", "december": "diciembre"
            }
            # Definir now siempre para usarlo en hora_esquina si es necesario
            now = datetime.now(pytz.timezone("America/Bogota"))
            # Usar fecha manual si está disponible, sino generar automática
            if "fecha" in data and data["fecha"]:
                fecha = data["fecha"]
            else:
                mes_en = now.strftime("%B").lower()
                mes = meses_es.get(mes_en, mes_en)
                hora_12h = now.strftime("%I:%M")
                sufijo = "a.m." if now.strftime("%p") == "AM" else "p.m."
                fecha = f"{now.strftime('%d')} de {mes} de {now.strftime('%Y')} a las {hora_12h} {sufijo}"
            logger.info(f"[DEBUG] fecha completa → {fecha}")
            logger.info(f"[DEBUG] longitud → {len(fecha)}")
            # Usar referencia manual si está disponible, sino generar automática
            referencia = data.get("referencia", f"M{random.randint(10000000, 99999999)}")
            try:
                valor = float(data["valor"])
                valor_formateado = "$ {:,.2f}".format(abs(valor)).replace(",", "X").replace(".", ",").replace("X", ".")
            except (ValueError, TypeError) as e:
                logger.error(f"Error al formatear valor: {data.get('valor')} - {str(e)}")
                valor_formateado = "$ 0,00"
            telefono_raw = data.get("telefono", "")
            telefono_formateado = f"{telefono_raw[:3]} {telefono_raw[3:6]} {telefono_raw[6:]}" if telefono_raw.isdigit() and len(telefono_raw) == 10 else telefono_raw

            # Aplicar formato uniforme para QR de Nequi, Llaves, BRE-B y Bancolombia
            nombre_base = data.get("nombre", "Nombre no proporcionado")
            
            if es_comprobante_llave:
                # Llaves: formato uniforme en Title Case (Mar**** Mar*****)
                datos = {
                    "nombre": ofuscar_nombre_uniforme(nombre_base, mayusculas=False),
                    "llave": data.get("llave", ""),
                    "banco_destino": data.get("banco_destino", ""),
                    "numero_envio": (
                        f"{data.get('numero_envio', '')[:3]} "
                        f"{data.get('numero_envio', '')[3:6]} "
                        f"{data.get('numero_envio', '')[6:]}"
                        if data.get("numero_envio", "").isdigit()
                        and len(data.get("numero_envio", "")) == 10
                        else data.get("numero_envio", "")
                    ),
                    "valor1": valor_formateado,
                    "fecha": fecha,
                    "referencia": referencia,
                    "disponible": "Disponible",
                }
            elif es_bancolombia:
                # Bancolombia: formato uniforme en Title Case (Mar**** Mar*****)
                datos = {
                    "nombre": ofuscar_nombre_uniforme(nombre_base, mayusculas=False),
                    "valor1": valor_formateado,
                    "hora_esquina": now.strftime("%I:%M").lstrip("0"),
                    "fecha": fecha,
                    "referencia": referencia,  # Usar la referencia (manual o automática) definida arriba
                    "disponible": "Disponible",
                    "banco": "Bancolombia",
                    "cuenta": data.get("cuenta", data.get("numero_cuenta", "")),  # Compatibilidad con ambos campos
                }
            else:
                datos = {
                    "telefono": telefono_formateado,
                    "nombre": eliminar_tildes(nombre_base).title(),
                    "valor1": valor_formateado,
                    "fecha": fecha,
                    "referencia": referencia,
                    "disponible": "Disponible",
                }
                if es_comprobante_qr or es_comprobante4:
                    # QR de Nequi y BRE-B: formato uniforme en Title Case (Mar**** Mar*****)
                    # NOTA: QR Bancolombia tiene su propia configuración separada
                    datos = {
                        "nombre": ofuscar_nombre_uniforme(nombre_base, mayusculas=False),
                        "llave": data.get("llave", ""),
                        "banco_destino": data.get("banco_destino", ""),
                        "numero_envio": (
                            f"{data.get('numero_envio', '')[:3]} "
                            f"{data.get('numero_envio', '')[3:6]} "
                            f"{data.get('numero_envio', '')[6:]}"
                            if data.get("numero_envio", "").isdigit()
                            and len(data.get("numero_envio", "")) == 10
                            else data.get("numero_envio", "")
                        ),
                        "valor1": valor_formateado,
                        "fecha": fecha,
                        "referencia": referencia,
                        "disponible": "Disponible",
                    }

            for campo, texto in datos.items():
                if campo in styles:
                    style = styles[campo]
                    try:
                        fuente_campo = style.get("font", font_path)
                        font = ImageFont.truetype(fuente_campo, style["size"])
                        logger.info(f"[DEBUG] Dibujando campo {campo}: '{texto}' en posición {style['pos']} con color {style.get('color', 'default')}")
                        pos_x = style["pos"][0]
                        pos_y = style["pos"][1]
                        # Para Nequi a Bancolombia, dibujar sin outline (como el original)
                        if es_bancolombia:
                            draw.text((pos_x, pos_y), str(texto), font=font, fill=style["color"])
                        # Para Nequi (COMPROBANTE1), usar efecto profesional con múltiples capas de sombra
                        elif config["output"] == "comprobante1_generado.png":
                            draw_text_professional(draw, (pos_x, pos_y), str(texto), font, style["color"])
                        else:
                            draw_text_with_outline(draw, (pos_x, pos_y), str(texto), font=font, fill=style["color"], outline_fill="white", outline_width=2)
                    except Exception as e:
                        logger.error(f"Error al cargar fuente o dibujar campo {campo}: {str(e)}")
                        return None
                else:
                    logger.warning(f"[DEBUG] Campo {campo} no tiene estilo definido en config.py")

        # Dibujar hora en la esquina (hora_esquina)
        if "hora_esquina" in styles:
            style = styles["hora_esquina"]
            try:
                font = ImageFont.truetype(font_path, style["size"])
            except Exception as e:
                logger.error(f"Error al cargar fuente para hora_esquina: {str(e)}")
                return None
            hora_col = datetime.now(pytz.timezone("America/Bogota")).strftime("%I:%M")
            draw.text(style["pos"], hora_col, font=font, fill=style["color"])

        # Guardar imagen con optimización
        logger.info(f"[DEBUG] Guardando imagen: {output_path}, Dimensiones: {image.size}")
        try:
            # Para imágenes grandes (como plantilla Nequi 2560x5120), usar JPEG y reducir tamaño si es necesario
            total_pixels = image.size[0] * image.size[1]
            if total_pixels > 2000000:  # Si es mayor a 2MP (13MP en este caso)
                # Reducir tamaño si es muy grande (mantener proporción)
                max_dimension = 1920  # Máximo 1920px en el lado más largo
                if image.size[0] > max_dimension or image.size[1] > max_dimension:
                    ratio = min(max_dimension / image.size[0], max_dimension / image.size[1])
                    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                    logger.info(f"[DEBUG] Reduciendo imagen de {image.size} a {new_size}")
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                output_path_jpg = output_path.replace('.png', '.jpg')
                image.save(output_path_jpg, format='JPEG', quality=92, optimize=True)
                file_size_mb = os.path.getsize(output_path_jpg) / (1024*1024)
                logger.info(f"[DEBUG] Imagen guardada como JPEG: {output_path_jpg}, Tamaño: {file_size_mb:.2f} MB")
                return output_path_jpg
            else:
                image.save(output_path, format='PNG', compress_level=1)
                file_size_mb = os.path.getsize(output_path) / (1024*1024)
                logger.info(f"[DEBUG] Imagen guardada como PNG: {output_path}, Tamaño: {file_size_mb:.2f} MB")
                return output_path
        except Exception as e:
            logger.error(f"Error al guardar imagen: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    except Exception as e:
        logger.error(f"Error al generar comprobante: {str(e)}")
        return None


# ====================================================================
# FUNCIONES AUXILIARES PARA QR BC
# ====================================================================

def generar_codigo_comprobante() -> str:
    """Genera un código aleatorio de 12 caracteres para el comprobante"""
    import string
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=12))


def dividir_texto_en_lineas(texto: str, max_palabras_por_linea: int = 2) -> list:
    """Divide un texto largo en múltiples líneas"""
    palabras = texto.split()
    lineas = []
    for i in range(0, len(palabras), max_palabras_por_linea):
        linea = ' '.join(palabras[i:i + max_palabras_por_linea])
        lineas.append(linea)
    return lineas


def dividir_texto_por_ancho(draw, texto: str, font, ancho_maximo: int, limite_derecho: int = None, x_inicio: int = None) -> list:
    """Divide un texto en MÁXIMO 2 líneas según el ancho máximo permitido (para QR BC)
    Estrategia 2x2: Si hay 3+ palabras, primeras 2 arriba, últimas 2 abajo"""
    palabras = texto.split()
    if not palabras:
        return []
    
    # Si hay solo una palabra, retornar una línea
    if len(palabras) == 1:
        return [texto]
    
    # Si hay 3 o más palabras, SIEMPRE dividir (independientemente del ancho):
    # Primera línea: primeras 2 palabras
    # Segunda línea: tercera palabra en adelante
    if len(palabras) >= 3:
        primera_linea = ' '.join(palabras[:2])  # Primeras 2 palabras
        # Si hay exactamente 3 palabras: tercera palabra abajo
        # Si hay 4+ palabras: últimas 2 palabras abajo
        if len(palabras) == 3:
            segunda_linea = palabras[2]  # Solo la tercera palabra (índice 2)
        elif len(palabras) >= 4:
            segunda_linea = ' '.join(palabras[-2:])  # Últimas 2 palabras
        
        return [primera_linea, segunda_linea]
    
    # Verificar si todo el texto cabe en una línea (solo para 2 palabras)
    bbox_completo = draw.textbbox((0, 0), texto, font=font)
    ancho_completo = bbox_completo[2] - bbox_completo[0]
    if ancho_completo <= ancho_maximo:
        return [texto]
    
    # Si hay 2 palabras, dividir normalmente
    # Si no caben juntas, separar
    return [palabras[0], palabras[1]]


def ofuscar_nombre_bc(nombre: str) -> str:
    """Ofusca el nombre después de 3 letras de cada palabra (para BC)"""
    palabras = nombre.split()
    ofuscadas = []
    for palabra in palabras:
        if len(palabra) <= 3:
            ofuscadas.append(palabra)
        else:
            ofuscadas.append(palabra[:3] + '*' * (len(palabra) - 3))
    return ' '.join(ofuscadas)


def dibujar_texto_multilinea(draw, coordenadas, texto, font, color, interlineado=5, indentar_segunda_linea=False):
    """Dibuja texto que puede ocupar múltiples líneas
    Si indentar_segunda_linea es True, la segunda línea y siguientes tendrán indentación automática"""
    if isinstance(texto, str):
        lineas = dividir_texto_en_lineas(texto, max_palabras_por_linea=2)
    else:
        lineas = texto
    
    x, y = coordenadas
    # Para QR BC: calcular indentación basada en el ancho de un espacio
    if indentar_segunda_linea and len(lineas) > 1:
        # Calcular el ancho de un espacio en la fuente
        bbox_espacio = draw.textbbox((0, 0), " ", font=font)
        ancho_espacio = bbox_espacio[2] - bbox_espacio[0]
        # Indentación: aproximadamente 4-5 espacios para alineación visual
        indentacion = int(ancho_espacio * 4.5)
    else:
        indentacion = 0
    
    for i, linea in enumerate(lineas):
        x_pos = x + (indentacion if i > 0 and indentar_segunda_linea else 0)
        draw.text((x_pos, y), linea, fill=color, font=font)
        y += font.size + interlineado


# ====================================================================
# FUNCIONES AUXILIARES PARA BANCOLOMBIA
# ====================================================================

def formatear_punto_venta_bc_qr(texto: str) -> tuple:
    """Formatea el punto de venta en dos líneas en MAYÚSCULAS
    Retorna tupla (linea1, linea2)"""
    if not texto:
        return ("", "")
    
    # Convertir a mayúsculas
    texto_upper = texto.upper()
    palabras = texto_upper.split()
    
    if len(palabras) == 0:
        return ("", "")
    elif len(palabras) == 1:
        return (palabras[0], "")
    elif len(palabras) == 2:
        return (palabras[0], palabras[1])
    elif len(palabras) == 3:
        # Para 3 palabras: primeras 2 en primera línea, tercera en segunda
        linea1 = " ".join(palabras[:2])
        linea2 = palabras[2]
        return (linea1, linea2)
    else:
        # Si hay 4 o más palabras, dividir balanceadamente
        mitad = len(palabras) // 2
        linea1 = " ".join(palabras[:mitad])
        linea2 = " ".join(palabras[mitad:])
        return (linea1, linea2)


def enmascarar_nombre_bc_qr(nombre: str) -> tuple:
    """Enmascara el nombre y lo divide en dos líneas
    Formato: primeras 3 letras visibles, seguidas de 3 asteriscos
    Retorna tupla (linea1, linea2)"""
    if not nombre:
        return ("", "")
    
    # Convertir a mayúsculas
    nombre_upper = nombre.upper()
    palabras = nombre_upper.split()
    
    # Aplicar enmascaramiento a cada palabra
    palabras_mask = []
    for palabra in palabras:
        if len(palabra) <= 3:
            # Si la palabra tiene 3 letras o menos, mostrarla completa con 3 asteriscos
            palabras_mask.append(palabra + "***")
        else:
            # Mostrar las primeras 3 letras y exactamente 3 asteriscos
            visibles = palabra[:3]
            palabras_mask.append(visibles + "***")
    
    # Misma lógica que formatear_punto_venta_bc_qr
    if len(palabras_mask) == 0:
        return ("", "")
    elif len(palabras_mask) == 1:
        return (palabras_mask[0], "")
    elif len(palabras_mask) == 2:
        return (palabras_mask[0], palabras_mask[1])
    elif len(palabras_mask) == 3:
        # Para 3 palabras: primeras 2 en primera línea, tercera en segunda
        linea1 = " ".join(palabras_mask[:2])
        linea2 = palabras_mask[2]
        return (linea1, linea2)
    else:
        # Si hay 4 o más palabras, dividir balanceadamente
        mitad = len(palabras_mask) // 2
        linea1 = " ".join(palabras_mask[:mitad])
        linea2 = " ".join(palabras_mask[mitad:])
        return (linea1, linea2)


def formatear_numero_cuenta_ahorros(numero: str) -> str:
    """Formatea número de cuenta: '12345678912' -> '123 - 456789 - 12'"""
    if not numero:
        return ""
    # Limpiar el número (solo dígitos)
    digitos = "".join(ch for ch in numero if ch.isdigit())
    
    # Asegurar que tenga 11 dígitos
    if len(digitos) != 11:
        return numero  # Retornar original si no tiene 11 dígitos
    
    # Formatear como: 123 - 456789 - 12
    return f"{digitos[:3]} - {digitos[3:9]} - {digitos[9:]}"


def formatear_valor_ahorros(valor_str: str) -> str:
    """Formatea el valor: '50000' -> '50.000'"""
    if not valor_str:
        return ""
    
    # Limpiar y convertir a número
    valor_limpio = valor_str.replace(".", "").replace(",", "").replace(" ", "")
    try:
        valor = int(valor_limpio)
        # Formatear con puntos como separadores de miles
        return f"{valor:,}".replace(",", ".")
    except ValueError:
        return valor_str


def formatear_valor_bc_qr(valor_str: str) -> str:
    """Formatea el valor para BC QR: '390000' -> '$ 390.000'"""
    if not valor_str:
        return ""
    
    # Limpiar y convertir a número
    valor_limpio = valor_str.replace(".", "").replace(",", "").replace(" ", "")
    try:
        valor = int(valor_limpio)
        # Formatear con símbolo $ y puntos como separadores de miles
        return f"$ {valor:,}".replace(",", ".")
    except ValueError:
        return valor_str


def generar_fecha_ahorros() -> str:
    """Genera fecha en formato: '06 Sept 2025 - 01:23 p. m.'"""
    try:
        # Mapeo de meses en español abreviado
        meses_abrev = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        
        now = datetime.now(pytz.timezone("America/Bogota"))
        dia = now.strftime("%d")
        mes = meses_abrev[now.month]
        año = now.year
        hora = now.strftime("%I:%M").lstrip("0")  # Remover cero inicial de la hora
        periodo = "a. m." if now.hour < 12 else "p. m."
        
        return f"{dia} {mes} {año} - {hora} {periodo}"
    except Exception:
        return ""


def generar_fecha_bc_qr() -> str:
    """Genera fecha en formato BC QR: '07 oct. 2025 - 02:34 a.m.'"""
    try:
        # Mapeo de meses en español abreviado con punto y minúsculas
        meses_abrev = {
            1: "ene.", 2: "feb.", 3: "mar.", 4: "abr.", 5: "may.", 6: "jun.",
            7: "jul.", 8: "ago.", 9: "sept.", 10: "oct.", 11: "nov.", 12: "dic."
        }
        
        now = datetime.now(pytz.timezone("America/Bogota"))
        dia = now.strftime("%d")
        mes = meses_abrev[now.month]
        año = now.year
        hora = now.strftime("%I:%M").lstrip("0")  # Remover cero inicial de la hora
        periodo = "a.m." if now.hour < 12 else "p.m."  # Sin espacios
        
        return f"{dia} {mes} {año} - {hora} {periodo}"
    except Exception:
        return ""


def formatear_nombre_ahorros(nombre: str) -> str:
    """Devuelve el nombre tal como lo ingresó el usuario, sin modificar mayúsculas/minúsculas"""
    if not nombre:
        return ""
    return nombre  # Sin modificar el formato original


def generar_comprobante_ahorros(data, config):
    """Genera comprobante de ahorros con formateo específico (lógica de BOTSITECOL)"""
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    font_path = config["font"]

    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Formatear datos
    nombre_formateado = formatear_nombre_ahorros(data.get("nombre", ""))
    numero_cuenta_formateado = formatear_numero_cuenta_ahorros(data.get("numero_cuenta", ""))
    valor_formateado = formatear_valor_ahorros(str(data.get("valor", "")))
    fecha_formateada = generar_fecha_ahorros()
    
    # Formatear fecha_esquina (solo hora en formato 1:43)
    now = datetime.now(pytz.timezone("America/Bogota"))
    fecha_esquina = now.strftime("%I:%M").lstrip("0")
    
    # Formatear valor de transferencia con $ (ejemplo: $ 6.000)
    valor_limpio = str(data.get("valor", "")).replace(".", "").replace(",", "").replace(" ", "")
    try:
        valor_int = int(valor_limpio)
        valor_transferencia = f"$ {valor_int:,}".replace(",", ".")
    except:
        valor_transferencia = f"$ {data.get('valor', '0')}"
    
    # Formatear costo de transferencia (solo el número, sin etiqueta) - $ 1.000,00 o $ 0,00
    costo = data.get("costo_transferencia", 0)
    if costo and int(costo) > 0:
        # Formatear con punto para miles y coma para decimales
        costo_int = int(costo)
        costo_formateado = f"$ {costo_int:,}".replace(",", "X").replace(".", ",").replace("X", ".") + ",00"
    else:
        costo_formateado = "$ 0,00"
    
    # Generar número de comprobante: 00000 + 5 dígitos aleatorios
    comprobante_no = "00000" + "".join([str(random.randint(0, 9)) for _ in range(5)])
    
    # Formatear referencia de transferencia (siempre se genera, automática si el usuario dijo no)
    referencia = data.get("referencia_transferencia")
    if referencia:
        # Formatear con * al inicio: *7423
        referencia_formateada = f"*{referencia}"
    else:
        # Si no hay referencia, generar una automáticamente
        referencia_formateada = f"*{''.join([str(random.randint(0, 9)) for _ in range(4)])}"

    datos = {
        "fecha_esquina": fecha_esquina,
        "comprobante_no": comprobante_no,
        "fecha": fecha_formateada,
        "valor_transferencia": valor_transferencia,
        "costo_transferencia": costo_formateado,
        "nombre": nombre_formateado,
        "referencia_transferencia": referencia_formateada,  # Siempre en (88, 2044)
        "numero_cuenta": numero_cuenta_formateado,  # Siempre en (85, 1605)
    }

    # Dibujar cada campo con su fuente específica SIN OUTLINE
    for campo, texto in datos.items():
        if campo in styles:
            style = styles[campo]
            # Usar fuente específica del campo o la fuente por defecto
            fuente_campo = style.get("font", font_path)
            font = ImageFont.truetype(fuente_campo, style["size"])
            # Dibujar texto directamente sin outline
            draw.text(style["pos"], str(texto), font=font, fill=style["color"])

    # Obtener el color de fondo gris de la plantilla (muestrear un área central)
    # Tomar el color de un píxel en el centro de la imagen
    width, height = image.size
    center_x, center_y = width // 2, height // 2
    bg_color = image.getpixel((center_x, center_y))
    
    # Si el color es muy oscuro (negro), buscar un color gris más claro en otra área
    if sum(bg_color) < 100:  # Si es muy oscuro
        # Buscar en un área más abajo donde suele estar el fondo gris
        sample_y = min(height - 100, center_y + 200)
        bg_color = image.getpixel((center_x, sample_y))
    
    # Crear una nueva imagen con el tamaño completo y el color de fondo gris
    final_image = Image.new("RGB", (width, height), bg_color)
    
    # Pegar la imagen original sobre el fondo gris
    final_image.paste(image, (0, 0))
    
    # Guardar la imagen final
    final_image.save(output_path, format='PNG', compress_level=1)
    return output_path


# ====================================================================
# FUNCIONES AUXILIARES PARA BC A NEQUI
# ====================================================================

def ajustar_texto_ancho(draw, texto: str, fuente_path: str, tamano_inicial: int, 
                        ancho_maximo: int, tamano_minimo: int = 10) -> tuple:
    """Ajusta automáticamente el tamaño de fuente para que el texto quepa en el ancho máximo"""
    tamano_actual = tamano_inicial
    
    while tamano_actual >= tamano_minimo:
        fuente = ImageFont.truetype(fuente_path, tamano_actual)
        bbox = draw.textbbox((0, 0), texto, font=fuente)
        ancho_texto = bbox[2] - bbox[0]
        
        if ancho_texto <= ancho_maximo:
            return fuente, tamano_actual
        
        tamano_actual -= 1
    
    return ImageFont.truetype(fuente_path, tamano_minimo), tamano_minimo


def traducir_mes(fecha_dt):
    """Traduce el mes de inglés a español abreviado"""
    MESES_EN_ES = {
        "january": "Ene", "february": "Feb", "march": "Mar", "april": "Abr",
        "may": "May", "june": "Jun", "july": "Jul", "august": "Ago",
        "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dic"
    }
    import locale
    locale_actual = locale.getlocale(locale.LC_TIME)
    try:
        locale.setlocale(locale.LC_TIME, 'C')
        mes_en = fecha_dt.strftime("%B").lower()
    finally:
        locale.setlocale(locale.LC_TIME, locale_actual)
    return MESES_EN_ES.get(mes_en, mes_en)


# ====================================================================
# FUNCIONES BOT BANCOLOMBIA (ORIGINAL BC A NEQUI)
# ====================================================================

def generar_comprobante_bc_nequi(numero: str, valor: str, nombre: str = "") -> str:
    """Genera el comprobante de BC a Nequi (configuración original)"""
    from config import COORDENADAS_NEQUI_BC, FUENTES_NEQUI_BC, RUTAS_NEQUI_BC, COLORES_NEQUI_BC
    
    valor = str(valor).replace("$", "").replace(".", "").replace(",", "").strip()
    numero = numero.strip()
    nombre = nombre.strip() if nombre else ""
    
    valor_entero = int(valor)
    valor_formateado = f"$ {valor_entero:,}".replace(",", ".")
    
    # Generar comprobante aleatorio: 00000 + 5 dígitos aleatorios
    comprobante_aleatorio = "00000" + "".join([str(random.randint(0, 9)) for _ in range(5)])
    
    # Generar cuenta de ahorros: * + 4 dígitos diferentes, primer dígito siempre es 4, 8 o 9
    primer_digito = random.choice(['4', '8', '9'])
    digitos_disponibles = [d for d in '0123456789' if d != primer_digito]
    random.shuffle(digitos_disponibles)
    cuenta_ahorros = "*" + primer_digito + "".join(digitos_disponibles[:3])
    
    plantilla = Image.open(RUTAS_NEQUI_BC['plantilla'])
    if plantilla.mode in ('RGBA', 'LA', 'P'):
        plantilla = plantilla.convert('RGB')
    
    draw = ImageDraw.Draw(plantilla)
    
    font_numero = ImageFont.truetype(RUTAS_NEQUI_BC['font'], FUENTES_NEQUI_BC['numero'])
    font_valor = ImageFont.truetype(RUTAS_NEQUI_BC['font'], FUENTES_NEQUI_BC['valor'])
    font_fecha = ImageFont.truetype('fuentes/opensans_regular.ttf', FUENTES_NEQUI_BC['fecha'])
    font_nombre = ImageFont.truetype(RUTAS_NEQUI_BC['font'], FUENTES_NEQUI_BC['nombre'])
    font_comprobante = ImageFont.truetype('fuentes/opensans_regular.ttf', FUENTES_NEQUI_BC['comprobante'])
    font_cuenta_ahorros = ImageFont.truetype(RUTAS_NEQUI_BC['font'], FUENTES_NEQUI_BC['cuenta_ahorros'])
    
    colombia = pytz.timezone("America/Bogota")
    fecha_actual = datetime.now(colombia)
    dia = fecha_actual.strftime("%d")
    mes = traducir_mes(fecha_actual)
    anio = fecha_actual.strftime("%Y")
    hora = fecha_actual.strftime("%I:%M %p").lower().replace("am", "a. m.").replace("pm", "p. m.")
    fecha_formateada = f"{dia} {mes} {anio} - {hora}"
    
    coordenadas = COORDENADAS_NEQUI_BC
    
    draw.text(coordenadas['fecha'], fecha_formateada, fill=COLORES_NEQUI_BC['fecha'], font=font_fecha)
    draw.text(coordenadas['valor'], valor_formateado, fill=COLORES_NEQUI_BC['valor'], font=font_valor)
    draw.text(coordenadas['numero'], numero, fill=COLORES_NEQUI_BC['numero'], font=font_numero)
    draw.text(coordenadas['comprobante'], comprobante_aleatorio, fill=COLORES_NEQUI_BC['comprobante'], font=font_comprobante)
    draw.text(coordenadas['cuenta_ahorros'], cuenta_ahorros, fill=COLORES_NEQUI_BC['cuenta_ahorros'], font=font_cuenta_ahorros)
    
    if nombre:
        font_nombre_ajustado, _ = ajustar_texto_ancho(
            draw, nombre, RUTAS_NEQUI_BC['font'], FUENTES_NEQUI_BC['nombre'],
            ancho_maximo=400, tamano_minimo=14
        )
        draw.text(coordenadas['nombre'], nombre, fill=(255, 255, 255), font=font_nombre_ajustado)
    
    output_path = 'comprobante_bc_nequi_generado.jpg'
    plantilla.save(output_path, format='JPEG', quality=95, optimize=False)
    logger.info(f"Comprobante BC a Nequi generado: {numero} - ${valor_entero:,.0f}")
    return output_path


def generar_movimientos_bc_nequi(cuenta: str, valor: str) -> str:
    """Genera la imagen de movimientos para BC a Nequi (configuración original)"""
    from config import COORDENADAS_MOVIMIENTOS_NEQUI_BC, FUENTES_MOVIMIENTOS_NEQUI_BC, COLORES_MOVIMIENTOS_NEQUI_BC, RUTAS_MOVIMIENTOS_NEQUI_BC
    
    valor = str(valor).replace("$", "").replace(".", "").replace(",", "").strip()
    valor_entero = int(valor)
    valor_formateado = f"{valor_entero:,}".replace(",", ".")
    
    plantilla = Image.open(RUTAS_MOVIMIENTOS_NEQUI_BC['plantilla'])
    if plantilla.mode in ('RGBA', 'LA', 'P'):
        plantilla = plantilla.convert('RGB')
    
    draw = ImageDraw.Draw(plantilla)
    
    font_fecha = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], FUENTES_MOVIMIENTOS_NEQUI_BC['fecha'])
    font_cuenta = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], FUENTES_MOVIMIENTOS_NEQUI_BC['cuenta_ahorros'])
    
    tamano_cop = 18
    num_digitos = len(str(valor_entero))
    
    if num_digitos >= 9:
        tamano_saldo_neg = 16
    elif num_digitos >= 8:
        tamano_saldo_neg = 18
    elif num_digitos >= 7:
        tamano_saldo_neg = 20
    elif num_digitos >= 6:
        tamano_saldo_neg = 22
    elif num_digitos >= 5:
        tamano_saldo_neg = 24
    else:
        tamano_saldo_neg = FUENTES_MOVIMIENTOS_NEQUI_BC['saldo_negativo']
    
    font_saldo_neg = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], tamano_saldo_neg)
    font_cop = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], tamano_cop)
    font_decimales = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], int(tamano_saldo_neg * 0.70))
    
    colombia = pytz.timezone("America/Bogota")
    fecha_actual = datetime.now(colombia)
    dia = fecha_actual.strftime("%d")
    mes_num = fecha_actual.strftime("%m")
    anio = fecha_actual.strftime("%Y")
    
    meses = {
        '01': 'ENE', '02': 'FEB', '03': 'MAR', '04': 'ABR',
        '05': 'MAY', '06': 'JUN', '07': 'JUL', '08': 'AGO',
        '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DIC'
    }
    mes = meses.get(mes_num, mes_num)
    fecha_formateada = f"{dia} {mes} {anio}"
    
    saldo_base = valor_entero + random.randint(10000, 100000)
    saldo_disponible_entero = f"$ {saldo_base:,}".replace(",", ".")
    
    num_digitos_disp = len(str(saldo_base))
    
    if num_digitos_disp >= 9:
        tamano_saldo_disp = 18
    elif num_digitos_disp >= 8:
        tamano_saldo_disp = 20
    elif num_digitos_disp >= 7:
        tamano_saldo_disp = 22
    elif num_digitos_disp >= 6:
        tamano_saldo_disp = 25
    else:
        tamano_saldo_disp = FUENTES_MOVIMIENTOS_NEQUI_BC['saldo_disponible']
    
    font_saldo_disp = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], tamano_saldo_disp)
    font_decimales_disp = ImageFont.truetype(RUTAS_MOVIMIENTOS_NEQUI_BC['font'], int(tamano_saldo_disp * 0.70))
    
    coordenadas = COORDENADAS_MOVIMIENTOS_NEQUI_BC
    
    draw.text(coordenadas['fecha'], fecha_formateada, fill=COLORES_MOVIMIENTOS_NEQUI_BC['fecha'], font=font_fecha)
    draw.text(coordenadas['cuenta_ahorros'], cuenta, fill=COLORES_MOVIMIENTOS_NEQUI_BC['cuenta_ahorros'], font=font_cuenta)
    
    cop_text = "COP"
    draw.text(coordenadas['cop'], cop_text, fill=COLORES_MOVIMIENTOS_NEQUI_BC['saldo_negativo'], font=font_cop)
    
    valor_entero_text = f"-$ {valor_formateado}"
    x_saldo, y_saldo = coordenadas['saldo_negativo']
    
    draw.text((x_saldo, y_saldo), valor_entero_text, fill=COLORES_MOVIMIENTOS_NEQUI_BC['saldo_negativo'], font=font_saldo_neg)
    
    bbox_entero = draw.textbbox((0, 0), valor_entero_text, font=font_saldo_neg)
    ancho_entero = bbox_entero[2] - bbox_entero[0]
    
    draw.text((x_saldo + ancho_entero, y_saldo + 3), ",00", fill=COLORES_MOVIMIENTOS_NEQUI_BC['saldo_negativo'], font=font_decimales)
    
    x_disp, y_disp = coordenadas['saldo_disponible']
    draw.text((x_disp, y_disp), saldo_disponible_entero, fill=COLORES_MOVIMIENTOS_NEQUI_BC['saldo_disponible'], font=font_saldo_disp)
    
    bbox_disp_entero = draw.textbbox((0, 0), saldo_disponible_entero, font=font_saldo_disp)
    ancho_disp_entero = bbox_disp_entero[2] - bbox_disp_entero[0]
    
    draw.text((x_disp + ancho_disp_entero, y_disp + 3), ",02", fill=COLORES_MOVIMIENTOS_NEQUI_BC['saldo_disponible'], font=font_decimales_disp)
    
    output_path = f"gen_{uuid.uuid4().hex}.jpg"
    plantilla.save(output_path, format='JPEG', quality=95, optimize=False)
    logger.info(f"Movimientos BC Nequi generados: {cuenta} - COP -${valor_formateado}")
    return output_path


# ====================================================================
# FUNCIONES BOT BANCOLOMBIA (QR BC ORIGINAL)
# ====================================================================

def generar_comprobante_qr_bc(punto_venta: str, enviado_a: str, codigo_negocio: str, 
                               cantidad: float, ultimos_4: str) -> str:
    """Genera el comprobante QR Bancolombia (configuración original del proyecto PruebaNqcsst)"""
    from config import COORDENADAS_QR_BC, FUENTES_BC, RUTAS_BC, COLORES_BC
    
    plantilla = Image.open(RUTAS_BC['plantilla_qr_bc'])
    if plantilla.mode in ('RGBA', 'LA', 'P'):
        plantilla = plantilla.convert('RGB')
    draw = ImageDraw.Draw(plantilla)
    
    font_fecha = ImageFont.truetype(RUTAS_BC['font'], FUENTES_BC['fecha'])
    font_normal = ImageFont.truetype(RUTAS_BC['font'], FUENTES_BC['normal'])
    font_cantidad = ImageFont.truetype(RUTAS_BC['font'], FUENTES_BC['cantidad'])
    
    # Obtener hora actual en Colombia correctamente
    utc_now = datetime.now(pytz.utc)
    colombia_tz = pytz.timezone("America/Bogota")
    ahora = utc_now.astimezone(colombia_tz)
    fecha_actual = ahora.strftime('%d %b. %Y - %-I:%M %p').lower().replace('am', 'a.m.').replace('pm', 'p.m.')
    
    # Convertir todos los textos a MAYÚSCULAS para QR BC
    punto_venta = punto_venta.upper()
    enviado_a = ofuscar_nombre_bc(enviado_a).upper()  # Usar el parámetro enviado_a en lugar de punto_venta
    codigo_negocio = codigo_negocio.upper()
    
    ultimos_4_formato = f'*{ultimos_4}'
    codigo_comprobante = generar_codigo_comprobante()
    cuenta_ahorros = f'*{ultimos_4}'
    
    coordenadas = COORDENADAS_QR_BC
    color = COLORES_BC['texto']
    
    draw.text(coordenadas['comprobante_no'], codigo_comprobante, fill=color, font=font_fecha)
    draw.text(coordenadas['fecha'], fecha_actual, fill=color, font=font_fecha)
    
    # Ajustar tamaño de fuente de cantidad según el número de dígitos
    cantidad_texto = f'${cantidad:,.0f}'
    tamano_cantidad = FUENTES_BC['cantidad']
    
    # Obtener coordenadas de cantidad
    x_cantidad, y_cantidad = coordenadas['cantidad']
    
    # Verificar ancho real del texto de cantidad
    bbox_cantidad = draw.textbbox((0, 0), cantidad_texto, font=font_cantidad)
    ancho_cantidad = bbox_cantidad[2] - bbox_cantidad[0]
    
    # Calcular límite derecho (mismo que para otros campos)
    x_codigo = coordenadas['codigo_negocio'][0]
    bbox_codigo = draw.textbbox((0, 0), codigo_negocio, font=font_normal)
    ancho_codigo = bbox_codigo[2] - bbox_codigo[0]
    limite_derecho_cantidad = x_codigo + ancho_codigo + 10  # Donde termina el código + margen
    
    # Calcular ancho máximo disponible
    ancho_maximo_cantidad = limite_derecho_cantidad - x_cantidad - 15  # Margen de seguridad
    
    # Si la cantidad es muy alta (ancho excede límite), mover más a la izquierda
    if ancho_cantidad > ancho_maximo_cantidad or cantidad > 42000000:
        # Calcular cuánto se está pasando
        exceso = ancho_cantidad - ancho_maximo_cantidad if ancho_cantidad > ancho_maximo_cantidad else 0
        
        # Mover X más a la izquierda cuando la cantidad es muy alta
        desplazamiento_izquierda = min(exceso + 30, 100)  # Mover más a la izquierda (exceso + 30px extra)
        x_cantidad_ajustado = max(x_cantidad - desplazamiento_izquierda, 150)  # Reducir X (mover a la izquierda), mínimo 150px
        
        # Si la cantidad es muy grande (más de 42 millones), también reducir el tamaño de fuente
        if cantidad > 42000000:
            ancho_maximo = 250  # Ancho máximo permitido para la cantidad
            font_cantidad_ajustada, _ = ajustar_texto_ancho(
                draw, cantidad_texto, RUTAS_BC['font'], tamano_cantidad, 
                ancho_maximo=ancho_maximo, tamano_minimo=28
            )
            draw.text((x_cantidad_ajustado, y_cantidad), cantidad_texto, fill=color, font=font_cantidad_ajustada)
        else:
            draw.text((x_cantidad_ajustado, y_cantidad), cantidad_texto, fill=color, font=font_cantidad)
    else:
        # Cantidad normal: dibujar en posición original
        draw.text((x_cantidad, y_cantidad), cantidad_texto, fill=color, font=font_cantidad)
    
    # Punto de venta (nombre normal) - dividir según ancho real (QR BC)
    x_punto, y_punto = coordenadas['punto_venta']
    
    # Verificar si tiene 3+ palabras para forzar división
    palabras_punto = punto_venta.split()
    tiene_3_o_mas_palabras = len(palabras_punto) >= 3
    
    # Verificar ancho real del texto completo
    bbox_punto = draw.textbbox((0, 0), punto_venta, font=font_normal)
    ancho_punto = bbox_punto[2] - bbox_punto[0]
    
    # Calcular límite basado en donde termina el código de negocio (mismo que para enviado_a)
    x_codigo = coordenadas['codigo_negocio'][0]
    bbox_codigo = draw.textbbox((0, 0), codigo_negocio, font=font_normal)
    ancho_codigo = bbox_codigo[2] - bbox_codigo[0]
    limite_derecho_codigo = x_codigo + ancho_codigo + 10  # Donde termina el código + margen
    
    # Calcular ancho máximo disponible hasta el código
    ancho_maximo_punto = limite_derecho_codigo - x_punto - 15  # Margen de seguridad
    
    # Si tiene 3+ palabras O el nombre es largo, dividir SIEMPRE
    if tiene_3_o_mas_palabras or ancho_punto > ancho_maximo_punto:
        # Calcular cuánto se está pasando
        exceso = ancho_punto - ancho_maximo_punto
        # Mover X un poco MÁS a la izquierda (reducir X moderadamente)
        # Mover hasta 85-90 píxeles a la izquierda cuando es largo (aumentado para punto de venta)
        desplazamiento_izquierda = min(exceso // 2 + 25, 90)  # Mover un poco más a la izquierda (exceso/2 + 25px extra)
        x_punto_ajustado = max(x_punto - desplazamiento_izquierda, 225)  # Reducir X (mover a la izquierda), mínimo 225px desde el borde
        
        # Recalcular ancho máximo con la nueva posición (más espacio disponible)
        ancho_maximo_ajustado = limite_derecho_codigo - x_punto_ajustado - 15
        
        # Dividir en 2 líneas con estrategia 2x2
        lineas_punto = dividir_texto_por_ancho(draw, punto_venta, font_normal, ancho_maximo_ajustado, limite_derecho_codigo, x_punto_ajustado)
        # Indentar segunda línea automáticamente (QR BC)
        dibujar_texto_multilinea(draw, (x_punto_ajustado, y_punto), lineas_punto, font_normal, color, indentar_segunda_linea=True)
    else:
        # Texto corto: dibujar normalmente en posición original
        x_punto_ajustado = x_punto  # Guardar para comparar con enviado_a
        draw.text((x_punto, y_punto), punto_venta, fill=color, font=font_normal)
    
    # Enviado a (nombre ofuscado) - dividir según ancho real (QR BC)
    # IMPORTANTE: El enviado_a SIEMPRE debe estar más a la derecha que el punto_venta
    x_enviado, y_enviado = coordenadas['enviado_a']
    
    # Verificar ancho real del texto completo
    bbox_enviado = draw.textbbox((0, 0), enviado_a, font=font_normal)
    ancho_enviado = bbox_enviado[2] - bbox_enviado[0]
    
    # Calcular límite basado en donde termina el código de negocio
    # x_codigo, bbox_codigo, ancho_codigo, limite_derecho_codigo ya están definidos arriba
    
    # Calcular ancho máximo disponible hasta el código
    ancho_maximo_enviado = limite_derecho_codigo - x_enviado - 15  # Margen de seguridad
    
    # Si el nombre es largo, mover x_enviado A LA IZQUIERDA (reducir X)
    # PERO asegurarse de que SIEMPRE esté más a la derecha que punto_venta
    if ancho_enviado > ancho_maximo_enviado:
        # Calcular cuánto se está pasando
        exceso = ancho_enviado - ancho_maximo_enviado
        # Mover X a la izquierda (reducir X)
        desplazamiento_izquierda = min(exceso // 2 + 20, 80)  # Mover a la izquierda (exceso/2 + 20px extra)
        x_enviado_ajustado = max(x_enviado - desplazamiento_izquierda, 200)  # Reducir X (mover a la izquierda), mínimo 200px
        
        # Asegurar que enviado_a SIEMPRE esté más a la derecha que punto_venta (al menos 20px de diferencia)
        # Si después del ajuste está más a la izquierda, ajustarlo
        if x_enviado_ajustado <= x_punto_ajustado:
            x_enviado_ajustado = x_punto_ajustado + 20  # Mínimo 20px más a la derecha que punto_venta
        
        # Recalcular ancho máximo con la nueva posición (más espacio disponible)
        ancho_maximo_ajustado = limite_derecho_codigo - x_enviado_ajustado - 15
        
        # Dividir en 2 líneas con estrategia 2x2
        lineas_enviado = dividir_texto_por_ancho(draw, enviado_a, font_normal, ancho_maximo_ajustado, limite_derecho_codigo, x_enviado_ajustado)
        # Indentar segunda línea automáticamente (QR BC)
        dibujar_texto_multilinea(draw, (x_enviado_ajustado, y_enviado), lineas_enviado, font_normal, color, indentar_segunda_linea=True)
    else:
        # Texto corto: dibujar normalmente en posición original
        x_enviado_ajustado = x_enviado
        # Asegurar que enviado_a SIEMPRE esté más a la derecha que punto_venta
        if x_enviado_ajustado <= x_punto_ajustado:
            x_enviado_ajustado = x_punto_ajustado + 20  # Mínimo 20px más a la derecha que punto_venta
        draw.text((x_enviado_ajustado, y_enviado), enviado_a, fill=color, font=font_normal)
    
    draw.text(coordenadas['codigo_negocio'], codigo_negocio, fill=color, font=font_normal)
    draw.text(coordenadas['texto_ahorros'], 'Ahorros', fill=color, font=font_normal)
    draw.text(coordenadas['cuenta_ahorros'], cuenta_ahorros, fill=color, font=font_normal)
    
    output_path = 'comprobante_qr_bc_generado.png'
    plantilla.save(output_path, format='PNG', compress_level=1)
    logger.info(f"Comprobante QR BC generado: {punto_venta} - ${cantidad:,.0f}")
    return output_path


# ====================================================================
# FUNCIONES BOT BANCOLOMBIA (NUEVAS - BC A BC)
# ====================================================================

def generar_comprobante_bc_nq_t(data, config):
    """Genera comprobante BC a NQ y T sin nombre, solo teléfono, valor y fecha automática"""
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    font_path = config["font"]

    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Formatear datos
    numero_cuenta_formateado = formatear_numero_cuenta_ahorros(data.get("telefono", ""))
    valor_formateado = formatear_valor_ahorros(str(data.get("valor", "")))
    fecha_formateada = generar_fecha_ahorros()

    datos = {
        "numero_cuenta": numero_cuenta_formateado,
        "valor": valor_formateado,
        "fecha": fecha_formateada,
    }

    # Dibujar cada campo con su fuente específica SIN OUTLINE
    for campo, texto in datos.items():
        if campo in styles:
            style = styles[campo]
            # Usar fuente específica del campo o la fuente por defecto
            fuente_campo = style.get("font", font_path)
            font = ImageFont.truetype(fuente_campo, style["size"])
            # Dibujar texto directamente sin outline
            draw.text(style["pos"], str(texto), font=font, fill=style["color"])

    image.save(output_path, format='PNG', compress_level=1)
    return output_path


def generar_comprobante_bc_qr(data, config):
    """Genera comprobante BC QR con punto de venta, nombre enmascarado, código de comercio, valor y fecha"""
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    font_path = config["font"]

    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Formatear datos
    # Formatear punto de venta en dos líneas
    punto_venta_linea1, punto_venta_linea2 = formatear_punto_venta_bc_qr(data.get("punto_venta", ""))
    
    # Formatear nombre enmascarado en dos líneas
    nombre_enmascarado_linea1, nombre_enmascarado_linea2 = enmascarar_nombre_bc_qr(data.get("nombre", ""))
    
    # Combinar las líneas con salto de línea para mostrar en una sola posición
    punto_venta_completo = punto_venta_linea1
    if punto_venta_linea2:
        punto_venta_completo += "\n" + punto_venta_linea2
    
    nombre_enmascarado_completo = nombre_enmascarado_linea1
    if nombre_enmascarado_linea2:
        nombre_enmascarado_completo += "\n" + nombre_enmascarado_linea2
    
    # Código de comercio
    codigo_comercio = data.get("codigo_negocio", "")
    
    valor_formateado = formatear_valor_bc_qr(str(data.get("valor", "")))
    fecha_formateada = generar_fecha_bc_qr()

    datos = {
        "punto_venta": punto_venta_completo,
        "nombre_enmascarado": nombre_enmascarado_completo,
        "codigo_comercio": codigo_comercio,
        "valor": valor_formateado,
        "fecha": fecha_formateada,
    }

    # Dibujar cada campo con su fuente específica SIN OUTLINE
    for campo, texto in datos.items():
        if campo in styles:
            style = styles[campo]
            # Usar fuente específica del campo o la fuente por defecto
            fuente_campo = style.get("font", font_path)
            font = ImageFont.truetype(fuente_campo, style["size"])
            
            # Si es el campo "valor", centrarlo horizontalmente
            if campo == "valor":
                # Obtener el ancho del texto
                bbox = draw.textbbox((0, 0), str(texto), font=font)
                text_width = bbox[2] - bbox[0]
                
                # Calcular la posición X centrada
                # La coordenada X en config será el centro, no el inicio
                center_x = style["pos"][0]
                x_position = center_x - (text_width // 2)
                y_position = style["pos"][1]
                
                # Dibujar texto centrado
                draw.text((x_position, y_position), str(texto), font=font, fill=style["color"])
            elif campo in ["punto_venta", "nombre_enmascarado"]:
                # Manejar texto multilínea
                texto_str = str(texto)
                if "\n" in texto_str:
                    lineas = texto_str.split("\n")
                    x_pos = style["pos"][0]
                    y_pos = style["pos"][1]
                    # Ajustar el espaciado según el tamaño de fuente
                    line_height = int(style["size"] * 1.2)  # 20% más que el tamaño de fuente
                    
                    for i, linea in enumerate(lineas):
                        if linea.strip():  # Solo dibujar si hay texto
                            draw.text((x_pos, y_pos + (i * line_height)), linea, font=font, fill=style["color"])
                else:
                    draw.text(style["pos"], texto_str, font=font, fill=style["color"])
            else:
                # Dibujar texto normalmente para otros campos
                draw.text(style["pos"], str(texto), font=font, fill=style["color"])

    image.save(output_path, format='PNG', compress_level=1)
    return output_path


def generar_comprobante_nequi_bc(data, config):
    """
    Genera un comprobante de transferencia de Nequi a Bancolombia (usando generar_comprobante genérica)
    """
    # Usar la función genérica generar_comprobante que maneja todos los casos
    return generar_comprobante(data, config)


def generar_comprobante_nequi_ahorros(data, config):
    """
    Genera un comprobante de transferencia de Nequi Ahorros con nombres enmascarados
    """
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    font_path = config["font"]

    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Formatear valor
    valor_formateado = "$ {:,.2f}".format(float(data.get("valor", 0))).replace(",", "X").replace(".", ",").replace("X", ".")
    
    # Usar el número de cuenta proporcionado por el usuario
    numero_cuenta = data.get("numero_cuenta", "")
    
    # Generar referencia M + 7 dígitos
    referencia = f"M{random.randint(1000000, 9999999)}"
    
    # Generar fecha actual
    meses_es = {
        "january": "enero", "february": "febrero", "march": "marzo", "april": "abril",
        "may": "mayo", "june": "junio", "july": "julio", "august": "agosto",
        "september": "septiembre", "october": "octubre", "november": "noviembre", "december": "diciembre"
    }
    
    now = datetime.now(pytz.timezone("America/Bogota"))
    mes_en = now.strftime("%B").lower()
    mes = meses_es.get(mes_en, mes_en)
    fecha = now.strftime(f"%d de {mes} de %Y a las %I:%M %p").lower().replace("am", "a. m.").replace("pm", "p. m.")

    # Enmascarar nombre igual que en comprobante_nuevo
    nombre_mask = ofuscar_nombre(data.get("nombre", ""))
    
    # Datos a dibujar
    datos = {
        "nombre": nombre_mask,
        "valor": valor_formateado,
        "fecha": fecha,
        "banco": "Bancolombia",
        "numero_cuenta": numero_cuenta,
        "referencia": referencia,
        "disponible": "Disponible"
    }

    # Dibujar cada campo
    for campo, texto in datos.items():
        if campo in styles:
            style = styles[campo]
            font = ImageFont.truetype(font_path, style["size"])
            draw_text_with_outline(draw, style["pos"], str(texto), font, style["color"], "#2e2b33", 2)

    image.save(output_path, format='PNG', compress_level=1)
    return output_path


def generar_comprobante_daviplata(numero_daviplata: str, ultimos_4: str, valor: int) -> str:
    """Genera el comprobante de DaviPlata (configuración original con color #333333 y fuente Manrope-Bold del proyecto app)"""
    from config import COORDENADAS_DAVIPLATA, FUENTES_DAVIPLATA, RUTAS_DAVIPLATA, COLORES_DAVIPLATA
    
    plantilla = Image.open(RUTAS_DAVIPLATA['plantilla'])
    if plantilla.mode in ('RGBA', 'LA', 'P'):
        plantilla = plantilla.convert('RGB')
    
    draw = ImageDraw.Draw(plantilla)
    
    # Cargar fuentes Manrope del proyecto app (solo fuente cambiada)
    font_bold = ImageFont.truetype(RUTAS_DAVIPLATA['font_bold'], FUENTES_DAVIPLATA['bold'])
    font_medium = ImageFont.truetype(RUTAS_DAVIPLATA['font_medium'], FUENTES_DAVIPLATA['normal'])
    font_light = ImageFont.truetype(RUTAS_DAVIPLATA['font_light'], FUENTES_DAVIPLATA['light'])
    font_valor = ImageFont.truetype(RUTAS_DAVIPLATA['font_bold'], FUENTES_DAVIPLATA['valor'])
    font_hora = ImageFont.truetype(RUTAS_DAVIPLATA['font_medium'], FUENTES_DAVIPLATA['hora_esquina'])
    
    # Obtener fecha y hora actual (Colombia)
    colombia = pytz.timezone("America/Bogota")
    fecha_actual = datetime.now(colombia)
    
    # Hora en esquina (formato 12h sin ceros a la izquierda)
    hora_esquina = fecha_actual.strftime("%I:%M").lstrip("0")
    
    # Formato de valor con puntos ($ 32.000)
    valor_formateado = f"$ {valor:,}".replace(",", ".")
    
    # Generar desde ofuscado: DaviPlata - ******ultimos_4
    desde_ofuscado = f"DaviPlata - ******{ultimos_4}"
    
    # Fecha y hora de transacción (30/10/2025 - 06:24 pm)
    dia = fecha_actual.strftime("%d")
    mes = fecha_actual.strftime("%m")
    anio = fecha_actual.strftime("%Y")
    hora_transaccion = fecha_actual.strftime("%I:%M %p").lower()
    fecha_hora_transaccion = f"{dia}/{mes}/{anio} - {hora_transaccion}"
    
    # Número de aprobación aleatorio (6 dígitos)
    numero_aprobacion = f"{random.randint(100000, 999999):06d}"
    
    coordenadas = COORDENADAS_DAVIPLATA
    
    # Dibujar hora en esquina (blanca, pequeña)
    draw.text(coordenadas['hora_esquina'], hora_esquina, fill=COLORES_DAVIPLATA['hora'], font=font_hora)
    
    # Dibujar valor/cantidad (bold, #333333 del proyecto app, grande)
    draw.text(coordenadas['valor'], valor_formateado, fill=COLORES_DAVIPLATA['negro'], font=font_valor)
    
    # Dibujar número DaviPlata (bold, #333333 del proyecto app)
    draw.text(coordenadas['numero_daviplata'], numero_daviplata, fill=COLORES_DAVIPLATA['negro'], font=font_bold)
    
    # Dibujar desde ofuscado (bold, #333333 del proyecto app)
    draw.text(coordenadas['desde'], desde_ofuscado, fill=COLORES_DAVIPLATA['negro'], font=font_bold)
    
    # Dibujar fecha y hora de transacción (medium, #333333 del proyecto app)
    draw.text(coordenadas['fecha_hora_transaccion'], fecha_hora_transaccion, fill=COLORES_DAVIPLATA['negro'], font=font_medium)
    
    # Dibujar número de aprobación (bold, #333333 del proyecto app)
    draw.text(coordenadas['aprobacion'], numero_aprobacion, fill=COLORES_DAVIPLATA['negro'], font=font_bold)
    
    output_path = f"gen_{uuid.uuid4().hex}.png"
    plantilla.save(output_path, format='PNG', compress_level=1)
    logger.info(f"Comprobante DaviPlata generado: {numero_daviplata} - ${valor:,}")
    return output_path


def generar_comprobante_llaves_daviplata(data, config):
    """Genera comprobante de DaviPlata LLAVES con la plantilla Daviplata_llaves.jpg"""
    try:
        # Obtener directorio base del script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construir rutas absolutas para recursos (template y fuentes)
        template_path = os.path.join(base_dir, config["template"])
        # Output en directorio actual de trabajo (donde se ejecuta el bot)
        output_path = f"gen_{uuid.uuid4().hex}.png"
        styles = config["styles"]

        # Verificar que el template existe
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template no encontrado: {template_path}")

        image = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        # Formatear datos
        nombre = data.get("nombre", "").upper()  # Siempre en mayúsculas
        llave = data.get("llave", "")
        valor = data.get("valor", 0)
        desde = data.get("desde", "DaviPlata - ******0000")
        entidad_destino = data.get("entidad_destino", "")
        
        # Formatear valor con puntos
        try:
            valor_int = int(valor)
            valor_formateado = f"$ {valor_int:,}".replace(",", ".")
        except:
            valor_formateado = f"$ {valor}"
        
        # Generar fecha y hora en formato "Agosto 31 de 2025 - 01:13 a.m."
        now = datetime.now(pytz.timezone("America/Bogota"))
        dia = now.strftime("%d").lstrip("0")  # Quitar cero inicial si existe
        mes_num = now.strftime("%m")
        anio = now.strftime("%Y")
        hora = now.strftime("%I:%M %p").lower()
        
        # Diccionario de meses en español
        meses_es = {
            "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
            "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
            "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
        }
        mes_nombre = meses_es.get(mes_num, mes_num).capitalize()
        fecha_hora = f"{mes_nombre} {dia} de {anio} - {hora}"
        
        # Si tiene fecha manual, usarla
        if "fecha_manual_value" in data:
            fecha_hora = data["fecha_manual_value"]

        datos = {
            "nombre": nombre,
            "llave": llave,
            "valor": valor_formateado,
            "desde": desde,
            "entidad_destino": entidad_destino,
            "fecha": fecha_hora,
        }

        # Dibujar cada campo
        for campo, texto in datos.items():
            if campo in styles:
                style = styles[campo]
                fuente_campo = style.get("font", config["font"])
                # Construir ruta absoluta para la fuente
                # Si la fuente es relativa, construir ruta absoluta
                if not os.path.isabs(fuente_campo):
                    fuente_path = os.path.join(base_dir, fuente_campo)
                else:
                    fuente_path = fuente_campo
                
                # Verificar que la fuente existe
                if not os.path.exists(fuente_path):
                    logger.error(f"Fuente no encontrada: {fuente_path}")
                    raise FileNotFoundError(f"Fuente no encontrada: {fuente_path}")
                
                font = ImageFont.truetype(fuente_path, style["size"])
                draw.text(style["pos"], str(texto), font=font, fill=style["color"])

        image.save(output_path, format='PNG', compress_level=1)
        return output_path
    except FileNotFoundError as e:
        logger.error(f"Error de archivo no encontrado en Llaves DaviPlata: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generando Llaves DaviPlata: {str(e)}")
        raise

def generar_comprobante_anulado(data, config):
    """Genera un comprobante anulado usando la función genérica"""
    base_path = generar_comprobante(data, config)
    return base_path

def generar_movimiento_ahorros(data, config):
    """Genera movimiento BC a BC usando plantilla ahorros.jpg"""
    from datetime import datetime
    import pytz
    
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    
    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    
    # Formatear valor
    valor = abs(data.get("valor", 0))
    valor_str = f"{valor:,}".replace(",", ".")
    valor_parts = valor_str.split(".")
    valor_texto = valor_parts[0] + ","
    decimales = valor_parts[1][:2] if len(valor_parts) > 1 else "00"
    if len(decimales) < 2:
        decimales = decimales.ljust(2, "0")
    
    # Fuentes
    font_cop = ImageFont.truetype(styles["valor_cop"]["font"], styles["valor_cop"]["size"])
    font_dolar = ImageFont.truetype(styles["valor_dolar"]["font"], styles["valor_dolar"]["size"])
    font_valor = ImageFont.truetype(styles["valor_numero"]["font"], styles["valor_numero"]["size"])
    font_dec = ImageFont.truetype(styles["valor_decimal"]["font"], styles["valor_decimal"]["size"])
    font_fecha = ImageFont.truetype(styles["fecha"]["font"], styles["fecha"]["size"])
    font_negocio = ImageFont.truetype(styles["texto_negocio"]["font"], styles["texto_negocio"]["size"])
    
    # Posiciones base
    x_decimales = styles["x_decimales"]
    y_base = styles["y_base"]
    ajuste = 2
    ajuste_dec = 1
    
    # Medir anchos
    ancho_dec = draw.textlength(decimales, font=font_dec)
    ancho_valor = draw.textlength(valor_texto, font=font_valor)
    ancho_dolar = draw.textlength("-$", font=font_dolar)
    ancho_cop = draw.textlength("COP", font=font_cop)
    
    # Calcular posiciones
    x_valor = x_decimales - ancho_valor + ajuste
    x_dolar = x_valor - ancho_dolar - 5
    x_cop = x_dolar - ancho_cop - 5
    x_dec = x_decimales + ajuste_dec
    
    # Color
    color = "#F2879E"
    
    # Dibujar monto
    draw.text((x_cop, y_base), "COP", font=font_cop, fill=color)
    draw.text((x_dolar, y_base - 2), "-$", font=font_dolar, fill=color)
    draw.text((x_valor, y_base - 1), valor_texto, font=font_valor, fill=color)
    draw.text((x_dec, y_base + 3), decimales, font=font_dec, fill=color)
    
    # Dibujar fecha
    now = datetime.now(pytz.timezone("America/Bogota"))
    meses_abr = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    fecha_texto = f"{now.day} {meses_abr[now.month - 1]} {now.year}"
    draw.text(styles["fecha"]["pos"], fecha_texto, font=font_fecha, fill="white")
    
    # NO dibujar texto del negocio (se quitó "AHORROS" como se solicitó)
    
    image.save(output_path, format='PNG', compress_level=1)
    return output_path

def generar_movimiento_qr_bc(data, config):
    """Genera movimiento QR BC usando plantilla qr.jpg"""
    from datetime import datetime
    import pytz
    
    template_path = config["template"]
    output_path = f"gen_{uuid.uuid4().hex}.png"
    styles = config["styles"]
    
    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    
    # Formatear valor
    valor = abs(data.get("valor", 0))
    valor_str = f"{valor:,}".replace(",", ".")
    valor_parts = valor_str.split(".")
    valor_texto = valor_parts[0] + ","
    decimales = valor_parts[1][:2] if len(valor_parts) > 1 else "00"
    if len(decimales) < 2:
        decimales = decimales.ljust(2, "0")
    
    # Fuentes
    font_cop = ImageFont.truetype(styles["valor_cop"]["font"], styles["valor_cop"]["size"])
    font_dolar = ImageFont.truetype(styles["valor_dolar"]["font"], styles["valor_dolar"]["size"])
    font_valor = ImageFont.truetype(styles["valor_numero"]["font"], styles["valor_numero"]["size"])
    font_dec = ImageFont.truetype(styles["valor_decimal"]["font"], styles["valor_decimal"]["size"])
    font_fecha = ImageFont.truetype(styles["fecha"]["font"], styles["fecha"]["size"])
    font_negocio = ImageFont.truetype(styles["texto_negocio"]["font"], styles["texto_negocio"]["size"])
    
    # Posiciones base
    x_decimales = styles["x_decimales"]
    y_base = styles["y_base"]
    ajuste = 2
    ajuste_dec = 1
    
    # Medir anchos
    ancho_dec = draw.textlength(decimales, font=font_dec)
    ancho_valor = draw.textlength(valor_texto, font=font_valor)
    ancho_dolar = draw.textlength("-$", font=font_dolar)
    ancho_cop = draw.textlength("COP", font=font_cop)
    
    # Calcular posiciones
    x_valor = x_decimales - ancho_valor + ajuste
    x_dolar = x_valor - ancho_dolar - 5
    x_cop = x_dolar - ancho_cop - 5
    x_dec = x_decimales + ajuste_dec
    
    # Color
    color = "#F2879E"
    
    # Dibujar monto
    draw.text((x_cop, y_base), "COP", font=font_cop, fill=color)
    draw.text((x_dolar, y_base - 2), "-$", font=font_dolar, fill=color)
    draw.text((x_valor, y_base - 1), valor_texto, font=font_valor, fill=color)
    draw.text((x_dec, y_base + 3), decimales, font=font_dec, fill=color)
    
    # Dibujar fecha
    now = datetime.now(pytz.timezone("America/Bogota"))
    meses_abr = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    fecha_texto = f"{now.day} {meses_abr[now.month - 1]} {now.year}"
    draw.text(styles["fecha"]["pos"], fecha_texto, font=font_fecha, fill="white")
    
    # NO dibujar texto del negocio (se quitó "NEQUIVOUCH" como se solicitó)
    
    image.save(output_path, format='PNG', compress_level=1)
    return output_path