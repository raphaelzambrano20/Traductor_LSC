from src.services.normalizacion import normalizar_texto
from src.services.recursos_lsc import convertir_a_data_uri, obtener_recurso_item


def _buscar_recurso_visual(texto, tipo):
    texto = normalizar_texto(texto)
    if not texto or tipo == "deletreo":
        return None, None, None

    recurso = obtener_recurso_item(texto, tipo)
    if not recurso:
        return None, None, None

    return recurso["tipo"], recurso["ruta"], convertir_a_data_uri(recurso["ruta"])


def construir_secuencia_avatar(traduccion):
    pasos = []

    for item in traduccion:
        if item["estado"] == "deletrear":
            for letra in item.get("letras", []):
                pasos.append(
                    {
                        "texto": letra.upper(),
                        "categoria": "alfabeto",
                        "tipo": "letra",
                        "estado": "avatar_basico",
                        "recurso_tipo": None,
                        "ruta": None,
                    }
                )
            continue

        recurso_tipo, ruta, data_uri = _buscar_recurso_visual(item["texto"], item["tipo"])
        pasos.append(
            {
                "texto": item["texto"],
                "categoria": item["categoria"],
                "tipo": item["tipo"],
                "estado": "recurso_visual" if ruta else "avatar_basico",
                "recurso_tipo": recurso_tipo,
                "ruta": ruta,
                "recurso_data": data_uri,
            }
        )

    return pasos
