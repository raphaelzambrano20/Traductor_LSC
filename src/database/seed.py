import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_connection, initialize_database
from src.services.normalizacion import normalizar_texto


CATEGORIAS_INICIALES = [
    ("cordialidad", "Saludos, despedidas y expresiones de cortesia."),
    ("colores", "Colores basicos."),
    ("numeros", "Numeros basicos."),
    ("alfabeto", "Letras para deletrear palabras no registradas."),
    ("familia", "Personas y relaciones familiares."),
    ("acciones", "Verbos y acciones frecuentes."),
    ("objetos", "Objetos, alimentos y elementos frecuentes."),
    ("personas", "Roles comunes en el contexto educativo."),
    ("pronombres", "Pronombres personales usados en conversacion."),
    ("estados", "Estados, condiciones y respuestas descriptivas."),
    ("control", "Etiquetas internas para reposo, transicion o ausencia de sena."),
    ("neutro", "Respuestas o palabras generales."),
]

SENAS_INICIALES = [
    ("hola", "cordialidad", []),
    ("gracias", "cordialidad", ["muchas gracias"]),
    ("permiso", "cordialidad", []),
    ("por favor", "cordialidad", ["por_favor"]),
    ("si", "neutro", ["sí"]),
    ("no", "neutro", []),
    ("ayuda", "acciones", ["ayudar"]),
    ("quiero", "acciones", ["querer", "deseo"]),
    ("agua", "objetos", []),
    ("profesor", "personas", ["docente", "maestro"]),
    ("estudiante", "personas", ["alumno"]),
    ("sordo", "personas", []),
    ("yo", "pronombres", ["soy"]),
    ("tu", "pronombres", ["usted"]),
    ("bien", "estados", []),
    ("mal", "estados", []),
    ("saludos", "cordialidad", ["saludo"]),
    ("sin_sena", "control", ["sin sena", "no sena"]),
    ("reposo", "control", []),
    ("ninguna", "control", []),
    ("mama", "familia", ["mamá", "madre"]),
    ("papa", "familia", ["papá", "padre"]),
    ("rojo", "colores", ["roja", "rojos", "rojas"]),
    ("azul", "colores", []),
    ("verde", "colores", []),
    ("uno", "numeros", ["1"]),
    ("dos", "numeros", ["2"]),
    ("tres", "numeros", ["3"]),
]

FRASES_INICIALES = [
    ("buenos dias", "cordialidad", ["buenos_dias", "buen día", "buen dia"]),
    ("como estas", "cordialidad", ["cómo estás", "como está", "cómo está"]),
    ("muchas gracias", "cordialidad", []),
]


def upsert_categoria(conexion, nombre, descripcion):
    nombre = normalizar_texto(nombre)
    conexion.execute(
        """
        INSERT INTO categorias (nombre, descripcion)
        VALUES (?, ?)
        ON CONFLICT(nombre) DO UPDATE SET descripcion = excluded.descripcion
        """,
        (nombre, descripcion),
    )
    return conexion.execute("SELECT id FROM categorias WHERE nombre = ?", (nombre,)).fetchone()["id"]


def seed_database():
    initialize_database()
    with get_connection() as conexion:
        categorias = {
            nombre: upsert_categoria(conexion, nombre, descripcion)
            for nombre, descripcion in CATEGORIAS_INICIALES
        }
        conexion.execute("DELETE FROM sinonimos WHERE texto = ?", ("saludo",))

        for palabra, categoria, sinonimos in SENAS_INICIALES:
            palabra_normalizada = normalizar_texto(palabra)
            conexion.execute(
                """
                INSERT INTO senas (palabra, categoria_id)
                VALUES (?, ?)
                ON CONFLICT(palabra) DO UPDATE SET categoria_id = excluded.categoria_id
                """,
                (palabra_normalizada, categorias[categoria]),
            )
            sena_id = conexion.execute(
                "SELECT id FROM senas WHERE palabra = ?", (palabra_normalizada,)
            ).fetchone()["id"]
            for sinonimo in sinonimos:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO sinonimos (sena_id, texto)
                    VALUES (?, ?)
                    """,
                    (sena_id, normalizar_texto(sinonimo)),
                )

        for texto, categoria, sinonimos in FRASES_INICIALES:
            texto_normalizado = normalizar_texto(texto)
            conexion.execute(
                """
                INSERT INTO frases (texto, categoria_id)
                VALUES (?, ?)
                ON CONFLICT(texto) DO UPDATE SET categoria_id = excluded.categoria_id
                """,
                (texto_normalizado, categorias[categoria]),
            )
            frase_id = conexion.execute(
                "SELECT id FROM frases WHERE texto = ?", (texto_normalizado,)
            ).fetchone()["id"]
            for sinonimo in sinonimos:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO sinonimos (frase_id, texto)
                    VALUES (?, ?)
                    """,
                    (frase_id, normalizar_texto(sinonimo)),
                )


if __name__ == "__main__":
    seed_database()
    print("Base de datos LSC inicializada correctamente.")
