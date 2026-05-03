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
        self.ultimas_referencias_visibles = []
        self.ultimas_manos_visibles = []

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
    def _punto_ubicacion_mano(mano_landmarks):
        if not mano_landmarks:
            return None

        # Para senas de apuntar, la punta del indice representa mejor la ubicacion
        # intencional que el centro de la palma.
        punta_indice = mano_landmarks.landmark[8]
        return np.array([punta_indice.x, punta_indice.y, punta_indice.z], dtype=float)

    @staticmethod
    def calidad_manos(landmarks):
        if not landmarks:
            return 0, 0.0

        manos_detectadas = 0
        cobertura_total = 0.0
        ancho_mano = 21 * 3

        for indice in range(2):
            inicio = indice * ancho_mano
            fin = inicio + ancho_mano
            valores = np.array(landmarks[inicio:fin], dtype=float)
            if np.any(valores):
                manos_detectadas += 1
                puntos = valores.reshape(21, 3)
                ancho = float(np.max(puntos[:, 0]) - np.min(puntos[:, 0]))
                alto = float(np.max(puntos[:, 1]) - np.min(puntos[:, 1]))
                cobertura_total += max(ancho, alto)

        return manos_detectadas, cobertura_total

    @staticmethod
    def _caracteristicas_contexto(mano_centro, referencias):
        if mano_centro is None:
            return [0.0] * (1 + 3 + len(referencias) * 4 + len(referencias) + 3 + 3)

        caracteristicas = [1.0, *mano_centro.tolist()]
        distancias = []

        for referencia in referencias:
            if referencia is None:
                caracteristicas.extend([0.0, 0.0, 0.0, 0.0])
                distancias.append(None)
                continue

            diferencia = mano_centro - referencia
            distancia = float(np.linalg.norm(diferencia))
            distancias.append(distancia)
            caracteristicas.extend([*diferencia.tolist(), distancia])

        distancias_validas = []
        for indice, referencia in enumerate(referencias):
            if referencia is not None:
                distancia_2d = float(np.linalg.norm(mano_centro[:2] - referencia[:2]))
                distancias_validas.append((indice, distancia_2d))
        zona_cercana = [0.0] * len(referencias)
        if distancias_validas:
            indice_cercano, _ = min(distancias_validas, key=lambda item: item[1])
            zona_cercana[indice_cercano] = 1.0
        caracteristicas.extend(zona_cercana)

        nariz = referencias[0] if len(referencias) > 0 else None
        pecho = referencias[4] if len(referencias) > 4 else None
        centro_x = None
        if nariz is not None and pecho is not None:
            centro_x = float((nariz[0] + pecho[0]) / 2)
        elif nariz is not None:
            centro_x = float(nariz[0])
        elif pecho is not None:
            centro_x = float(pecho[0])

        margen_lado = 0.04
        lado = [0.0, 0.0, 0.0]  # izquierda, centro, derecha desde la vista de la persona
        if centro_x is None:
            lado[1] = 1.0
        elif mano_centro[0] < centro_x - margen_lado:
            lado[2] = 1.0
        elif mano_centro[0] > centro_x + margen_lado:
            lado[0] = 1.0
        else:
            lado[1] = 1.0
        caracteristicas.extend(lado)

        referencia_altura = pecho if pecho is not None else nariz
        margen_altura = 0.05
        altura = [0.0, 0.0, 0.0]  # arriba, medio, abajo
        if referencia_altura is None:
            altura[1] = 1.0
        elif mano_centro[1] < referencia_altura[1] - margen_altura:
            altura[0] = 1.0
        elif mano_centro[1] > referencia_altura[1] + margen_altura:
            altura[2] = 1.0
        else:
            altura[1] = 1.0
        caracteristicas.extend(altura)

        return caracteristicas

    @staticmethod
    def _descripcion_ubicacion_mano(mano_centro, referencias):
        if mano_centro is None:
            return None

        nombres_zonas = ["nariz", "boca", "oreja izq", "oreja der", "pecho"]
        distancias = []
        for indice, referencia in enumerate(referencias):
            if referencia is not None:
                distancias.append((indice, float(np.linalg.norm(mano_centro[:2] - referencia[:2]))))

        zona = "sin zona"
        if distancias:
            indice_zona, _ = min(distancias, key=lambda item: item[1])
            zona = nombres_zonas[indice_zona]

        nariz = referencias[0] if len(referencias) > 0 else None
        pecho = referencias[4] if len(referencias) > 4 else None
        centro_x = None
        if nariz is not None and pecho is not None:
            centro_x = float((nariz[0] + pecho[0]) / 2)
        elif nariz is not None:
            centro_x = float(nariz[0])
        elif pecho is not None:
            centro_x = float(pecho[0])

        if centro_x is None:
            lado = "centro"
        elif mano_centro[0] < centro_x - 0.04:
            lado = "derecha"
        elif mano_centro[0] > centro_x + 0.04:
            lado = "izquierda"
        else:
            lado = "centro"

        referencia_altura = pecho if pecho is not None else nariz
        if referencia_altura is None:
            altura = "medio"
        elif mano_centro[1] < referencia_altura[1] - 0.05:
            altura = "arriba"
        elif mano_centro[1] > referencia_altura[1] + 0.05:
            altura = "abajo"
        else:
            altura = "medio"

        return f"{zona} | {lado} | {altura}"

    @staticmethod
    def _dibujar_referencia(frame, punto, texto=None, color=(0, 255, 0)):
        if punto is None:
            return

        alto, ancho = frame.shape[:2]
        x = int(punto[0] * ancho)
        y = int(punto[1] * alto)

        if x < 0 or x >= ancho or y < 0 or y >= alto:
            return

        cv2.circle(frame, (x, y), 7, color, -1)
        if not texto:
            return

        cv2.putText(
            frame,
            texto,
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            2,
        )

    def dibujar_referencias_visibles(self, frame, espejo=False):
        for punto, texto, color in self.ultimas_referencias_visibles:
            if punto is None:
                continue

            punto_visible = punto.copy()
            if espejo:
                punto_visible[0] = 1.0 - punto_visible[0]

            self._dibujar_referencia(frame, punto_visible, texto, color)

    def dibujar_ubicaciones_manos(self, frame, espejo=False):
        for punto, texto, color in self.ultimas_manos_visibles:
            if punto is None:
                continue

            punto_visible = punto.copy()
            if espejo:
                punto_visible[0] = 1.0 - punto_visible[0]

            self._dibujar_referencia(frame, punto_visible, texto, color)

    def obtener_landmarks(self, frame):
        imagen_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.holistic.process(imagen_rgb)

        landmarks_lista = []

        manos = [
            resultado.left_hand_landmarks,
            resultado.right_hand_landmarks,
        ][: self.max_manos]
        centros_manos = []
        puntos_ubicacion_manos = []

        for mano_landmarks in manos:
            centros_manos.append(self._extender_landmarks(landmarks_lista, mano_landmarks))
            puntos_ubicacion_manos.append(self._punto_ubicacion_mano(mano_landmarks))

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
        referencias_visibles = [
            (nariz, "nariz", (0, 255, 255)),
            (boca, "boca", (0, 200, 255)),
            (oreja_izquierda, "oreja izq", (255, 100, 0)),
            (oreja_derecha, "oreja der", (255, 100, 0)),
            (pecho, "pecho", (0, 255, 0)),
        ]
        self.ultimas_referencias_visibles = referencias_visibles
        self.ultimas_manos_visibles = []

        for punto, texto, color in referencias_visibles:
            self._dibujar_referencia(frame, punto, color=color)

        for mano_centro, punto_ubicacion in zip(centros_manos, puntos_ubicacion_manos):
            punto_contexto = punto_ubicacion if punto_ubicacion is not None else mano_centro
            landmarks_lista.extend(self._caracteristicas_contexto(punto_contexto, referencias))
            descripcion = self._descripcion_ubicacion_mano(punto_contexto, referencias)
            if descripcion:
                self.ultimas_manos_visibles.append((punto_contexto, descripcion, (255, 255, 0)))

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
