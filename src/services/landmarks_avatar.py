import csv
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import DATASET_PATH, LEGACY_DATASET_PATH, LANDMARKS_POR_MANO, MAX_MANOS

HAND_CONNECTIONS = [
    [0,1],[1,2],[2,3],[3,4],
    [0,5],[5,6],[6,7],[7,8],
    [5,9],[9,10],[10,11],[11,12],
    [9,13],[13,14],[14,15],[15,16],
    [13,17],[17,18],[18,19],[19,20],
    [0,17],
]

_cache = {}


def obtener_landmarks_sena(nombre_sena):
    if nombre_sena in _cache:
        return _cache[nombre_sena]

    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return None

    muestras = []
    total_hand = LANDMARKS_POR_MANO * MAX_MANOS  # 126

    with dataset.open("r", encoding="utf-8") as f:
        for fila in csv.reader(f):
            if not fila or fila[0].strip() != nombre_sena:
                continue
            try:
                vals = [float(v) for v in fila[1:total_hand + 1]]
                if len(vals) == total_hand:
                    muestras.append(vals)
            except ValueError:
                continue

    if not muestras:
        _cache[nombre_sena] = None
        return None

    promedio = np.mean(muestras, axis=0)
    mano_der = promedio[:LANDMARKS_POR_MANO]
    mano_izq = promedio[LANDMARKS_POR_MANO:total_hand]

    def a_puntos(vals):
        return [[round(float(vals[i]), 4), round(float(vals[i+1]), 4)]
                for i in range(0, len(vals) - 2, 3)]

    tiene_der = np.any(mano_der != 0)
    tiene_izq = np.any(mano_izq != 0)

    resultado = {
        "nombre": nombre_sena,
        "muestras": len(muestras),
        "conexiones": HAND_CONNECTIONS,
        "mano_der": a_puntos(mano_der) if tiene_der else None,
        "mano_izq": a_puntos(mano_izq) if tiene_izq else None,
    }
    _cache[nombre_sena] = resultado
    return resultado


def listar_senas_con_landmarks():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return []
    senas = set()
    with dataset.open("r", encoding="utf-8") as f:
        for fila in csv.reader(f):
            if fila and fila[0].strip():
                senas.add(fila[0].strip())
    return sorted(senas)
