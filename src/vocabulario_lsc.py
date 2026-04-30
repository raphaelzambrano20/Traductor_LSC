VOCABULARIO_INICIAL_LSC = [
    "hola",
    "gracias",
    "si",
    "no",
    "ayuda",
    "profesor",
    "estudiante",
    "buenos_dias",
    "permiso",
    "por_favor",
]


def normalizar_etiqueta(texto):
    return texto.strip().lower().replace(" ", "_")
