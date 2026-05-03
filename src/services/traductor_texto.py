from src.config import DATABASE_PATH
from src.database.connection import get_connection, initialize_database
from src.services.normalizacion import normalizar_texto, tokenizar


def _cargar_catalogo():
    if not DATABASE_PATH.exists():
        initialize_database()

    with get_connection() as conexion:
        senas = conexion.execute(
            """
            SELECT s.id, s.palabra AS texto, c.nombre AS categoria, 'palabra' AS tipo
            FROM senas s
            JOIN categorias c ON c.id = s.categoria_id
            WHERE s.activo = 1
            """
        ).fetchall()
        frases = conexion.execute(
            """
            SELECT f.id, f.texto, c.nombre AS categoria, 'frase' AS tipo
            FROM frases f
            JOIN categorias c ON c.id = f.categoria_id
            WHERE f.activo = 1
            """
        ).fetchall()
        sinonimos = conexion.execute(
            """
            SELECT sn.texto, s.palabra AS sena_texto, f.texto AS frase_texto,
                   COALESCE(cs.nombre, cf.nombre) AS categoria,
                   CASE WHEN sn.sena_id IS NULL THEN 'frase' ELSE 'palabra' END AS tipo
            FROM sinonimos sn
            LEFT JOIN senas s ON s.id = sn.sena_id
            LEFT JOIN frases f ON f.id = sn.frase_id
            LEFT JOIN categorias cs ON cs.id = s.categoria_id
            LEFT JOIN categorias cf ON cf.id = f.categoria_id
            """
        ).fetchall()

    catalogo = {}
    for fila in [*senas, *frases]:
        texto = normalizar_texto(fila["texto"])
        catalogo[texto] = {
            "texto": texto,
            "categoria": fila["categoria"],
            "tipo": fila["tipo"],
            "encontrado_por": texto,
        }

    for fila in sinonimos:
        sinonimo = normalizar_texto(fila["texto"])
        texto_base = normalizar_texto(fila["sena_texto"] or fila["frase_texto"])
        catalogo[sinonimo] = {
            "texto": texto_base,
            "categoria": fila["categoria"],
            "tipo": fila["tipo"],
            "encontrado_por": sinonimo,
        }

    return catalogo


def traducir_texto(texto):
    catalogo = _cargar_catalogo()
    palabras = tokenizar(texto)
    resultado = []
    i = 0

    while i < len(palabras):
        mejor = None
        mejor_largo = 0

        for largo in range(min(5, len(palabras) - i), 0, -1):
            candidato = " ".join(palabras[i : i + largo])
            if candidato in catalogo:
                mejor = catalogo[candidato]
                mejor_largo = largo
                break

        if mejor:
            resultado.append({**mejor, "estado": "encontrada"})
            i += mejor_largo
        else:
            palabra = palabras[i]
            resultado.append(
                {
                    "texto": palabra,
                    "categoria": "alfabeto",
                    "tipo": "deletreo",
                    "estado": "deletrear",
                    "letras": list(palabra),
                    "encontrado_por": palabra,
                }
            )
            i += 1

    return resultado
