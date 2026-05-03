import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATABASE_PATH


def get_connection(db_path: Path = DATABASE_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(db_path)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def initialize_database(db_path: Path = DATABASE_PATH):
    schema_path = Path(__file__).with_name("schema.sql")
    with get_connection(db_path) as conexion:
        conexion.executescript(schema_path.read_text(encoding="utf-8"))
    return db_path
