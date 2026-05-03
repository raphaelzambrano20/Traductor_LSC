import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_connection, initialize_database
from src.services.normalizacion import normalizar_texto


def listar_categorias():
    initialize_database()
    with get_connection() as conexion:
        return [
            dict(fila)
            for fila in conexion.execute(
                "SELECT id, nombre, descripcion FROM categorias ORDER BY nombre"
            )
        ]


def registrar_categoria(nombre, descripcion=""):
    nombre = normalizar_texto(nombre)
    if not nombre:
        raise ValueError("La categoria no puede estar vacia.")

    initialize_database()
    with get_connection() as conexion:
        conexion.execute(
            """
            INSERT INTO categorias (nombre, descripcion)
            VALUES (?, ?)
            ON CONFLICT(nombre) DO UPDATE SET descripcion = categorias.descripcion
            """,
            (nombre, descripcion),
        )
        return conexion.execute(
            "SELECT id FROM categorias WHERE nombre = ?", (nombre,)
        ).fetchone()["id"]


def registrar_sena(palabra, categoria, sinonimos=None):
    palabra = normalizar_texto(palabra)
    categoria = normalizar_texto(categoria)
    sinonimos = sinonimos or []

    if not palabra:
        raise ValueError("La sena no puede estar vacia.")
    if not categoria:
        raise ValueError("La categoria no puede estar vacia.")

    categoria_id = registrar_categoria(categoria)
    with get_connection() as conexion:
        conexion.execute(
            """
            INSERT INTO senas (palabra, categoria_id)
            VALUES (?, ?)
            ON CONFLICT(palabra) DO UPDATE SET categoria_id = excluded.categoria_id
            """,
            (palabra, categoria_id),
        )
        sena_id = conexion.execute(
            "SELECT id FROM senas WHERE palabra = ?", (palabra,)
        ).fetchone()["id"]

        for sinonimo in sinonimos:
            sinonimo = normalizar_texto(sinonimo)
            if sinonimo and sinonimo != palabra:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO sinonimos (sena_id, texto)
                    VALUES (?, ?)
                    """,
                    (sena_id, sinonimo),
                )

    return palabra


def obtener_sinonimos_sena(palabra):
    palabra = normalizar_texto(palabra)
    if not palabra:
        return []

    initialize_database()
    with get_connection() as conexion:
        filas = conexion.execute(
            """
            SELECT sn.texto
            FROM sinonimos sn
            JOIN senas s ON s.id = sn.sena_id
            WHERE s.palabra = ?
            ORDER BY sn.id
            """,
            (palabra,),
        ).fetchall()

    return [fila["texto"] for fila in filas if normalizar_texto(fila["texto"]) != palabra]


def obtener_sena(palabra):
    palabra = normalizar_texto(palabra)
    if not palabra:
        return None

    initialize_database()
    with get_connection() as conexion:
        fila = conexion.execute(
            """
            SELECT s.palabra, c.nombre AS categoria
            FROM senas s
            JOIN categorias c ON c.id = s.categoria_id
            WHERE s.palabra = ?
            """,
            (palabra,),
        ).fetchone()

    return dict(fila) if fila else None
