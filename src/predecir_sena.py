import os
import warnings
import time
import threading
from collections import deque

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2
import joblib
import numpy as np

from caracteristicas_temporales import extraer_caracteristicas_temporales, hay_mano_detectada
from config import (
    ENTRADA_MODELO,
    ETIQUETAS_SIN_SENA,
    FRAMES_SECUENCIA,
    LANDMARKS_POR_MANO,
    MAX_MANOS,
    MODEL_PATH,
)
from detector_manos import DetectorManos
from voz import hablar_windows


def cargar_modelo():
    artefacto = joblib.load(MODEL_PATH)

    if isinstance(artefacto, dict) and "modelo" in artefacto:
        modelo = artefacto["modelo"]
        n_features = int(artefacto.get("n_features", getattr(modelo, "n_features_in_", ENTRADA_MODELO)))
        return modelo, n_features

    return artefacto, int(getattr(artefacto, "n_features_in_", ENTRADA_MODELO))


def preparar_entrada(historial_landmarks, n_features):
    if n_features > ENTRADA_MODELO:
        ancho_base = n_features // 3 if n_features % 3 == 0 else ENTRADA_MODELO
        caracteristicas = extraer_caracteristicas_temporales(historial_landmarks, ancho_base)
    else:
        caracteristicas = list(historial_landmarks[-1])

    if len(caracteristicas) < n_features:
        caracteristicas.extend([0.0] * (n_features - len(caracteristicas)))
    else:
        caracteristicas = caracteristicas[:n_features]

    return np.array(caracteristicas).reshape(1, -1)


def formatear_frase(frase):
    return " ".join(frase).strip()


def es_sin_sena(etiqueta):
    return str(etiqueta).strip().lower() in ETIQUETAS_SIN_SENA


def obtener_landmarks_manos(landmarks):
    return np.array(landmarks[: LANDMARKS_POR_MANO * MAX_MANOS], dtype=float)


def calcular_movimiento_manos(manos_actuales, manos_anteriores):
    if manos_anteriores is None:
        return float("inf")

    return float(np.mean(np.abs(manos_actuales - manos_anteriores)))


def predecir():
    if not MODEL_PATH.exists():
        print("No existe el modelo. Primero ejecute: python src/entrenar_modelo.py")
        return

    modelo, n_features = cargar_modelo()
    detector = DetectorManos()
    camara = cv2.VideoCapture(0)
    historial_landmarks = deque(maxlen=FRAMES_SECUENCIA)
    ultima_prediccion = None
    frames_estables = 0
    ultimo_tiempo_sena = 0
    ultimo_tiempo_actividad = 0
    manos_anteriores = None
    parrafo = []
    indice_voz = 0
    minimo_frames_estables = 5
    segundos_sin_movimiento_para_hablar = 2.0
    segundos_entre_senas = 0.7
    umbral_movimiento_mano = 0.003
    confianza_minima_voz = 0.45
    voz_habilitada = True
    frase_ya_hablada = True
    voz_ocupada = False
    bloqueo_voz = threading.Lock()

    def hablar_en_segundo_plano(texto):
        nonlocal voz_ocupada

        with bloqueo_voz:
            if voz_ocupada:
                return False
            voz_ocupada = True

        def tarea_voz():
            nonlocal voz_ocupada
            try:
                hablar_windows(texto, esperar=True)
                print(f"Voz automatica: {texto}")
            finally:
                with bloqueo_voz:
                    voz_ocupada = False

        threading.Thread(target=tarea_voz, daemon=True).start()
        return True

    while True:
        ret, frame = camara.read()

        if not ret:
            print("No se pudo acceder a la camara.")
            break

        frame, landmarks = detector.obtener_landmarks(frame)
        historial_landmarks.append(landmarks)
        texto_prediccion = "Esperando sena..."
        confianza = None
        prediccion_actual = None
        ahora = time.time()
        manos_detectadas = hay_mano_detectada(landmarks)

        if manos_detectadas:
            manos_actuales = obtener_landmarks_manos(landmarks)
            movimiento_manos = calcular_movimiento_manos(manos_actuales, manos_anteriores)
            if movimiento_manos >= umbral_movimiento_mano:
                ultimo_tiempo_actividad = ahora
            manos_anteriores = manos_actuales
            entrada = preparar_entrada(historial_landmarks, n_features)

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

                if es_sin_sena(prediccion_actual):
                    texto_prediccion = "Sin sena detectada"
                    frames_estables = 0
                    ultima_prediccion = None
                else:
                    confianza_suficiente = confianza is None or confianza >= confianza_minima_voz
                    puede_hablar = (
                        voz_habilitada
                        and frames_estables >= minimo_frames_estables
                        and confianza_suficiente
                        and ahora - ultimo_tiempo_sena >= segundos_entre_senas
                    )
                    if puede_hablar:
                        palabra = prediccion_actual.replace("_", " ")
                        ultima_palabra = parrafo[-1] if parrafo else None
                        if palabra != ultima_palabra:
                            parrafo.append(palabra)
                            ultimo_tiempo_sena = ahora
                            frase_ya_hablada = False
            except Exception:
                texto_prediccion = "Sena no reconocida"
        else:
            ultima_prediccion = None
            frames_estables = 0
            manos_anteriores = None

        ahora = time.time()
        pausa_para_hablar = (
            voz_habilitada
            and len(parrafo) > indice_voz
            and not frase_ya_hablada
            and ahora - ultimo_tiempo_actividad >= segundos_sin_movimiento_para_hablar
        )
        if pausa_para_hablar:
            texto_voz = formatear_frase(parrafo[indice_voz:])
            if texto_voz:
                if hablar_en_segundo_plano(texto_voz):
                    parrafo.clear()
                    indice_voz = 0
                    frase_ya_hablada = True

        frame_mostrado = cv2.flip(frame, 1)
        cv2.putText(
            frame_mostrado,
            texto_prediccion,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame_mostrado,
            "Q salir | C limpiar parrafo | V hablar parrafo | Voz: 2s sin movimiento",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame_mostrado,
            "Parrafo: " + " ".join(parrafo[-10:]),
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        if n_features > ENTRADA_MODELO:
            cv2.putText(
                frame_mostrado,
                f"Modo movimiento: {len(historial_landmarks)}/{FRAMES_SECUENCIA} frames",
                (10, 155),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

        cv2.imshow("Traductor LSC", frame_mostrado)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break
        if tecla == ord("c"):
            parrafo.clear()
            indice_voz = 0
            frase_ya_hablada = True
        if tecla == ord("v"):
            texto_voz = formatear_frase(parrafo)
            if texto_voz:
                if hablar_en_segundo_plano(texto_voz):
                    parrafo.clear()
                    indice_voz = 0
                    frase_ya_hablada = True

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    predecir()
