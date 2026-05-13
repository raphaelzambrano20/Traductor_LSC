import csv
import time
from collections import Counter, deque
from datetime import datetime

import cv2
import numpy as np

from caracteristicas_temporales import hay_mano_detectada
from config import DATA_DIR, FRAMES_SECUENCIA, MODEL_PATH
from detector_manos import DetectorManos
from predecir_sena import (
    CALIDAD_MINIMA_MANO,
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    cargar_modelo,
    cumple_requisitos_sena,
    preparar_entrada,
)
from vocabulario_lsc import normalizar_etiqueta


RESULTADOS_PATH = DATA_DIR / "validacion_camara.csv"


def guardar_resultado(fila):
    DATA_DIR.mkdir(exist_ok=True)
    existe = RESULTADOS_PATH.exists()
    with RESULTADOS_PATH.open("a", encoding="utf-8", newline="") as archivo:
        campos = [
            "fecha",
            "sena_esperada",
            "prediccion_final",
            "correcta",
            "intentos_validos",
            "confianza_promedio",
            "confianza_maxima",
            "detalle_predicciones",
        ]
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        if not existe:
            escritor.writeheader()
        escritor.writerow(fila)


def predecir_frame(modelo, n_features, historial_landmarks, detector):
    landmarks = historial_landmarks[-1]
    manos_visibles, calidad_manos = detector.calidad_manos(landmarks)
    if not hay_mano_detectada(landmarks) or calidad_manos < CALIDAD_MINIMA_MANO:
        return None, None, f"Manos visibles: {manos_visibles} | calidad baja {calidad_manos:.2f}"

    entrada = preparar_entrada(historial_landmarks, n_features)
    prediccion = str(modelo.predict(entrada)[0])
    confianza = None
    if hasattr(modelo, "predict_proba"):
        confianza = float(np.max(modelo.predict_proba(entrada)))

    requisitos_ok, mensaje = cumple_requisitos_sena(prediccion, historial_landmarks, detector)
    if not requisitos_ok:
        return prediccion, confianza, mensaje

    return prediccion, confianza, ""


def validar_sena(sena_esperada, duracion_segundos=6):
    if not MODEL_PATH.exists():
        print("No existe el modelo. Primero ejecute: python src/entrenar_modelo.py")
        return

    sena_esperada = normalizar_etiqueta(sena_esperada)
    modelo, n_features = cargar_modelo()
    detector = DetectorManos()
    camara = cv2.VideoCapture(0)
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camara.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    historial_landmarks = deque(maxlen=FRAMES_SECUENCIA)
    predicciones = []
    confianzas = []
    inicio = time.time()

    print(f"Validando '{sena_esperada}' durante {duracion_segundos} segundos.")
    print("Presione Q para terminar antes.")

    while time.time() - inicio < duracion_segundos:
        ret, frame = camara.read()
        if not ret:
            print("No se pudo acceder a la camara.")
            break

        frame, landmarks = detector.obtener_landmarks(frame)
        historial_landmarks.append(landmarks)
        prediccion = None
        confianza = None
        mensaje = "Esperando suficientes frames..."

        if len(historial_landmarks) == FRAMES_SECUENCIA:
            prediccion, confianza, mensaje = predecir_frame(
                modelo,
                n_features,
                historial_landmarks,
                detector,
            )
            if prediccion:
                predicciones.append(prediccion)
            if confianza is not None:
                confianzas.append(confianza)

        frame_mostrado = cv2.flip(frame, 1)
        detector.dibujar_referencias_visibles(frame_mostrado, espejo=True)
        detector.dibujar_ubicaciones_manos(frame_mostrado, espejo=True)

        restante = max(0, int(duracion_segundos - (time.time() - inicio)))
        texto_prediccion = prediccion or mensaje
        if confianza is not None:
            texto_prediccion += f" ({confianza:.0%})"

        cv2.putText(
            frame_mostrado,
            f"Esperada: {sena_esperada} | Tiempo: {restante}s",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame_mostrado,
            f"Prediccion: {texto_prediccion}",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame_mostrado,
            "Q terminar prueba",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        cv2.imshow("Validacion real de camara", frame_mostrado)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camara.release()
    cv2.destroyAllWindows()

    conteo = Counter(predicciones)
    prediccion_final = conteo.most_common(1)[0][0] if conteo else ""
    correcta = prediccion_final == sena_esperada
    confianza_promedio = float(np.mean(confianzas)) if confianzas else 0.0
    confianza_maxima = float(np.max(confianzas)) if confianzas else 0.0
    detalle = "; ".join(f"{sena}:{total}" for sena, total in conteo.most_common())

    fila = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "sena_esperada": sena_esperada,
        "prediccion_final": prediccion_final,
        "correcta": "si" if correcta else "no",
        "intentos_validos": len(predicciones),
        "confianza_promedio": round(confianza_promedio, 4),
        "confianza_maxima": round(confianza_maxima, 4),
        "detalle_predicciones": detalle,
    }
    guardar_resultado(fila)

    print("\nResultado:")
    print(f"Esperada: {sena_esperada}")
    print(f"Prediccion final: {prediccion_final or 'sin prediccion'}")
    print(f"Correcta: {'si' if correcta else 'no'}")
    print(f"Intentos validos: {len(predicciones)}")
    print(f"Confianza promedio: {confianza_promedio:.2%}")
    print(f"Detalle: {detalle or 'sin predicciones'}")
    print(f"Guardado en: {RESULTADOS_PATH}")


def main():
    while True:
        sena = input("\nSena esperada para validar (Enter para salir): ").strip()
        if not sena:
            break

        duracion = input("Duracion en segundos [6]: ").strip()
        duracion_segundos = int(duracion) if duracion.isdigit() else 6
        validar_sena(sena, duracion_segundos)


if __name__ == "__main__":
    main()
