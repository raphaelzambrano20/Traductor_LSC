import base64
import mimetypes
import re
from pathlib import Path

from src.config import PROJECT_ROOT
from src.database.connection import get_connection, initialize_database
from src.services.normalizacion import normalizar_texto


DATA_VIDEOS_DIR = PROJECT_ROOT / "data" / "videos"
DATA_IMAGENES_DIR = PROJECT_ROOT / "data" / "imagenes"
EXTENSIONES_VIDEO = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES_EMBEBIDOS = 18 * 1024 * 1024


def _nombre_archivo_seguro(texto):
    texto = normalizar_texto(texto).replace(" ", "_")
    texto = re.sub(r"[^a-z0-9_]+", "", texto)
    return texto or "recurso"


def _ruta_relativa(ruta):
    return Path(ruta).resolve().relative_to(PROJECT_ROOT).as_posix()


def _ruta_absoluta(ruta):
    if not ruta:
        return None

    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = PROJECT_ROOT / ruta

    return ruta if ruta.exists() else None


def listar_items_lsc():
    initialize_database()
    with get_connection() as conexion:
        senas = conexion.execute(
            """
            SELECT s.palabra AS texto, 'palabra' AS tipo, c.nombre AS categoria,
                   s.ruta_video, s.ruta_imagen
            FROM senas s
            JOIN categorias c ON c.id = s.categoria_id
            WHERE s.activo = 1
            ORDER BY c.nombre, s.palabra
            """
        ).fetchall()
        frases = conexion.execute(
            """
            SELECT f.texto, 'frase' AS tipo, c.nombre AS categoria,
                   f.ruta_video, NULL AS ruta_imagen
            FROM frases f
            JOIN categorias c ON c.id = f.categoria_id
            WHERE f.activo = 1
            ORDER BY c.nombre, f.texto
            """
        ).fetchall()

    return [dict(fila) for fila in [*senas, *frases]]


def guardar_archivo_recurso(archivo, texto, tipo_item, tipo_recurso):
    texto = normalizar_texto(texto)
    tipo_item = str(tipo_item).strip().lower()
    tipo_recurso = str(tipo_recurso).strip().lower()

    if tipo_item not in {"palabra", "frase"}:
        raise ValueError("El tipo debe ser palabra o frase.")
    if tipo_recurso not in {"video", "imagen"}:
        raise ValueError("El recurso debe ser video o imagen.")
    if tipo_item == "frase" and tipo_recurso == "imagen":
        raise ValueError("Las frases solo soportan video en la base actual.")

    extension = Path(archivo.name).suffix.lower()
    if tipo_recurso == "video" and extension not in EXTENSIONES_VIDEO:
        raise ValueError("Use un video mp4, mov, avi, webm o mkv.")
    if tipo_recurso == "imagen" and extension not in EXTENSIONES_IMAGEN:
        raise ValueError("Use una imagen jpg, png o webp.")

    carpeta_base = DATA_VIDEOS_DIR if tipo_recurso == "video" else DATA_IMAGENES_DIR
    carpeta = carpeta_base / ("frases" if tipo_item == "frase" else "senas")
    carpeta.mkdir(parents=True, exist_ok=True)

    ruta_destino = carpeta / f"{_nombre_archivo_seguro(texto)}{extension}"
    ruta_destino.write_bytes(archivo.getbuffer())
    registrar_recurso(texto, tipo_item, tipo_recurso, _ruta_relativa(ruta_destino))
    return ruta_destino


def registrar_recurso(texto, tipo_item, tipo_recurso, ruta_relativa):
    texto = normalizar_texto(texto)
    initialize_database()
    with get_connection() as conexion:
        if tipo_item == "frase":
            conexion.execute(
                "UPDATE frases SET ruta_video = ? WHERE texto = ?",
                (ruta_relativa, texto),
            )
        elif tipo_recurso == "video":
            conexion.execute(
                "UPDATE senas SET ruta_video = ? WHERE palabra = ?",
                (ruta_relativa, texto),
            )
        else:
            conexion.execute(
                "UPDATE senas SET ruta_imagen = ? WHERE palabra = ?",
                (ruta_relativa, texto),
            )


def obtener_recurso_item(texto, tipo_item):
    texto = normalizar_texto(texto)
    initialize_database()
    with get_connection() as conexion:
        if tipo_item == "frase":
            fila = conexion.execute(
                "SELECT ruta_video, NULL AS ruta_imagen FROM frases WHERE texto = ? AND activo = 1",
                (texto,),
            ).fetchone()
        else:
            fila = conexion.execute(
                "SELECT ruta_video, ruta_imagen FROM senas WHERE palabra = ? AND activo = 1",
                (texto,),
            ).fetchone()

    if not fila:
        return None

    ruta_video = _ruta_absoluta(fila["ruta_video"])
    if ruta_video:
        return {"tipo": "video", "ruta": ruta_video}

    ruta_imagen = _ruta_absoluta(fila["ruta_imagen"])
    if ruta_imagen:
        return {"tipo": "imagen", "ruta": ruta_imagen}

    return None


def convertir_a_data_uri(ruta):
    ruta = _ruta_absoluta(ruta)
    if not ruta or ruta.stat().st_size > MAX_BYTES_EMBEBIDOS:
        return None

    mime = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{datos}"


def mapa_recursos_embebibles():
    recursos = {}
    for item in listar_items_lsc():
        recurso = obtener_recurso_item(item["texto"], item["tipo"])
        if not recurso:
            continue

        data_uri = convertir_a_data_uri(recurso["ruta"])
        if not data_uri:
            continue

        clave = normalizar_texto(item["texto"]).replace(" ", "_")
        recursos[clave] = {
            "texto": item["texto"],
            "tipo": recurso["tipo"],
            "data": data_uri,
        }

    return recursos
