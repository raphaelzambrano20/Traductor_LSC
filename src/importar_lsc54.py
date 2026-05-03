import argparse
import csv
import json
import unicodedata
from pathlib import Path

import numpy as np

from config import DATA_DIR, ENTRADA_MODELO, LANDMARKS_POR_MANO, MAX_MANOS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LSC54_SAMPLE_PATH = PROJECT_ROOT / "data" / "external" / "lsc54" / "sample.json"
SALIDA_LSC54_PATH = DATA_DIR / "lsc54_convertido.csv"

MAPEO_ETIQUETAS = {
    "Ayudar": "ayuda",
    "Buenos Días": "buenos_dias",
    "Buenas Noches": "buenas_noches",
    "Buenas Tardes": "buenas_tardes",
    "Hola": "hola",
    "De nada": "de_nada",
    "Perdón": "perdon",
}


def normalizar_etiqueta(texto):
    texto = MAPEO_ETIQUETAS.get(texto, texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return texto.strip().lower().replace(" ", "_")


def punto(datos_frame, grupo, indice):
    grupo_datos = datos_frame.get(grupo)

    if not grupo_datos:
        return None

    try:
        return np.array(
            [
                grupo_datos["x"][indice],
                grupo_datos["y"][indice],
                grupo_datos["z"][indice],
            ],
            dtype=float,
        )
    except (KeyError, IndexError, TypeError):
        return None


def promedio_puntos(*puntos):
    puntos_validos = [punto for punto in puntos if punto is not None]

    if not puntos_validos:
        return None

    return np.mean(puntos_validos, axis=0)


def extender_mano(caracteristicas, datos_frame, grupo):
    grupo_datos = datos_frame.get(grupo)

    if not grupo_datos:
        caracteristicas.extend([0.0] * LANDMARKS_POR_MANO)
        return None

    puntos = []
    for indice in range(21):
        mano_punto = punto(datos_frame, grupo, indice)
        if mano_punto is None:
            caracteristicas.extend([0.0, 0.0, 0.0])
            continue

        caracteristicas.extend(mano_punto.tolist())
        puntos.append(mano_punto)

    if not puntos:
        return None

    return np.mean(np.array(puntos, dtype=float), axis=0)


def caracteristicas_contexto(mano_centro, referencias):
    if mano_centro is None:
        return [0.0] * (1 + 3 + len(referencias) * 4)

    caracteristicas = [1.0, *mano_centro.tolist()]

    for referencia in referencias:
        if referencia is None:
            caracteristicas.extend([0.0, 0.0, 0.0, 0.0])
            continue

        diferencia = mano_centro - referencia
        distancia = float(np.linalg.norm(diferencia))
        caracteristicas.extend([*diferencia.tolist(), distancia])

    return caracteristicas


def convertir_frame(datos_frame):
    caracteristicas = []
    centros_manos = []

    for grupo in ("l_hand", "r_hand")[:MAX_MANOS]:
        centros_manos.append(extender_mano(caracteristicas, datos_frame, grupo))

    nariz = punto(datos_frame, "pose", 0)
    boca = promedio_puntos(punto(datos_frame, "pose", 9), punto(datos_frame, "pose", 10))
    oreja_izquierda = punto(datos_frame, "pose", 7)
    oreja_derecha = punto(datos_frame, "pose", 8)
    hombro_izquierdo = punto(datos_frame, "pose", 11)
    hombro_derecho = punto(datos_frame, "pose", 12)
    pecho = promedio_puntos(hombro_izquierdo, hombro_derecho)
    referencias = [nariz, boca, oreja_izquierda, oreja_derecha, pecho]

    for mano_centro in centros_manos:
        caracteristicas.extend(caracteristicas_contexto(mano_centro, referencias))

    for referencia in referencias:
        if referencia is None:
            caracteristicas.extend([0.0, 0.0, 0.0])
        else:
            caracteristicas.extend(referencia.tolist())

    if hombro_izquierdo is None or hombro_derecho is None:
        caracteristicas.append(0.0)
    else:
        caracteristicas.append(float(np.linalg.norm(hombro_izquierdo - hombro_derecho)))

    if len(caracteristicas) < ENTRADA_MODELO:
        caracteristicas.extend([0.0] * (ENTRADA_MODELO - len(caracteristicas)))

    return caracteristicas[:ENTRADA_MODELO]


def ordenar_frames(frames):
    return sorted(frames.items(), key=lambda item: int(item[0].split("_")[-1]))


def indices_muestra(total_frames, cantidad):
    if total_frames <= cantidad:
        return list(range(total_frames))

    return sorted(set(np.linspace(0, total_frames - 1, cantidad, dtype=int).tolist()))


def convertir_lsc54(entrada, salida, frames_por_repeticion):
    with entrada.open("r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    salida.parent.mkdir(exist_ok=True)
    conteo = {}
    filas = 0

    with salida.open("w", newline="", encoding="utf-8") as archivo_salida:
        escritor = csv.writer(archivo_salida)

        for datos_firmante in datos.values():
            for datos_categoria in datos_firmante.values():
                for nombre_sena, datos_sena in datos_categoria.items():
                    etiqueta = normalizar_etiqueta(nombre_sena)
                    for datos_video in datos_sena.values():
                        for frames in datos_video.values():
                            frames_ordenados = ordenar_frames(frames)
                            for indice in indices_muestra(len(frames_ordenados), frames_por_repeticion):
                                _, datos_frame = frames_ordenados[indice]
                                escritor.writerow([etiqueta] + convertir_frame(datos_frame))
                                conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
                                filas += 1

    return filas, conteo


def main():
    parser = argparse.ArgumentParser(description="Convierte una muestra de LSC-54 al formato del proyecto.")
    parser.add_argument("--entrada", type=Path, default=LSC54_SAMPLE_PATH)
    parser.add_argument("--salida", type=Path, default=SALIDA_LSC54_PATH)
    parser.add_argument("--frames-por-repeticion", type=int, default=3)
    args = parser.parse_args()

    if not args.entrada.exists():
        print(f"No existe el archivo de entrada: {args.entrada}")
        return

    filas, conteo = convertir_lsc54(args.entrada, args.salida, args.frames_por_repeticion)
    print(f"Archivo convertido: {args.salida}")
    print(f"Filas generadas: {filas}")
    for etiqueta, cantidad in sorted(conteo.items()):
        print(f"{etiqueta}: {cantidad}")


if __name__ == "__main__":
    main()
