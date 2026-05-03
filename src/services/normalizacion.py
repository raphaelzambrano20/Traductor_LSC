import re
import unicodedata


def normalizar_texto(texto):
    texto = texto.strip().lower().replace("_", " ")
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9ñ\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto):
    texto = normalizar_texto(texto)
    return texto.split() if texto else []
