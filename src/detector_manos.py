import os
import warnings

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2
import mediapipe as mp

from config import ENTRADA_MODELO


class DetectorManos:
    def __init__(self, max_manos=2, deteccion_confianza=0.7, seguimiento_confianza=0.7):
        self.mp_manos = mp.solutions.hands
        self.manos = self.mp_manos.Hands(
            static_image_mode=False,
            max_num_hands=max_manos,
            min_detection_confidence=deteccion_confianza,
            min_tracking_confidence=seguimiento_confianza,
        )
        self.mp_dibujo = mp.solutions.drawing_utils

    def obtener_landmarks(self, frame):
        imagen_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.manos.process(imagen_rgb)

        landmarks_lista = []

        if resultado.multi_hand_landmarks:
            for mano_landmarks in resultado.multi_hand_landmarks:
                for punto in mano_landmarks.landmark:
                    landmarks_lista.extend([punto.x, punto.y, punto.z])

                self.mp_dibujo.draw_landmarks(
                    frame,
                    mano_landmarks,
                    self.mp_manos.HAND_CONNECTIONS,
                )

        if len(landmarks_lista) < ENTRADA_MODELO:
            landmarks_lista.extend([0.0] * (ENTRADA_MODELO - len(landmarks_lista)))
        else:
            landmarks_lista = landmarks_lista[:ENTRADA_MODELO]

        return frame, landmarks_lista
