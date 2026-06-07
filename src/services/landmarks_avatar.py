import csv
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import (DATASET_PATH, LEGACY_DATASET_PATH, LANDMARKS_POR_MANO, MAX_MANOS,
                    CARACTERISTICAS_CONTEXTO_POR_MANO)

HAND_CONNECTIONS = [
    [0,1],[1,2],[2,3],[3,4],
    [0,5],[5,6],[6,7],[7,8],
    [5,9],[9,10],[10,11],[11,12],
    [9,13],[13,14],[14,15],[15,16],
    [13,17],[17,18],[18,19],[19,20],
    [0,17],
]

_cache = {}   # Clave: nombre_sena → resultado con [x,y,z] por landmark
MIN_RATIO_MANO = 0.40

# Offset donde empiezan las referencias corporales en el CSV (después de label)
# = manos (126) + contexto por mano (35×2=70) = 196 valores → col 197 en CSV
_REF_INICIO = LANDMARKS_POR_MANO * MAX_MANOS + CARACTERISTICAS_CONTEXTO_POR_MANO * MAX_MANOS


def obtener_landmarks_sena(nombre_sena):
    if nombre_sena in _cache:
        return _cache[nombre_sena]

    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return None

    muestras_mano_izq = []
    muestras_mano_der = []
    nariz_muestras = []
    pecho_muestras = []
    total_hand = LANDMARKS_POR_MANO * MAX_MANOS  # 126
    ref_csv_idx = 1 + _REF_INICIO  # índice en la fila CSV donde empieza nariz

    def mano_presente(vals, n=21, umbral=0.01, min_puntos=15):
        """Exige que al menos min_puntos de los 21 landmarks tengan coordenadas reales."""
        return sum(
            1 for i in range(0, n * 3, 3)
            if abs(vals[i]) > umbral or abs(vals[i + 1]) > umbral
        ) >= min_puntos

    with dataset.open("r", encoding="utf-8") as f:
        for fila in csv.reader(f):
            if not fila or fila[0].strip() != nombre_sena:
                continue
            try:
                vals = [float(v) for v in fila[1:total_hand + 1]]
                if len(vals) == total_hand:
                    mano_izq_vals = vals[:LANDMARKS_POR_MANO]
                    mano_der_vals = vals[LANDMARKS_POR_MANO:total_hand]
                    muestras_mano_izq.append(mano_izq_vals if mano_presente(mano_izq_vals) else None)
                    muestras_mano_der.append(mano_der_vals if mano_presente(mano_der_vals) else None)
                # Leer referencias corporales si existen (nariz=0, pecho=4)
                if len(fila) > ref_csv_idx + 14:
                    refs = [float(v) for v in fila[ref_csv_idx:ref_csv_idx + 15]]
                    if refs[0] != 0.0 or refs[1] != 0.0:
                        nariz_muestras.append([refs[0], refs[1]])
                    if refs[12] != 0.0 or refs[13] != 0.0:
                        pecho_muestras.append([refs[12], refs[13]])
            except (ValueError, IndexError):
                continue

    total_muestras = max(len(muestras_mano_izq), len(muestras_mano_der))
    if total_muestras == 0:
        _cache[nombre_sena] = None
        return None

    def promedio_mano(muestras):
        presentes = [m for m in muestras if m is not None]
        ratio = len(presentes) / total_muestras if total_muestras else 0.0
        if ratio < MIN_RATIO_MANO:
            return None, ratio
        return np.mean(presentes, axis=0), ratio

    # DetectorManos guarda: left_hand_landmarks, right_hand_landmarks.
    # Para el avatar usamos nombres desde la persona: mano_izq y mano_der.
    mano_izq, ratio_izq = promedio_mano(muestras_mano_izq)
    mano_der, ratio_der = promedio_mano(muestras_mano_der)

    def a_puntos(vals):
        # Devuelve [x, y, z] por landmark — el Z de MediaPipe codifica profundidad
        # de cada dedo (negativo = hacia la cámara, positivo = hacia atrás).
        # Necesario para que el avatar pueda mostrar dedos curvados vs extendidos.
        return [[round(float(vals[i]), 4),
                 round(float(vals[i+1]), 4),
                 round(float(vals[i+2]), 4)]
                for i in range(0, len(vals) - 2, 3)]

    nariz_ref = np.mean(nariz_muestras, axis=0).tolist() if nariz_muestras else None
    pecho_ref = np.mean(pecho_muestras, axis=0).tolist() if pecho_muestras else None

    resultado = {
        "nombre": nombre_sena,
        "muestras": total_muestras,
        "conexiones": HAND_CONNECTIONS,
        "mano_der": a_puntos(mano_der) if mano_der is not None else None,
        "mano_izq": a_puntos(mano_izq) if mano_izq is not None else None,
        "ratio_mano_der": round(ratio_der, 3),
        "ratio_mano_izq": round(ratio_izq, 3),
        "nariz": [round(nariz_ref[0], 4), round(nariz_ref[1], 4)] if nariz_ref else None,
        "pecho": [round(pecho_ref[0], 4), round(pecho_ref[1], 4)] if pecho_ref else None,
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
