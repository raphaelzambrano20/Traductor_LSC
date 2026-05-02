import csv
import os
import warnings
import time
from collections import deque

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2

from caracteristicas_temporales import extraer_caracteristicas_temporales, hay_mano_detectada
from config import DATA_DIR, DATASET_PATH, FRAMES_SECUENCIA
from detector_manos import DetectorManos
from vocabulario_lsc import normalizar_etiqueta


def capturar_sena(nombre_sena, cantidad_muestras=100):
    nombre_sena = normalizar_etiqueta(nombre_sena)

    if not nombre_sena:
        print("Debe digitar el nombre de la sena LSC.")
        return

    detector = DetectorManos()
    camara = cv2.VideoCapture(0)
    historial_landmarks = deque(maxlen=FRAMES_SECUENCIA)
    ultimo_guardado = 0
    grabando_movimiento = False

    DATA_DIR.mkdir(exist_ok=True)
    muestras_guardadas = 0

    print("Camara abierta. Prepare la mano y presione R justo antes de hacer la sena.")
    print(f"El sistema grabara {FRAMES_SECUENCIA} frames y guardara la muestra automaticamente.")

    with DATASET_PATH.open(mode="a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)

        while muestras_guardadas < cantidad_muestras:
            ret, frame = camara.read()

            if not ret:
                print("No se pudo acceder a la camara.")
                break

            frame, landmarks = detector.obtener_landmarks(frame)
            if grabando_movimiento:
                historial_landmarks.append(landmarks)
            frame_mostrado = cv2.flip(frame, 1)

            cv2.putText(
                frame_mostrado,
                f"Sena: {nombre_sena} | Muestras: {muestras_guardadas}/{cantidad_muestras}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame_mostrado,
                "R grabar movimiento | Q salir",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
            estado = "Grabando..." if grabando_movimiento else "Listo para grabar"
            cv2.putText(
                frame_mostrado,
                f"{estado} | Frames: {len(historial_landmarks)}/{FRAMES_SECUENCIA}",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
            if time.time() - ultimo_guardado < 1.2:
                cv2.putText(
                    frame_mostrado,
                    "Muestra de movimiento guardada",
                    (10, 135),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                )

            cv2.imshow("Captura de senas", frame_mostrado)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("r") and not grabando_movimiento:
                historial_landmarks.clear()
                grabando_movimiento = True
                print("Grabando movimiento... haga la sena ahora.")

            if grabando_movimiento and len(historial_landmarks) == FRAMES_SECUENCIA:
                caracteristicas = extraer_caracteristicas_temporales(historial_landmarks)
                tiene_mano = any(hay_mano_detectada(landmarks) for landmarks in historial_landmarks)
                if tiene_mano and any(caracteristicas):
                    escritor.writerow([nombre_sena] + caracteristicas)
                    archivo.flush()
                    muestras_guardadas += 1
                    ultimo_guardado = time.time()
                    print(
                        f"Guardada muestra {muestras_guardadas}/{cantidad_muestras} "
                        f"de '{nombre_sena}' con {len(caracteristicas)} valores temporales."
                    )
                else:
                    print("No se detecto la mano durante la grabacion. Intente de nuevo.")
                historial_landmarks.clear()
                grabando_movimiento = False

            if tecla == ord("q"):
                break

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    nombre = input("Digite el nombre de la sena LSC: ").strip()
    cantidad = int(input("Cantidad de muestras: "))
    capturar_sena(nombre, cantidad)
