# Configuración para comprobante Nequi
COMPROBANTE1_CONFIG = {
    "template": "img/plantilla_nequi.jpg",
    "output": "comprobante_generado.jpg",
    "styles": {
        "nombre": {"size": 83, "color": "#200021", "pos": (200, 2320)},
        "valor1": {"size": 83, "color": "#200021", "pos": (200, 2660)},
        "telefono": {"size": 83, "color": "#200021", "pos": (200, 3000)},
        "fecha": {"size": 83, "color": "#200021", "pos": (200, 3320)},
        "referencia": {"size": 83, "color": "#200021", "pos": (200, 3650)},
        "disponible": {"size": 83, "color": "#200021", "pos": (200, 3990)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para comprobante BRE-B
COMPROBANTE4_CONFIG = {
    "template": "img/plantilla_bre-b.jpg",
    "output": "comprobante4_generado.png",
    "styles": {
        "nombre": {"size": 80, "color": "#2e2b33", "pos": (180, 2250)},
        "llave": {"size": 80, "color": "#2e2b33", "pos": (180, 2550)},
        "banco_destino": {"size": 80, "color": "#2e2b33", "pos": (180, 2830)},
        "fecha": {"size": 80, "color": "#2e2b33", "pos": (180, 3120)},
        "valor1": {"size": 80, "color": "#2e2b33", "pos": (180, 3420)},
        "referencia": {"size": 80, "color": "#2e2b33", "pos": (180, 3700)},
        "numero_envio": {"size": 80, "color": "#2e2b33", "pos": (180, 4000)},
        "disponible": {"size": 80, "color": "#2e2b33", "pos": (180, 4280)},
        "hora_esquina": {"size": 80, "color": "#FFFFFF", "pos": (90, 40)},
    },
    "font": "fuentes/Manrope-Medium.ttf"
}

# Configuración para movimiento Nequi
COMPROBANTE_MOVIMIENTO_CONFIG = {
    "template": "img/movement.jpg",
    "output": "comprobante_movimiento_generado.png",
    "styles": {
        "nombre": {"size": 16, "color": "#262626", "pos": (78, 340), "font": "fuentes/Manrope-Medium.ttf"},  # Nota: fuente redundante, se usa "font" del nivel superior si no se especifica
        "valor1": {"size": 18, "color": "#C85C6E", "pos": (323, 355), "max_width": 200, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 26, "color": "#C85C6E", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
        "hora_esquina": {"size": 22, "color": "#FFFFFF", "pos": (19, 13)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para movimiento BRE-B (638x1280)
COMPROBANTE_MOVIMIENTO2_CONFIG = {
    "template": "img/movements_bre-b.jpg",
    "output": "comprobante_movimiento2_generado.png",
    "styles": {
        "nombre": {"size": 18, "color": "#262626", "pos": (88, 320), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 20, "color": "#C85C6E", "pos": (595, 345), "max_width": 170, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 17, "color": "#C85C6E", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
        "hora_esquina": {"size": 11, "color": "#FFFFFF", "pos": (25, 13)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para comprobante QR
COMPROBANTE_QR_CONFIG = {
    "template": "img/plantillaqr.jpg",
    "output": "comprobante_qr_generado.png",
    "styles": {
        "nombre": {"size": 80, "color": "#2e2b33", "pos": (180, 2250)},
        "llave": {"size": 80, "color": "#2e2b33", "pos": (180, 2550)},
        "banco_destino": {"size": 80, "color": "#2e2b33", "pos": (180, 2830)},
        "fecha": {"size": 80, "color": "#2e2b33", "pos": (180, 3120)},
        "valor1": {"size": 80, "color": "#2e2b33", "pos": (180, 3420)},
        "referencia": {"size": 80, "color": "#2e2b33", "pos": (180, 3700)},
        "numero_envio": {"size": 80, "color": "#2e2b33", "pos": (180, 4000)},
        "disponible": {"size": 80, "color": "#2e2b33", "pos": (180, 4280)},
        "hora_esquina": {"size": 80, "color": "#FFFFFF", "pos": (90, 40)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para movimiento QR BC (del proyecto app)
COMPROBANTE_MOVIMIENTO3_CONFIG = {
    "template": "img/comprobante_movimiento3.jpg",
    "output": "comprobante_movimiento3_generado.png",
    "styles": {
        "nombre": {"size": 18, "color": "#1b0b19", "pos": (87, 324), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 21, "color": "#b14253", "pos": (570, 333), "max_width": 200, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 26, "color": "#b14253", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
    },
    "font": "fuentes/Manrope-Medium.ttf"
}

# Configuración para comprobante Llave (usa las mismas coordenadas que QR)
COMPROBANTE_LLAVE = {
    "template": "img/plantilla_llaves.jpg",
    "output": "comprobante_llave_generado.png",
    "styles": {
        "nombre": {"size": 80, "color": "#2e2b33", "pos": (180, 2250)},
        "llave": {"size": 80, "color": "#2e2b33", "pos": (180, 2550)},
        "banco_destino": {"size": 80, "color": "#2e2b33", "pos": (180, 2830)},
        "fecha": {"size": 80, "color": "#2e2b33", "pos": (180, 3120)},
        "valor1": {"size": 80, "color": "#2e2b33", "pos": (180, 3420)},
        "referencia": {"size": 80, "color": "#2e2b33", "pos": (180, 3700)},
        "numero_envio": {"size": 80, "color": "#2e2b33", "pos": (180, 4000)},
        "disponible": {"size": 80, "color": "#2e2b33", "pos": (180, 4280)},
        "hora_esquina": {"size": 80, "color": "#FFFFFF", "pos": (90, 40)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para comprobante NQ QR Normal
COMPROBANTE_NQ_QR_NORMAL_CONFIG = {
    "template": "img/qr_nequinormal.png",
    "output": "comprobante_nq_qr_normal_generado.png",
    "styles": {
        "nombre": {"size": 85, "color": "#2e2b33", "pos": (273, 2114), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 85, "color": "#2e2b33", "pos": (273, 2510), "font": "fuentes/Manrope-Medium.ttf"},
        "fecha": {"size": 85, "color": "#2e2b33", "pos": (273, 2870), "font": "fuentes/Manrope-Medium.ttf"},
        "referencia": {"size": 85, "color": "#2e2b33", "pos": (273, 3250), "font": "fuentes/Manrope-Medium.ttf"},
        "disponible": {"size": 85, "color": "#2e2b33", "pos": (273, 3640), "font": "fuentes/Manrope-Medium.ttf"},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para movimiento NQ QR Normal
MOVIMIENTO_NQ_QR_NORMAL_CONFIG = {
    "template": "img/movement.jpg",
    "output": "movimiento_nq_qr_normal_generado.png",
    "styles": {
        "nombre": {"size": 16, "color": "#262626", "pos": (78, 340), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 18, "color": "#C85C6E", "pos": (323, 355), "max_width": 200, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 26, "color": "#C85C6E", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
        "hora_esquina": {"size": 22, "color": "#FFFFFF", "pos": (19, 13)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para comprobante Anulado
COMPROBANTE_ANULADO_CONFIG = {
    "template": "img/anulado.jpg",
    "output": "comprobante_anulado.png",
    "styles": {
        "nombre": {"size": 22, "color": "#200021", "pos": (48, 278)},
        "valor1": {"size": 22, "color": "#200021", "pos": (48, 358)},
        "fecha": {"size": 22, "color": "#200021", "pos": (48, 443)},
        "referencia": {"size": 22, "color": "#200021", "pos": (48, 524)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# Configuración para movimiento BC a BC (ahorros.jpg)
MOVIMIENTO_AHORROS_CONFIG = {
    "template": "img/ahorros.jpg",
    "output": "movimiento_ahorros_generado.png",
    "styles": {
        "fecha": {"size": 18, "color": "#FFFFFF", "pos": (25, 643), "font": "fuentes/opensans_semibold.ttf"},
        "texto_negocio": {"size": 23, "color": "#FFFFFF", "pos": (197, 667), "font": "fuentes/opensans_regular.ttf"},
        "valor_cop": {"size": 18, "color": "#F2879E", "pos": (0, 716), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_dolar": {"size": 24, "color": "#F2879E", "pos": (0, 714), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_numero": {"size": 23, "color": "#F2879E", "pos": (0, 715), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_decimal": {"size": 17, "color": "#F2879E", "pos": (533, 719), "font": "fuentes/cibfontsans_bold.ttf"},
        "x_decimales": 532,
        "y_base": 716,
    },
    "font": "fuentes/cibfontsans_bold.ttf",
}

# Configuración para movimiento QR BC (qr.jpg)
MOVIMIENTO_QR_BC_CONFIG = {
    "template": "img/qr.jpg",
    "output": "movimiento_qr_bc_generado.png",
    "styles": {
        "fecha": {"size": 18, "color": "#FFFFFF", "pos": (25, 643), "font": "fuentes/opensans_semibold.ttf"},
        "texto_negocio": {"size": 23, "color": "#FFFFFF", "pos": (197, 667), "font": "fuentes/opensans_regular.ttf"},
        "valor_cop": {"size": 18, "color": "#F2879E", "pos": (0, 716), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_dolar": {"size": 24, "color": "#F2879E", "pos": (0, 714), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_numero": {"size": 23, "color": "#F2879E", "pos": (0, 715), "font": "fuentes/cibfontsans_bold.ttf"},
        "valor_decimal": {"size": 17, "color": "#F2879E", "pos": (533, 719), "font": "fuentes/cibfontsans_bold.ttf"},
        "x_decimales": 532,
        "y_base": 716,
    },
    "font": "fuentes/cibfontsans_bold.ttf",
}

COMPROBANTE_NEQUI_BANCOLOMBIA =  {
    "template": "img/nequi_a_bancol.jpg",
    "output": "comprobante_movimiento_generado.png",
    "styles": {
        "nombre": {"size": 20, "color": "#2e2b33", "pos": (43, 513), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 20, "color": "#2e2b33", "pos": (43, 590)},
        "hora_esquina": {"size": 22, "color": "#FFFFFF", "pos": (19, 13)},
        "fecha": {"size": 20, "color": "#2e2b33", "pos": (43, 664)},
        "banco": {"size": 20, "color": "#2e2b33", "pos": (43, 735), "font": "fuentes/Manrope-Medium.ttf"},
        "cuenta": {"size": 20, "color": "#2e2b33", "pos": (43, 811), "font": "fuentes/Manrope-Medium.ttf"},
        "referencia": {"size": 20, "color": "#2e2b33", "pos": (44, 885)},
        "disponible": {"size": 20, "color": "#2e2b33", "pos": (43, 963)},
       
    },
    "font": "fuentes/Manrope-Medium.ttf"
}
# Configuración para movimiento QR
BANCOL_MOVIMIENTO_CONFIG = {
    "template": "img/bancol_movement.jpg",  # Confirmado: usa '/' para compatibilidad con Zeabur
    "output": "comprobante_movimiento3_generado.png",
    "styles": {
        "nombre": {"size": 16, "color": "#272727", "pos": (78, 340), "font": "fuentes/Manrope-Medium.ttf"},  # Nota: fuente redundante
        "valor1": {"size": 18, "color": "#C85C6E", "pos": (323, 355), "max_width": 200, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 26, "color": "#C85C6E", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
        "hora_esquina": {"size": 18, "color": "#FFFFFF", "pos": (19, 13)},
    },
    "font": "fuentes/Manrope-Medium.ttf"
}


MOVIMIENTO_LLAVE_CONFIG = {
    "template": "img/movement_llave.jpg",
    "output": "comprobante_movimiento_generado.png",
    "styles": {
        "nombre": {"size": 16, "color": "#262626", "pos": (78, 340), "font": "fuentes/Manrope-Medium.ttf"},  # Nota: fuente redundante, se usa "font" del nivel superior si no se especifica
        "valor1": {"size": 18, "color": "#C85C6E", "pos": (323, 355), "max_width": 200, "font": "fuentes/Manrope-Bold.ttf"},
        "valor_decimal": {"size": 26, "color": "#C85C6E", "pos": (0, 0), "font": "fuentes/Manrope-Bold.ttf"},
        "hora_esquina": {"size": 22, "color": "#FFFFFF", "pos": (19, 13)},
    },
    "font": "fuentes/Manrope-Medium.ttf",
}

# ====================================================================
# CONFIGURACIONES BOT BANCOLOMBIA
# ====================================================================

# ✅ Configuración para comprobante de Ahorros (bc_a_bc.png) - del proyecto BOTSITECOL
COMPROBANTE_AHORROS_CONFIG = {
    "template": "img/bc_a_bc.png",
    "output": "comprobante_ahorros_generado.png",
    "styles": {
        "fecha_esquina": {"size": 36, "color": "#FFFFFF", "pos": (20, 33), "font": "fuentes/opensans_semibold.ttf"},
        "comprobante_no": {"size": 35, "color": "#FFFFFF", "pos": (575, 572), "font": "fuentes/opensans_regular.ttf"},
        "fecha": {"size": 32, "color": "#FFFFFF", "pos": (318, 628), "font": "fuentes/opensans_regular.ttf"},
        "valor_transferencia": {"size": 48, "color": "#FFFFFF", "pos": (78, 1010), "font": "fuentes/cibfontsans_bold.ttf"},
        "costo_transferencia": {"size": 48, "color": "#FFFFFF", "pos": (78, 1178), "font": "fuentes/cibfontsans_bold.ttf"},
        "nombre": {"size": 48, "color": "#FFFFFF", "pos": (88, 1500), "font": "fuentes/cibfontsans_bold.ttf"},
        "referencia_transferencia": {"size": 40, "color": "#FFFFFF", "pos": (88, 2044), "font": "fuentes/opensans_semibold.ttf"},
        "numero_cuenta": {"size": 40, "color": "#FFFFFF", "pos": (85, 1605), "font": "fuentes/opensans_semibold.ttf"},
    },
    "font": "fuentes/cibfontsans_regular.ttf",
}

# ✅ Configuración para comprobante de Ahorros (bancol.jpg) - del proyecto app
COMPROBANTE_AHORROS2_CONFIG = {
    "template": "img/bancol.jpg",
    "output": "comprobante_ahorros2_generado.png",
    "styles": {
        "nombre": {"size": 58, "color": "#FFFFFF", "pos": (94, 1645), "font": "fuentes/cibfontsans_regular.ttf"},
        "numero_cuenta": {"size": 46, "color": "#FFFFFF", "pos": (96, 1750), "font": "fuentes/opensans_semibold.ttf"},
        "valor": {"size": 62, "color": "#FFFFFF", "pos": (135, 1095), "font": "fuentes/cibfontsans_regular.ttf"},
        "fecha": {"size": 45, "color": "#FFFFFF", "pos": (344, 687), "font": "fuentes/opensans_semibold.ttf"},
    },
    "font": "fuentes/cibfontsans_regular.ttf",
}

# ✅ Configuración para comprobante BC a NQ y T (del proyecto app)
COMPROBANTE_BC_NQ_T_CONFIG = {
    "template": "img/bcnd.jpg",
    "output": "comprobante_bc_nq_t_generado.png",
    "styles": {
        "numero_cuenta": {"size": 46, "color": "#FFFFFF", "pos": (96, 2052), "font": "fuentes/opensans_semibold.ttf"},
        "valor": {"size": 62, "color": "#FFFFFF", "pos": (144, 1628), "font": "fuentes/cibfontsans_regular.ttf"},
        "fecha": {"size": 45, "color": "#FFFFFF", "pos": (325, 545), "font": "fuentes/opensans_semibold.ttf"},
    },
    "font": "fuentes/cibfontsans_regular.ttf",
}

# ✅ Configuración para comprobante QR BC (nueva plantilla qr_bancolombia_bre-b.png)
COORDENADAS_QR_BC = {
    'comprobante_no': (1236, 1310),   # Comprobante No. (12 caracteres aleatorios)
    'fecha': (780, 1420),             # Fecha formato "24 dic. 2025 - 08:28 a.m."
    'valor': (950, 1870),             # Valor del pago ($ 100.000)
    'costo_pago': (1080, 2280),       # Costo del pago ($ 0,00)
    'punto_venta': (1210, 2810),      # Punto de venta (nombre negocio sin ofuscar)
    'enviado_a': (1210, 3024),        # Enviado a (nombre ofuscado MIZ*** ES***)
    'cuenta_ahorros': (1870, 3870),   # Cuenta de Ahorros (*2231)
    'limite_derecho': 2852,           # Límite derecho que no se debe sobrepasar
}

FUENTES_BC = {
    'normal': 70,
    'fecha': 65,
    'valor': 110,
    'costo': 60,
}

RUTAS_BC = {
    'plantilla_qr_bc': 'img/qr_bancolombia_bre-b.png',
    'font': 'fuentes/cibfontsans_bold.ttf',
}

COLORES_BC = {
    'texto': '#000000',  # Negro para punto de venta, enviado a, valor
}

# ✅ Configuración original para comprobante BC a Nequi
COORDENADAS_NEQUI_BC = {
    'hora': (20, 14),
    'fecha': (211, 268),
    'valor': (48, 690),
    'numero': (50, 845),
    'comprobante': (314, 234),
    'cuenta_ahorros': (50, 1035),
    'nombre': (50, 1010),
}

FUENTES_NEQUI_BC = {
    'hora': 18,
    'numero': 20,
    'valor': 22,
    'fecha': 16,
    'nombre': 18,
    'comprobante': 17,
    'cuenta_ahorros': 20,
}

COLORES_NEQUI_BC = {
    'hora': (255, 255, 255),
    'numero': (255, 255, 255),
    'valor': (255, 255, 255),
    'fecha': (160, 160, 160),
    'comprobante': (160, 160, 160),
    'cuenta_ahorros': (255, 255, 255),
}

RUTAS_NEQUI_BC = {
    'plantilla': 'img/bc_a_nequi.jpg',
    'font': 'fuentes/cibfontsans_bold.ttf',
}

# Configuración para movimientos BC a Nequi
COORDENADAS_MOVIMIENTOS_NEQUI_BC = {
    'fecha': (28, 644),
    'cuenta_ahorros': (26, 358),
    'cop': (394, 720),
    'saldo_negativo': (432, 723),
    'saldo_disponible': (404, 360),
}

FUENTES_MOVIMIENTOS_NEQUI_BC = {
    'fecha': 18,
    'cuenta_ahorros': 24,
    'saldo_negativo': 26,
    'saldo_disponible': 28,
}

COLORES_MOVIMIENTOS_NEQUI_BC = {
    'fecha': (255, 255, 255),
    'cuenta_ahorros': (255, 255, 255),
    'saldo_negativo': (255, 156, 176),
    'saldo_disponible': (255, 255, 255),
}

RUTAS_MOVIMIENTOS_NEQUI_BC = {
    'plantilla': 'img/movements_nequi_bc.jpg',
    'font': 'fuentes/cibfontsans_bold.ttf',
}

# ✅ Configuración original para comprobante Nequi a Bancolombia (del proyecto PruebaNqcsst)
COMPROBANTE_NEQUI_BC_CONFIG = {
    "template": "img/nequi_a_bancol.jpg",
    "output": "comprobante_nequi_bc_generado.png",
    "styles": {
        "nombre": {"size": 20, "color": "#2e2b33", "pos": (43, 513), "font": "fuentes/Manrope-Medium.ttf"},
        "valor1": {"size": 20, "color": "#2e2b33", "pos": (43, 590)},
        "hora_esquina": {"size": 22, "color": "#FFFFFF", "pos": (19, 13)},
        "fecha": {"size": 20, "color": "#2e2b33", "pos": (43, 664)},
        "banco": {"size": 20, "color": "#2e2b33", "pos": (43, 735), "font": "fuentes/Manrope-Medium.ttf"},
        "cuenta": {"size": 20, "color": "#2e2b33", "pos": (43, 811), "font": "fuentes/Manrope-Medium.ttf"},
        "referencia": {"size": 20, "color": "#2e2b33", "pos": (44, 885)},
        "disponible": {"size": 20, "color": "#2e2b33", "pos": (43, 963)},
    },
    "font": "fuentes/Manrope-Medium.ttf"
}

# ✅ Configuración para comprobante Nequi Ahorros (con nombres enmascarados)
COMPROBANTE_NEQUI_AHORROS_CONFIG = {
    "template": "img/bc.png",
    "output": "comprobante_nequi_ahorros_generado.png",
    "styles": {
        "nombre": {"size": 22, "color": "#200021", "pos": (48, 562)},
        "valor": {"size": 22, "color": "#200021", "pos": (48, 652)},
        "fecha": {"size": 22, "color": "#200021", "pos": (48, 732)},
        "banco": {"size": 22, "color": "#200021", "pos": (48, 813)},
        "numero_cuenta": {"size": 22, "color": "#200021", "pos": (48, 897)},
        "referencia": {"size": 22, "color": "#200021", "pos": (48, 979)},
        "disponible": {"size": 22, "color": "#200021", "pos": (48, 1065)},
    },
    "font": "fuentes/Manrope-Medium.ttf"
}

# ====================================================================
# ====================================================================
# CONFIGURACIÓN DAVIPLATA (original, solo con color #333333 y fuente Manrope del proyecto app)
# ====================================================================

COORDENADAS_DAVIPLATA = {
    'hora_esquina': (34, 33),
    'numero_daviplata': (68, 362),  # Número DaviPlata de 12 dígitos - despegado +8px
    'valor': (68, 490),  # Cantidad/valor ($ 32.000)
    'desde': (68, 589),  # Desde ofuscado (DaviPlata - ******0962)
    'fecha_hora_transaccion': (70, 749),  # Fecha y hora
    'aprobacion': (68, 820),  # Número de aprobación (005337)
}

FUENTES_DAVIPLATA = {
    'hora_esquina': 18,
    'valor': 32,  # Valor grande y destacado
    'bold': 22,   # Textos importantes en negro
    'normal': 20, # Textos normales
    'light': 18,  # Etiquetas en gris
}

RUTAS_DAVIPLATA = {
    'plantilla': 'img/plantilla_davi.jpg',
    'font_bold': 'fuentes/Manrope-Bold.ttf',      # Bold del proyecto app (solo fuente cambiada)
    'font_medium': 'fuentes/Manrope-Medium.ttf',    # Medium del proyecto app (solo fuente cambiada)
    'font_roman': 'fuentes/Manrope-Medium.ttf',  # Roman del proyecto app (solo fuente cambiada)
    'font_light': 'fuentes/Manrope-Light.ttf',     # Light del proyecto app (solo fuente cambiada)
}

COLORES_DAVIPLATA = {
    'negro': (51, 51, 51),        # #333333 del proyecto app (solo color cambiado)
    'gris': (128, 128, 128),   # Gris para etiquetas (mantener original)
    'hora': (255, 255, 255),   # Blanco para la hora en esquina
}

# ====================================================================
# CONFIGURACIÓN DAVIPLATA LLAVES
# ====================================================================

COMPROBANTE_LLAVES_DAVIPLATA_CONFIG = {
    "template": "img/Daviplata_llaves.jpg",
    "output": "comprobante_llaves_daviplata_generado.png",
    "styles": {
        "nombre": {"size": 100, "color": "#413f3d", "pos": (350, 1740), "font": "fuentes/roboto_bold.ttf"},
        "llave": {"size": 100, "color": "#413f3d", "pos": (350, 1850), "font": "fuentes/roboto_bold.ttf"},
        "valor": {"size": 125, "color": "#413f3d", "pos": (360, 2550), "font": "fuentes/roboto_bold.ttf"},
        "desde": {"size": 125, "color": "#413f3d", "pos": (360, 3060), "font": "fuentes/roboto_bold.ttf"},
        "entidad_destino": {"size": 125, "color": "#413f3d", "pos": (360, 3480), "font": "fuentes/roboto_bold.ttf"},
        "fecha": {"size": 100, "color": "#413f3d", "pos": (360, 4390), "font": "fuentes/roboto_bold.ttf"},
    },
    "font": "fuentes/roboto_regular.ttf",
}

# ====================================================================
# CONFIGURACIÓN QR DAVIPLATA (Negocios)
# ====================================================================

COMPROBANTE_QR_DAVIPLATA_CONFIG = {
    "template": "img/qr_negociosdaviplata.png",
    "output": "comprobante_qr_daviplata_generado.png",
    "styles": {
        "compra_en": {"size": 85, "color": "#413f3d", "pos": (250, 2230), "font": "fuentes/roboto_bold.ttf"},
        "cantidad": {"size": 85, "color": "#413f3d", "pos": (260, 2710), "font": "fuentes/roboto_bold.ttf"},
        "desde": {"size": 85, "color": "#413f3d", "pos": (260, 3400), "font": "fuentes/roboto_bold.ttf"},
        "fecha": {"size": 85, "color": "#413f3d", "pos": (250, 3730), "font": "fuentes/roboto_bold.ttf"},
        "aprobacion": {"size": 85, "color": "#413f3d", "pos": (250, 4040), "font": "fuentes/roboto_bold.ttf"},
        "costo": {"size": 85, "color": "#413f3d", "pos": (250, 4360), "font": "fuentes/roboto_bold.ttf"},
    },
    "font": "fuentes/roboto_bold.ttf",
}
