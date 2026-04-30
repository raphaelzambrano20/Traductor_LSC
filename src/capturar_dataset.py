import csv
import os
import warnings

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2

from config import DATA_DIR, DATASET_PATH
from detector_manos import DetectorManos
from vocabulario_lsc import normalizar_etiqueta


def capturar_sena(nombre_sena, cantidad_muestras=100):
    nombre_sena = normalizar_etiqueta(nombre_sena)

    if not nombre_sena:
        print("Debe digitar el nombre de la sena LSC.")
        return

    detector = DetectorManos()
    camara = cv2.VideoCapture(0)

    DATA_DIR.mkdir(exist_ok=True)
    muestras_guardadas = 0

    with DATASET_PATH.open(mode="a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)

        while muestras_guardadas < cantidad_muestras:
            ret, frame = camara.read()

            if not ret:
                print("No se pudo acceder a la camara.")
                break

            frame, landmarks = detector.obtener_landmarks(frame)

            cv2.putText(
                frame,
                f"Sena: {nombre_sena} | Muestras: {muestras_guardadas}/{cantidad_muestras}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                "Presione S para guardar | Q para salir",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Captura de senas", frame)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("s") and any(landmarks):
                escritor.writerow([nombre_sena] + landmarks)
                muestras_guardadas += 1

            if tecla == ord("q"):
                break

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    nombre = input("Digite el nombre de la sena LSC: ").strip()
    cantidad = int(input("Cantidad de muestras: "))
    capturar_sena(nombre, cantidad)
