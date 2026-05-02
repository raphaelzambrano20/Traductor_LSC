import os
import warnings

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2
import mediapipe as mp
import numpy as np

from config import ENTRADA_MODELO


class DetectorManos:
    def __init__(self, max_manos=2, deteccion_confianza=0.7, seguimiento_confianza=0.7):
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            refine_face_landmarks=True,
            min_detection_confidence=deteccion_confianza,
            min_tracking_confidence=seguimiento_confianza,
        )
        self.mp_dibujo = mp.solutions.drawing_utils
        self.max_manos = max_manos

    @staticmethod
    def _punto(landmarks, indice):
        if not landmarks:
            return None

        punto = landmarks.landmark[indice]
        return np.array([punto.x, punto.y, punto.z], dtype=float)

    @staticmethod
    def _promedio_puntos(*puntos):
        puntos_validos = [punto for punto in puntos if punto is not None]

        if not puntos_validos:
            return None

        return np.mean(puntos_validos, axis=0)

    @staticmethod
    def _primer_punto_valido(*puntos):
        for punto in puntos:
            if punto is not None:
                return punto

        return None

    @staticmethod
    def _extender_landmarks(landmarks_lista, mano_landmarks):
        if not mano_landmarks:
            landmarks_lista.extend([0.0] * 21 * 3)
            return None

        puntos = []
        for punto in mano_landmarks.landmark:
            coordenadas = [punto.x, punto.y, punto.z]
            landmarks_lista.extend(coordenadas)
            puntos.append(coordenadas)

        return np.mean(np.array(puntos, dtype=float), axis=0)

    @staticmethod
    def _caracteristicas_contexto(mano_centro, referencias):
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

    def obtener_landmarks(self, frame):
        imagen_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.holistic.process(imagen_rgb)

        landmarks_lista = []

        manos = [
            resultado.left_hand_landmarks,
            resultado.right_hand_landmarks,
        ][: self.max_manos]
        centros_manos = []

        for mano_landmarks in manos:
            centros_manos.append(self._extender_landmarks(landmarks_lista, mano_landmarks))

            if mano_landmarks:
                self.mp_dibujo.draw_landmarks(
                    frame,
                    mano_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                )

        pose = resultado.pose_landmarks
        rostro = resultado.face_landmarks
        nariz = self._primer_punto_valido(self._punto(pose, 0), self._punto(rostro, 1))
        boca = self._primer_punto_valido(
            self._promedio_puntos(self._punto(pose, 9), self._punto(pose, 10)),
            self._promedio_puntos(self._punto(rostro, 13), self._punto(rostro, 14)),
        )
        oreja_izquierda = self._punto(pose, 7)
        oreja_derecha = self._punto(pose, 8)
        hombro_izquierdo = self._punto(pose, 11)
        hombro_derecho = self._punto(pose, 12)
        pecho = self._promedio_puntos(hombro_izquierdo, hombro_derecho)
        referencias = [nariz, boca, oreja_izquierda, oreja_derecha, pecho]

        for mano_centro in centros_manos:
            landmarks_lista.extend(self._caracteristicas_contexto(mano_centro, referencias))

        for referencia in referencias:
            if referencia is None:
                landmarks_lista.extend([0.0, 0.0, 0.0])
            else:
                landmarks_lista.extend(referencia.tolist())

        if hombro_izquierdo is None or hombro_derecho is None:
            landmarks_lista.append(0.0)
        else:
            landmarks_lista.append(float(np.linalg.norm(hombro_izquierdo - hombro_derecho)))

        if pose:
            self.mp_dibujo.draw_landmarks(
                frame,
                pose,
                self.mp_holistic.POSE_CONNECTIONS,
            )

        if len(landmarks_lista) < ENTRADA_MODELO:
            landmarks_lista.extend([0.0] * (ENTRADA_MODELO - len(landmarks_lista)))
        else:
            landmarks_lista = landmarks_lista[:ENTRADA_MODELO]

        return frame, landmarks_lista
