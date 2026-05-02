import numpy as np

from config import ENTRADA_MODELO, LANDMARKS_POR_MANO, MAX_MANOS


def hay_mano_detectada(landmarks):
    """Valida solo la zona de landmarks de manos, ignorando cara y cuerpo."""
    return any(landmarks[: LANDMARKS_POR_MANO * MAX_MANOS])


def extraer_caracteristicas_temporales(historial_landmarks, ancho_base=None):
    """Combina postura actual, desplazamiento y velocidad de una secuencia corta."""
    secuencia = [landmarks for landmarks in historial_landmarks if hay_mano_detectada(landmarks)]
    ancho_base = ancho_base or ENTRADA_MODELO

    if not secuencia:
        return [0.0] * (ancho_base * 3)

    secuencia_ajustada = []
    for landmarks in secuencia:
        valores = list(landmarks)
        if len(valores) < ancho_base:
            valores.extend([0.0] * (ancho_base - len(valores)))
        else:
            valores = valores[:ancho_base]
        secuencia_ajustada.append(valores)

    matriz = np.array(secuencia_ajustada, dtype=float)
    actual = matriz[-1]

    if len(matriz) == 1:
        desplazamiento = np.zeros(ancho_base)
        velocidad_media = np.zeros(ancho_base)
    else:
        desplazamiento = matriz[-1] - matriz[0]
        velocidad_media = np.mean(np.diff(matriz, axis=0), axis=0)

    caracteristicas = np.concatenate([actual, desplazamiento, velocidad_media])
    return caracteristicas.tolist()
