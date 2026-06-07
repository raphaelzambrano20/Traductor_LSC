"""
capturar_avatar.py
==================
Captura la secuencia temporal completa de una seña LSC para animar el avatar 3D.

Diferencias clave con capturar_dataset.py:
  - Guarda TODOS los frames en orden temporal (no muestras ML separadas)
  - Coordenadas normalizadas relativo a nariz/pecho desde el momento de captura
  - Formato JSON por seña: data/avatar_movimientos/<sena>.json
  - Optimizado para REPRODUCCION en el avatar, no para entrenamiento del modelo

Sistema de coordenadas normalizado (guardado en cada .json):
  - Origen  : nariz del firmante
  - Escala  : 1 unidad = distancia nariz-pecho (Y de imagen)
  - X       : positivo = derecha del frame (= izquierda del firmante)
  - Y       : positivo = arriba (Y de imagen invertida)
  - Z       : positivo = hacia la camara (Z de MediaPipe negado)
  - mano_der: right_hand_landmarks de MediaPipe (convenio person-centric)
              mano derecha del firmante -> aparece a la IZQUIERDA del frame
              -> norm_x negativo (muneca a la izquierda de la nariz)
  - mano_izq: left_hand_landmarks de MediaPipe
              mano izquierda del firmante -> aparece a la DERECHA del frame
              -> norm_x positivo

Referencias por frame (mismo sistema normalizado):
  - hombro_der: hombro derecho del firmante  (norm_x negativo)
  - hombro_izq: hombro izquierdo del firmante (norm_x positivo)
  - oreja_der:  oreja derecha del firmante    (norm_x negativo)
  - oreja_izq:  oreja izquierda del firmante  (norm_x positivo)

Uso:
  python src/capturar_avatar.py
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import mediapipe as mp
import numpy as np

# ── Rutas ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from camara_stream import CamaraStream

RUTA_MOVIMIENTOS = PROJECT_ROOT / "data" / "avatar_movimientos"
RUTA_MOVIMIENTOS.mkdir(parents=True, exist_ok=True)

# ── Parámetros ────────────────────────────────────────────────────────────────
CALIDAD_MIN_MANO       = 0.05   # tamaño minimo visible de la mano (0-1)
SECS_CUENTA_REGRESIVA  = 3
CALIDAD_MIN_FRAMES_PCT = 0.75   # 75% de frames deben tener mano+cuerpo

DURACIONES = {
    "1": ("corta",  15),   # ≈ 0.5 s a 30 fps
    "2": ("media",  25),   # ≈ 0.8 s a 30 fps
    "3": ("larga",  40),   # ≈ 1.3 s a 30 fps
}

CATEGORIAS = [
    "cortesia",
    "emociones",
    "personas",
    "familia",
    "numeros",
    "abecedario",
    "frases",
    "otra",
]

# ── MediaPipe ─────────────────────────────────────────────────────────────────
mp_holistic      = mp.solutions.holistic
mp_dibujo        = mp.solutions.drawing_utils
HAND_CONNECTIONS = mp_holistic.HAND_CONNECTIONS


# ═══════════════════════════════════════════════════════════════════════════════
# Normalización de landmarks
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_refs_cuerpo(pose_lm):
    """
    Extrae nariz, pecho, boca, hombros y orejas del resultado Holistic.

    Indices MediaPipe Holistic pose:
      0  = nariz
      7  = oreja izquierda del firmante
      8  = oreja derecha del firmante
      9  = esquina izquierda de la boca
      10 = esquina derecha de la boca
      11 = hombro izquierdo del firmante
      12 = hombro derecho del firmante
      13 = codo izquierdo del firmante
      14 = codo derecho del firmante

    Retorna: nariz, pecho, boca, hombro_der, hombro_izq,
             oreja_der, oreja_izq, codo_der, codo_izq
    (todos None si pose_lm es None)
    """
    if pose_lm is None:
        return None, None, None, None, None, None, None, None, None, None, None
    lm = pose_lm.landmark
    nariz      = np.array([lm[0].x,  lm[0].y,  lm[0].z],  dtype=float)
    oreja_izq  = np.array([lm[7].x,  lm[7].y,  lm[7].z],  dtype=float)
    oreja_der  = np.array([lm[8].x,  lm[8].y,  lm[8].z],  dtype=float)
    boca_izq   = np.array([lm[9].x,  lm[9].y,  lm[9].z],  dtype=float)
    boca_der   = np.array([lm[10].x, lm[10].y, lm[10].z], dtype=float)
    boca       = (boca_izq + boca_der) / 2.0
    hombro_izq = np.array([lm[11].x, lm[11].y, lm[11].z], dtype=float)
    hombro_der = np.array([lm[12].x, lm[12].y, lm[12].z], dtype=float)
    pecho      = (hombro_izq + hombro_der) / 2.0
    codo_izq   = np.array([lm[13].x, lm[13].y, lm[13].z], dtype=float)
    codo_der   = np.array([lm[14].x, lm[14].y, lm[14].z], dtype=float)
    # Muñecas desde pose — z en espacio del cuerpo (mismo sistema que codo)
    # lm[15] = muñeca izquierda del firmante, lm[16] = muñeca derecha del firmante
    muneca_izq = np.array([lm[15].x, lm[15].y, lm[15].z], dtype=float)
    muneca_der = np.array([lm[16].x, lm[16].y, lm[16].z], dtype=float)
    return nariz, pecho, boca, hombro_der, hombro_izq, oreja_der, oreja_izq, codo_der, codo_izq, muneca_der, muneca_izq


def calcular_escala(nariz, pecho):
    """1 / distancia nariz-pecho en coordenadas de imagen (eje Y)."""
    return 1.0 / max(abs(float(nariz[1]) - float(pecho[1])), 0.04)


def normalizar_punto(pt, nariz, escala):
    """
    Normaliza un punto [x, y, z] con el mismo sistema que las manos:
      origen = nariz, escala = 1 / dist(nariz-pecho),
      Y invertida (arriba = positivo), Z invertido (hacia camara = positivo).
    """
    return [
        round((float(pt[0]) - float(nariz[0])) * escala, 5),
        round(-(float(pt[1]) - float(nariz[1])) * escala, 5),
        round(-float(pt[2]) * escala, 5),
    ]


def normalizar_mano(mano_lm, nariz, pecho):
    """
    Normaliza los 21 landmarks de una mano relativo a nariz/pecho.
    Retorna lista de 21 puntos [nx, ny, nz] o None si algun parametro es None.
    """
    if mano_lm is None or nariz is None or pecho is None:
        return None
    escala = calcular_escala(nariz, pecho)
    return [
        normalizar_punto([lm.x, lm.y, lm.z], nariz, escala)
        for lm in mano_lm.landmark
    ]


def calidad_mano(mano_lm):
    """Devuelve el tamaño aparente de la mano (0.0 si no detectada)."""
    if mano_lm is None:
        return 0.0
    pts = np.array([[lm.x, lm.y] for lm in mano_lm.landmark])
    return float(max(pts[:, 0].max() - pts[:, 0].min(),
                     pts[:, 1].max() - pts[:, 1].min()))


# ═══════════════════════════════════════════════════════════════════════════════
# Dibujo / HUD
# ═══════════════════════════════════════════════════════════════════════════════

def hud(frame, linea1, linea2="", barra=None):
    """Barra semitransparente superior y barra de progreso inferior."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 44), (0, 0, 0), -1)
    if barra is not None:
        cv2.rectangle(overlay, (0, h - 8), (int(w * barra), h), (0, 200, 100), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.putText(frame, linea1, (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
    if linea2:
        cv2.putText(frame, linea2, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)


def dibujar_mano(frame, mano_lm, color_pt=(80, 220, 80)):
    """Dibuja conexiones y puntos de una mano sobre el frame."""
    if mano_lm is None:
        return
    mp_dibujo.draw_landmarks(
        frame, mano_lm, HAND_CONNECTIONS,
        mp_dibujo.DrawingSpec(color=color_pt,       thickness=2, circle_radius=3),
        mp_dibujo.DrawingSpec(color=(180, 180, 180), thickness=1),
    )


def dibujar_punto_ref(frame, punto_norm, color, radio=7, etiqueta=""):
    """Dibuja un punto de referencia corporal (coords MediaPipe 0-1)."""
    if punto_norm is None:
        return
    h, w = frame.shape[:2]
    x, y = int(punto_norm[0] * w), int(punto_norm[1] * h)
    if 0 <= x < w and 0 <= y < h:
        cv2.circle(frame, (x, y), radio, color, -1)
        if etiqueta:
            cv2.putText(frame, etiqueta, (x + radio + 2, y + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)


# ═══════════════════════════════════════════════════════════════════════════════
# Selección interactiva
# ═══════════════════════════════════════════════════════════════════════════════

def elegir_camara():
    print("\n¿Que camara usar?")
    print("  1. Camara local (USB / integrada)")
    print("  2. DroidCam / IP Webcam (WiFi)")
    op = input("Opcion [1]: ").strip() or "1"
    if op == "2":
        url = input("URL [http://192.168.1.2:4747/video]: ").strip()
        return url or "http://192.168.1.2:4747/video"
    return 0


def seleccionar_sena():
    print("\n" + "═" * 52)
    print("  CAPTURA DE SEÑA PARA AVATAR LSC")
    print("═" * 52)

    nombre = input("\nNombre de la sena (ej: hola, bien, yo): ").strip().lower()
    if not nombre:
        print("Nombre vacio. Saliendo.")
        sys.exit(0)

    print("\nCategorias:")
    for i, cat in enumerate(CATEGORIAS, 1):
        print(f"  {i}. {cat}")
    cat_idx = input(f"Categoria [1-{len(CATEGORIAS)}]: ").strip()
    try:
        categoria = CATEGORIAS[int(cat_idx) - 1]
    except (ValueError, IndexError):
        categoria = "otra"

    print("\nDuracion de la secuencia:")
    for k, (ndur, nf) in DURACIONES.items():
        print(f"  {k}. {ndur:6s} ({nf} frames ≈ {nf/30:.1f}s)")
    dur_key = input("Duracion [2]: ").strip() or "2"
    nombre_dur, n_frames = DURACIONES.get(dur_key, DURACIONES["2"])

    print("\nManos requeridas:")
    print("  1. Una mano")
    print("  2. Dos manos")
    manos_req = int(input("Manos [1]: ").strip() or "1")
    manos_req = max(1, min(2, manos_req))

    return nombre, categoria, nombre_dur, n_frames, manos_req


# ═══════════════════════════════════════════════════════════════════════════════
# Captura de secuencia
# ═══════════════════════════════════════════════════════════════════════════════

def capturar_secuencia(camara, holistic, nombre_sena, n_frames, manos_req):
    """
    Loop principal de captura:
      preview -> cuenta regresiva -> capturando -> done

    Retorna lista de dicts de frames o None si el usuario cancela.
    """
    estado = "preview"
    cuenta_inicio = None
    frames_data = []

    print(f"\nPreparate para hacer la sena '{nombre_sena}'.")
    print("  R = iniciar cuenta regresiva  |  Q = cancelar\n")

    while True:
        ret, frame = camara.read()
        if not ret or frame is None:
            print("Error leyendo camara.")
            return None

        # ── Procesar con MediaPipe ──────────────────────────────────────────
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        res = holistic.process(frame_rgb)
        frame_rgb.flags.writeable = True

        nariz, pecho, boca, hombro_der, hombro_izq, oreja_der, oreja_izq, codo_der, codo_izq, muneca_der, muneca_izq = \
            obtener_refs_cuerpo(res.pose_landmarks)

        # MediaPipe usa convenio person-centric:
        #   right_hand_landmarks = mano DERECHA del firmante (aparece a la izq del frame)
        #   left_hand_landmarks  = mano IZQUIERDA del firmante (aparece a la der del frame)
        mano_der_lm = res.right_hand_landmarks
        mano_izq_lm = res.left_hand_landmarks

        cal_der = calidad_mano(mano_der_lm)
        cal_izq = calidad_mano(mano_izq_lm)
        manos_ok = (cal_der >= CALIDAD_MIN_MANO if manos_req >= 1 else True) and \
                   (cal_izq >= CALIDAD_MIN_MANO if manos_req == 2 else True)
        cuerpo_ok = nariz is not None and pecho is not None

        # ── Dibujar sobre frame original (coordenadas correctas) ────────────
        # Colores BGR que coinciden con las esferas del avatar 3D:
        #   rojo    (0,0,255)     = nariz      → avatar 0xff4444
        #   naranja (0,170,255)   = boca       → avatar 0xffaa00
        #   cyan    (255,208,0)   = orejas     → avatar 0x00d0ff
        #   verde   (136,255,68)  = pecho      → avatar 0x44ff88
        #   naranja (0,119,255)   = hombros    → avatar 0xff7700
        dibujar_mano(frame, mano_der_lm, color_pt=(80, 220,  80))
        dibujar_mano(frame, mano_izq_lm, color_pt=(80, 160, 255))
        dibujar_punto_ref(frame, nariz,      (0,   0, 255), 7, "nariz")
        dibujar_punto_ref(frame, boca,       (0, 170, 255), 6, "boca")
        dibujar_punto_ref(frame, pecho,      (136, 255, 68), 7, "pecho")
        dibujar_punto_ref(frame, hombro_der, (0, 119, 255), 6, "H.der")
        dibujar_punto_ref(frame, hombro_izq, (0, 119, 255), 6, "H.izq")
        dibujar_punto_ref(frame, oreja_der,  (255, 208, 0), 5, "O.der")
        dibujar_punto_ref(frame, oreja_izq,  (255, 208, 0), 5, "O.izq")
        dibujar_punto_ref(frame, codo_der,   (255, 0, 255), 6, "C.der")   # magenta = codo
        dibujar_punto_ref(frame, codo_izq,   (255, 0, 255), 6, "C.izq")
        dibujar_punto_ref(frame, muneca_der, (0, 255, 255), 6, "M.der")   # amarillo = muneca
        dibujar_punto_ref(frame, muneca_izq, (0, 255, 255), 6, "M.izq")

        # ── Voltear para vista natural (espejo) ─────────────────────────────
        frame_vis = cv2.flip(frame, 1)

        # ── Lógica de estado ────────────────────────────────────────────────
        ahora = time.time()

        if estado == "preview":
            cal_txt = f"D:{cal_der:.2f} I:{cal_izq:.2f}"
            estado_txt = "OK" if (manos_ok and cuerpo_ok) else "Ajusta posicion"
            hud(frame_vis,
                f"SENA: {nombre_sena}  |  R=Iniciar  Q=Cancelar",
                f"Manos {cal_txt}  Cuerpo:{'OK' if cuerpo_ok else 'NO'}  {estado_txt}")

        elif estado == "cuenta_regresiva":
            segs = max(0.0, SECS_CUENTA_REGRESIVA - (ahora - cuenta_inicio))
            num  = int(segs) + 1
            h_f, w_f = frame_vis.shape[:2]
            cv2.putText(frame_vis, str(num),
                        (w_f // 2 - 35, h_f // 2 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 4.0, (0, 220, 255), 6, cv2.LINE_AA)
            hud(frame_vis, f"SENA: {nombre_sena}  —  Preparate...")
            if segs <= 0:
                estado = "capturando"
                frames_data = []
                print("  Capturando ahora — haz la sena completa!")

        elif estado == "capturando":
            progreso = len(frames_data) / n_frames
            hud(frame_vis,
                f"CAPTURANDO: {nombre_sena}  [{len(frames_data)}/{n_frames}]",
                barra=progreso)

            # Guardar frame normalizado con todas las referencias
            if cuerpo_ok:
                escala = calcular_escala(nariz, pecho)
                mano_der_norm = normalizar_mano(mano_der_lm, nariz, pecho)
                mano_izq_norm = normalizar_mano(mano_izq_lm, nariz, pecho)
                ref = {
                    "boca":       normalizar_punto(boca,       nariz, escala),
                    "hombro_der": normalizar_punto(hombro_der, nariz, escala),
                    "hombro_izq": normalizar_punto(hombro_izq, nariz, escala),
                    "oreja_der":  normalizar_punto(oreja_der,  nariz, escala),
                    "oreja_izq":  normalizar_punto(oreja_izq,  nariz, escala),
                    "codo_der":   normalizar_punto(codo_der,   nariz, escala),
                    "codo_izq":   normalizar_punto(codo_izq,   nariz, escala),
                    "muneca_der": normalizar_punto(muneca_der, nariz, escala),
                    "muneca_izq": normalizar_punto(muneca_izq, nariz, escala),
                }
            else:
                # Sin referencia corporal: frame inutilizable para normalizar
                mano_der_norm = None
                mano_izq_norm = None
                ref = {}

            frames_data.append({
                "f":   len(frames_data),
                "der": mano_der_norm,
                "izq": mano_izq_norm,
                "ref": ref,
            })

            if len(frames_data) >= n_frames:
                estado = "done"
                print(f"  Captura completa: {n_frames} frames.")
                break

        cv2.imshow("Captura Avatar LSC", frame_vis)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('r'), ord('R')):
            if estado == "preview":
                estado        = "cuenta_regresiva"
                cuenta_inicio = time.time()
        elif key in (ord('q'), ord('Q')):
            print("  Captura cancelada.")
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()
    return frames_data


# ═══════════════════════════════════════════════════════════════════════════════
# Revisión visual (replay)
# ═══════════════════════════════════════════════════════════════════════════════

def _a_px(norm_pt, cx, cy, escala, w, h):
    """Convierte coordenada normalizada [nx, ny] a pixel en canvas de revision."""
    px = int(cx + norm_pt[0] * escala)
    py = int(cy - norm_pt[1] * escala)   # Y invertida de nuevo para pantalla
    return max(0, min(w - 1, px)), max(0, min(h - 1, py))


def reproducir_captura(frames_data, nombre_sena, manos_req):
    """
    Muestra los landmarks normalizados cuadro a cuadro en un canvas.
    Verde  = mano derecha del firmante
    Azul   = mano izquierda del firmante
    Azul   = nariz (origen)
    Verde  = pecho (0, -1)
    Naranja = hombros
    Amarillo = orejas

    Teclas: S=Guardar  R=Recapturar  Q=Cancelar
    """
    W, H      = 520, 440
    ESCALA    = 130    # pixeles por unidad normalizada
    CX, CY    = W // 2, H // 3
    CONEX     = list(HAND_CONNECTIONS)
    MS_FRAME  = int(1000 / 18)   # ~18 fps de reproduccion

    # Calidad rapida
    frames_validos = sum(
        1 for f in frames_data
        if (f.get("der") is not None or f.get("izq") is not None)
    )
    calidad_pct = round(frames_validos / max(len(frames_data), 1) * 100, 1)

    print(f"\n  Revisando '{nombre_sena}': {len(frames_data)} frames "
          f"| Calidad {calidad_pct}%")
    if calidad_pct < CALIDAD_MIN_FRAMES_PCT * 100:
        print(f"  Calidad baja ({calidad_pct}%). Considera recapturar.")
    print("  S = Guardar  |  R = Recapturar  |  Q = Cancelar")

    frame_idx = 0
    while True:
        canvas = np.full((H, W, 3), 38, dtype=np.uint8)

        # Cuadricula de referencia
        for gx in range(0, W, ESCALA):
            cv2.line(canvas, (gx, 0), (gx, H), (55, 55, 55), 1)
        for gy in range(0, H, ESCALA):
            cv2.line(canvas, (0, gy), (W, gy), (55, 55, 55), 1)

        # Ejes principales
        cv2.line(canvas, (CX, 0),  (CX, H),  (80, 80, 80), 1)
        cv2.line(canvas, (0, CY),  (W, CY),  (80, 80, 80), 1)

        # Referencias fijas del sistema de coordenadas
        cv2.circle(canvas, (CX, CY), 7, (80, 100, 255), -1)         # nariz (origen)
        pecho_px = _a_px([0, -1, 0], CX, CY, ESCALA, W, H)
        cv2.circle(canvas, pecho_px, 7, (80, 220, 80), -1)           # pecho (-1 en Y)
        cv2.putText(canvas, "nariz", (CX + 9, CY - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (130, 130, 200), 1)
        cv2.putText(canvas, "pecho", (pecho_px[0] + 9, pecho_px[1] - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 180, 100), 1)

        # Referencias del frame actual (hombros y orejas)
        f = frames_data[frame_idx % len(frames_data)]
        ref = f.get("ref", {})

        for rkey, color, label in [
            ("boca",       (0, 170, 255),  "boca"),
            ("hombro_der", (0, 119, 255),  "H.der"),
            ("hombro_izq", (0, 119, 255),  "H.izq"),
            ("oreja_der",  (255, 208, 0),  "O.der"),
            ("oreja_izq",  (255, 208, 0),  "O.izq"),
            ("codo_der",   (255, 0, 255),  "C.der"),
            ("codo_izq",   (255, 0, 255),  "C.izq"),
            ("muneca_der", (0, 255, 255),  "M.der"),
            ("muneca_izq", (0, 255, 255),  "M.izq"),
        ]:
            pt = ref.get(rkey)
            if pt:
                px = _a_px(pt, CX, CY, ESCALA, W, H)
                cv2.circle(canvas, px, 5, color, -1)
                cv2.putText(canvas, label, (px[0] + 6, px[1] + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1)

        # Landmarks de manos del frame actual
        for key, color_pt, color_con in [
            ("der", (80, 220,  80), (40, 140,  40)),
            ("izq", (80, 160, 255), (40, 100, 200)),
        ]:
            pts = f.get(key)
            if pts is None:
                continue
            # Conexiones
            for (a, b) in CONEX:
                if a < len(pts) and b < len(pts):
                    pa = _a_px(pts[a], CX, CY, ESCALA, W, H)
                    pb = _a_px(pts[b], CX, CY, ESCALA, W, H)
                    cv2.line(canvas, pa, pb, color_con, 1)
            # Puntos
            for i, pt in enumerate(pts):
                px = _a_px(pt, CX, CY, ESCALA, W, H)
                r  = 4 if i in (0, 5, 9, 13, 17) else 2   # nudillos mas grandes
                cv2.circle(canvas, px, r, color_pt, -1)

        # Info de frame
        cv2.putText(canvas, f"REVISION: {nombre_sena}", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Frame {frame_idx + 1}/{len(frames_data)}  "
                    f"Calidad {calidad_pct}%",
                    (10, H - 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (160, 160, 160), 1)
        cv2.putText(canvas, "[ S=Guardar   R=Recapturar   Q=Cancelar ]",
                    (10, H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (120, 120, 120), 1)

        # Leyenda
        for i, (col, txt) in enumerate([
            ((80, 220,  80),  "mano der"),
            ((80, 160, 255),  "mano izq"),
            ((0,   0,  255),  "nariz"),
            ((0, 170,  255),  "boca"),
            ((136, 255, 68),  "pecho"),
            ((0, 119,  255),  "hombros"),
            ((255, 208,   0), "orejas"),
            ((255,   0, 255), "codos"),
            ((0, 255,  255),  "munecas"),
        ]):
            yy = 18 + i * 14
            cv2.circle(canvas, (W - 90, yy), 5, col, -1)
            cv2.putText(canvas, txt, (W - 82, yy + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1)

        cv2.imshow("Revision — Avatar LSC", canvas)
        key = cv2.waitKey(MS_FRAME) & 0xFF

        if   key in (ord('s'), ord('S')):
            cv2.destroyAllWindows()
            return "guardar", calidad_pct
        elif key in (ord('r'), ord('R')):
            cv2.destroyAllWindows()
            return "recapturar", calidad_pct
        elif key in (ord('q'), ord('Q')):
            cv2.destroyAllWindows()
            return "cancelar", calidad_pct

        frame_idx = (frame_idx + 1) % len(frames_data)


# ═══════════════════════════════════════════════════════════════════════════════
# Guardado JSON
# ═══════════════════════════════════════════════════════════════════════════════

def guardar_json(frames_data, nombre, categoria, nombre_dur, manos_req, calidad_pct):
    """Guarda la secuencia en data/avatar_movimientos/<nombre>.json"""
    datos = {
        "sena":           nombre,
        "categoria":      categoria,
        "manos":          str(manos_req),
        "duracion":       nombre_dur,
        "total_frames":   len(frames_data),
        "calidad_pct":    calidad_pct,
        "coordenadas":    "normalizadas",
        "convenio": {
            "origen":       "nariz del firmante",
            "escala":       "1 unidad = distancia nariz-pecho (imagen Y)",
            "x":            "positivo = derecha del frame (izquierda del firmante)",
            "y":            "positivo = arriba (Y imagen invertida)",
            "z":            "positivo = hacia la camara (Z mediapipe negado)",
            "mano_der":     "right_hand_landmarks — mano derecha del firmante (norm_x negativo)",
            "mano_izq":     "left_hand_landmarks  — mano izquierda del firmante (norm_x positivo)",
            "ref.boca":       "centro de la boca (promedio esquinas)",
            "ref.hombro_der": "hombro derecho del firmante (norm_x negativo)",
            "ref.hombro_izq": "hombro izquierdo del firmante (norm_x positivo)",
            "ref.oreja_der":  "oreja derecha del firmante (norm_x negativo)",
            "ref.oreja_izq":  "oreja izquierda del firmante (norm_x positivo)",
            "ref.codo_der":   "codo derecho del firmante — usado para IK exacto del brazo",
            "ref.codo_izq":   "codo izquierdo del firmante — usado para IK exacto del brazo",
            "ref.muneca_der": "muneca derecha del firmante (pose lm16) — z en espacio cuerpo, IK wrist",
            "ref.muneca_izq": "muneca izquierda del firmante (pose lm15) — z en espacio cuerpo, IK wrist",
        },
        "frames": frames_data,
    }

    ruta = RUTA_MOVIMIENTOS / f"{nombre}.json"

    # Backup si ya existe una version anterior
    if ruta.exists():
        ruta_bak = RUTA_MOVIMIENTOS / f"{nombre}.bak.json"
        ruta.rename(ruta_bak)
        print(f"  (version anterior -> {ruta_bak.name})")

    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, separators=(",", ":"))

    kb = ruta.stat().st_size / 1024
    print(f"\n  Guardado: {ruta.name}  ({kb:.1f} KB)")
    print(f"     Frames:    {len(frames_data)}")
    print(f"     Calidad:   {calidad_pct}%")
    print(f"     Categoria: {categoria}")
    return ruta


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    fuente = elegir_camara()
    nombre, categoria, nombre_dur, n_frames, manos_req = seleccionar_sena()

    print("\n  Abriendo camara...")
    camara = CamaraStream(fuente)
    camara.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camara.set(cv2.CAP_PROP_FPS, 30)

    if not camara.isOpened():
        print("Error: no se pudo abrir la camara.")
        sys.exit(1)

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    try:
        while True:
            frames_data = capturar_secuencia(
                camara, holistic, nombre, n_frames, manos_req
            )
            if frames_data is None:
                print("\n  Saliendo sin guardar.")
                break

            decision, calidad_pct = reproducir_captura(
                frames_data, nombre, manos_req
            )

            if decision == "guardar":
                guardar_json(
                    frames_data, nombre, categoria,
                    nombre_dur, manos_req, calidad_pct
                )
                continuar = input("\n  Capturar otra sena? [s/N]: ").strip().lower()
                if continuar == "s":
                    nombre, categoria, nombre_dur, n_frames, manos_req = seleccionar_sena()
                else:
                    break

            elif decision == "recapturar":
                print("  Recapturando misma sena...")

            else:  # cancelar
                print("  Cancelado.")
                break

    finally:
        holistic.close()
        camara.release()
        cv2.destroyAllWindows()
        print("\n  Sesion terminada.")


if __name__ == "__main__":
    main()
