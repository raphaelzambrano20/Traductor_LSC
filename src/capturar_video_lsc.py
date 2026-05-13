import argparse
import sys
import time
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.normalizacion import normalizar_texto
from src.services.recursos_lsc import DATA_VIDEOS_DIR, registrar_recurso


CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


def ruta_video(texto, tipo_item):
    nombre = normalizar_texto(texto).replace(" ", "_")
    carpeta = DATA_VIDEOS_DIR / ("frases" if tipo_item == "frase" else "senas")
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / f"{nombre}.mp4"


def dibujar_texto(frame, texto, y, color=(255, 255, 255), escala=0.75):
    cv2.putText(
        frame,
        texto,
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        escala,
        color,
        2,
        cv2.LINE_AA,
    )


def grabar_clip(texto, tipo_item, duracion, camara_id):
    texto = normalizar_texto(texto)
    if not texto:
        raise ValueError("La palabra o frase no puede estar vacia.")

    salida = ruta_video(texto, tipo_item)
    camara = cv2.VideoCapture(camara_id)
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camara.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    if not camara.isOpened():
        raise RuntimeError("No se pudo abrir la camara.")

    writer = None
    grabando = False
    inicio = None
    cuenta_regresiva = None

    try:
        while True:
            ret, frame = camara.read()
            if not ret:
                raise RuntimeError("No se pudo leer la camara.")

            frame = cv2.flip(frame, 1)
            ahora = time.time()

            if cuenta_regresiva is not None:
                restante = 3 - int(ahora - cuenta_regresiva)
                if restante > 0:
                    dibujar_texto(frame, f"Grabando en {restante}", 70, (0, 255, 255), 1.2)
                else:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    writer = cv2.VideoWriter(
                        str(salida),
                        fourcc,
                        CAMERA_FPS,
                        (int(camara.get(cv2.CAP_PROP_FRAME_WIDTH)), int(camara.get(cv2.CAP_PROP_FRAME_HEIGHT))),
                    )
                    grabando = True
                    inicio = ahora
                    cuenta_regresiva = None

            if grabando and writer is not None:
                writer.write(frame)
                transcurrido = ahora - inicio
                dibujar_texto(frame, f"REC {transcurrido:.1f}/{duracion:.1f}s", 70, (0, 0, 255), 1.0)
                if transcurrido >= duracion:
                    break
            else:
                dibujar_texto(frame, f"Sena/frase: {texto}", 45)
                dibujar_texto(frame, "R grabar | Q salir", 80, (0, 255, 0))

            cv2.imshow("Capturar video LSC", frame)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("q"):
                return None
            if tecla == ord("r") and not grabando and cuenta_regresiva is None:
                cuenta_regresiva = time.time()
    finally:
        if writer is not None:
            writer.release()
        camara.release()
        cv2.destroyAllWindows()

    registrar_recurso(texto, tipo_item, "video", salida.relative_to(PROJECT_ROOT).as_posix())
    return salida


def main():
    parser = argparse.ArgumentParser(description="Captura un video real validado para una sena LSC.")
    parser.add_argument("texto", nargs="?", help="Palabra o frase que se va a grabar.")
    parser.add_argument("--tipo", choices=["palabra", "frase"], default="palabra")
    parser.add_argument("--duracion", type=float, default=3.0)
    parser.add_argument("--camara", type=int, default=0)
    args = parser.parse_args()

    texto = args.texto or input("Palabra o frase LSC: ").strip()
    salida = grabar_clip(texto, args.tipo, args.duracion, args.camara)
    if salida:
        print(f"Video guardado y enlazado: {salida}")
    else:
        print("Captura cancelada.")


if __name__ == "__main__":
    main()
