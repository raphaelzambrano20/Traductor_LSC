import os
import warnings
import time

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2
import joblib
import numpy as np

from config import MODEL_PATH
from detector_manos import DetectorManos
from voz import hablar_windows


def predecir():
    if not MODEL_PATH.exists():
        print("No existe el modelo. Primero ejecute: python src/entrenar_modelo.py")
        return

    modelo = joblib.load(MODEL_PATH)
    detector = DetectorManos()
    camara = cv2.VideoCapture(0)
    ultima_prediccion = None
    frames_estables = 0
    ultimo_tiempo_voz = 0
    minimo_frames_estables = 3
    segundos_entre_voz = 3.0
    confianza_minima_voz = 0.45
    voz_habilitada = True

    while True:
        ret, frame = camara.read()

        if not ret:
            print("No se pudo acceder a la camara.")
            break

        frame, landmarks = detector.obtener_landmarks(frame)
        texto_prediccion = "Esperando sena..."
        confianza = None
        prediccion_actual = None

        if any(landmarks):
            entrada = np.array(landmarks).reshape(1, -1)

            try:
                prediccion = modelo.predict(entrada)[0]
                prediccion_actual = str(prediccion)
                if hasattr(modelo, "predict_proba"):
                    confianza = float(np.max(modelo.predict_proba(entrada)))

                if prediccion == ultima_prediccion:
                    frames_estables += 1
                else:
                    frames_estables = 1
                    ultima_prediccion = prediccion

                texto_prediccion = f"Traduccion: {prediccion}"
                if confianza is not None:
                    texto_prediccion += f" ({confianza:.0%})"

                ahora = time.time()
                confianza_suficiente = confianza is None or confianza >= confianza_minima_voz
                puede_hablar = (
                    voz_habilitada
                    and frames_estables >= minimo_frames_estables
                    and confianza_suficiente
                    and ahora - ultimo_tiempo_voz >= segundos_entre_voz
                )
                if puede_hablar:
                    hablar_windows(prediccion_actual.replace("_", " "))
                    print(f"Voz automatica: {prediccion_actual}")
                    ultimo_tiempo_voz = ahora
            except Exception:
                texto_prediccion = "Sena no reconocida"

        cv2.putText(
            frame,
            texto_prediccion,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            "Q salir | Voz automatica activa",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Traductor LSC", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    predecir()
