import csv
import os
import sys
import warnings
import time
from collections import deque
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype.*")

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from caracteristicas_temporales import extraer_caracteristicas_temporales
from config import DATA_DIR, DATASET_PATH, FRAMES_SECUENCIA
from detector_manos import DetectorManos
from database.registro_vocabulario import listar_categorias, obtener_sena, registrar_sena
from vocabulario_lsc import normalizar_etiqueta


MODOS_CAPTURA = {
    "1": ("corta", 12),
    "2": ("media", 20),
    "3": ("larga", 32),
}
CALIDAD_MINIMA_MANO = 0.08
SEGUNDOS_CUENTA_REGRESIVA = 3


def capturar_sena(nombre_sena, cantidad_muestras=100, frames_secuencia=FRAMES_SECUENCIA, manos_requeridas=1, fuente_camara=0):
    nombre_sena = normalizar_etiqueta(nombre_sena)

    if not nombre_sena:
        print("Debe digitar el nombre de la sena LSC.")
        return

    detector = DetectorManos()
    camara = cv2.VideoCapture(fuente_camara)
    if fuente_camara == 0:
        camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camara.set(cv2.CAP_PROP_FPS, 30)
    historial_landmarks = deque(maxlen=frames_secuencia)
    ultimo_guardado = 0
    grabando_movimiento = False
    cuenta_regresiva_hasta = None
    frames_minimos_manos = max(1, int(frames_secuencia * 0.7))

    DATA_DIR.mkdir(exist_ok=True)
    muestras_guardadas = 0

    print("Camara abierta. Prepare la mano y presione R para iniciar cuenta regresiva.")
    print(
        f"El sistema grabara {frames_secuencia} frames y exige {manos_requeridas} mano(s) "
        f"en al menos {frames_minimos_manos} frames."
    )

    with DATASET_PATH.open(mode="a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)

        while muestras_guardadas < cantidad_muestras:
            ret, frame = camara.read()

            if not ret:
                print("No se pudo acceder a la camara.")
                break

            frame, landmarks = detector.obtener_landmarks(frame)
            ahora = time.time()
            if cuenta_regresiva_hasta is not None and ahora >= cuenta_regresiva_hasta:
                historial_landmarks.clear()
                grabando_movimiento = True
                cuenta_regresiva_hasta = None
                print("Grabando movimiento... haga la sena ahora.")

            if grabando_movimiento:
                historial_landmarks.append(landmarks)
            frame_mostrado = cv2.flip(frame, 1)
            detector.dibujar_referencias_visibles(frame_mostrado, espejo=True)
            detector.dibujar_ubicaciones_manos(frame_mostrado, espejo=True)
            manos_detectadas, cobertura_manos = detector.calidad_manos(landmarks)
            calidad_ok = manos_detectadas >= manos_requeridas and cobertura_manos >= CALIDAD_MINIMA_MANO
            color_calidad = (0, 255, 0) if calidad_ok else (0, 0, 255)
            texto_calidad = (
                f"Manos visibles: {manos_detectadas} | Calidad: {cobertura_manos:.2f}"
            )

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
                "R iniciar cuenta regresiva | Q salir",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
            estado = "Grabando..." if grabando_movimiento else "Listo para grabar"
            if cuenta_regresiva_hasta is not None:
                segundos_restantes = max(0, int(cuenta_regresiva_hasta - ahora) + 1)
                estado = f"Prepare la sena: {segundos_restantes}"
            cv2.putText(
                frame_mostrado,
                f"{estado} | Frames: {len(historial_landmarks)}/{frames_secuencia}",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame_mostrado,
                texto_calidad,
                (10, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color_calidad,
                2,
            )
            if not calidad_ok:
                cv2.putText(
                    frame_mostrado,
                    f"Necesita {manos_requeridas} mano(s) visibles y buena luz antes de R",
                    (10, 170),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )
            if time.time() - ultimo_guardado < 1.2:
                cv2.putText(
                    frame_mostrado,
                    "Muestra de movimiento guardada",
                    (10, 205),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                )

            cv2.imshow("Captura de senas", frame_mostrado)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("r") and not grabando_movimiento and cuenta_regresiva_hasta is None:
                if calidad_ok:
                    cuenta_regresiva_hasta = time.time() + SEGUNDOS_CUENTA_REGRESIVA
                    print("Cuenta regresiva iniciada: prepare la sena.")
                else:
                    print(
                        f"Antes de grabar debe haber {manos_requeridas} mano(s) visibles "
                        "y buena iluminacion."
                    )

            if grabando_movimiento and len(historial_landmarks) == frames_secuencia:
                caracteristicas = extraer_caracteristicas_temporales(historial_landmarks)
                frames_con_mano = 0
                for item in historial_landmarks:
                    manos_frame, _ = detector.calidad_manos(item)
                    if manos_frame >= manos_requeridas:
                        frames_con_mano += 1
                calidad_promedio = sum(
                    detector.calidad_manos(item)[1] for item in historial_landmarks
                ) / len(historial_landmarks)
                captura_valida = (
                    frames_con_mano >= frames_minimos_manos
                    and calidad_promedio >= CALIDAD_MINIMA_MANO
                    and any(caracteristicas)
                )
                if captura_valida:
                    escritor.writerow([nombre_sena] + caracteristicas)
                    archivo.flush()
                    muestras_guardadas += 1
                    ultimo_guardado = time.time()
                    print(
                        f"Guardada muestra {muestras_guardadas}/{cantidad_muestras} "
                        f"de '{nombre_sena}' con {len(caracteristicas)} valores temporales."
                    )
                else:
                    print(
                        "Muestra descartada: la mano no se vio con suficiente claridad "
                        f"({frames_con_mano}/{frames_secuencia} frames con {manos_requeridas} mano(s), "
                        f"calidad {calidad_promedio:.2f})."
                    )
                historial_landmarks.clear()
                grabando_movimiento = False

            if tecla == ord("q"):
                break

    camara.release()
    cv2.destroyAllWindows()


def contar_muestras_por_sena():
    if not DATASET_PATH.exists():
        return {}

    conteo = {}
    with DATASET_PATH.open("r", encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        for fila in lector:
            if fila and fila[0].strip():
                etiqueta = fila[0].strip()
                conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
    return conteo


def elegir_sena():
    conteo = contar_muestras_por_sena()
    senas = sorted(conteo)

    if senas:
        print("\nSenas ya capturadas:")
        for indice, sena in enumerate(senas, start=1):
            print(f"{indice}. {sena} ({conteo[sena]} muestras)")
        print("N. Capturar una sena nueva")

        entrada = input("Seleccione una sena existente por numero o escriba N: ").strip()
        if entrada.isdigit():
            indice = int(entrada)
            if 1 <= indice <= len(senas):
                return senas[indice - 1], True, conteo[senas[indice - 1]]

    nombre = input("Digite el nombre de la sena LSC: ").strip()
    return nombre, False, 0


def pedir_categoria():
    categorias = listar_categorias()
    if categorias:
        print("\nCategorias disponibles:")
        for indice, categoria in enumerate(categorias, start=1):
            print(f"{indice}. {categoria['nombre']}")

    entrada = input("Categoria de la sena (nombre o numero): ").strip()
    if entrada.isdigit() and categorias:
        indice = int(entrada)
        if 1 <= indice <= len(categorias):
            return categorias[indice - 1]["nombre"]

    return entrada


def pedir_sinonimos():
    texto = input("Sinonimos opcionales separados por coma (Enter para omitir): ").strip()
    if not texto:
        return []
    return [item.strip() for item in texto.split(",") if item.strip()]


def pedir_modo_captura():
    print("\nTipo de sena:")
    print("1. Corta  (12 frames)")
    print("2. Media  (20 frames)")
    print("3. Larga  (32 frames)")
    entrada = input("Seleccione tipo de sena [2]: ").strip() or "2"
    nombre_modo, frames = MODOS_CAPTURA.get(entrada, MODOS_CAPTURA["2"])
    print(f"Modo seleccionado: {nombre_modo} ({frames} frames)")
    return frames


def pedir_manos_requeridas():
    entrada = input("Cuantas manos requiere esta sena? [1/2, Enter=1]: ").strip() or "1"
    if entrada == "2":
        return 2
    return 1


def elegir_camara():
    print("\nFuente de camara:")
    print("1. Camara local del PC (por defecto)")
    print("2. Camara IP - DroidCam (celular por WiFi)")
    entrada = input("Seleccione [1]: ").strip() or "1"
    if entrada == "2":
        url = input("URL de DroidCam [http://192.168.1.2:4747/video]: ").strip()
        return url or "http://192.168.1.2:4747/video"
    return 0


if __name__ == "__main__":
    fuente_camara = elegir_camara()
    nombre, existe_en_dataset, muestras_actuales = elegir_sena()
    etiqueta_normalizada = normalizar_etiqueta(nombre)

    sena_registrada = obtener_sena(etiqueta_normalizada)
    if existe_en_dataset and sena_registrada:
        etiqueta = etiqueta_normalizada
        print(
            f"Sena seleccionada: {etiqueta} -> {sena_registrada['categoria']} "
            f"({muestras_actuales} muestras actuales)"
        )
    else:
        if existe_en_dataset:
            print("La sena existe en el dataset, pero no estaba registrada en SQLite.")
        categoria = pedir_categoria()
        sinonimos = pedir_sinonimos()
        etiqueta = registrar_sena(nombre, categoria, sinonimos)
        print(f"Sena registrada en la base: {etiqueta} -> {categoria}")

    cantidad = int(input("Cantidad de muestras: "))
    frames_secuencia = pedir_modo_captura()
    manos_requeridas = pedir_manos_requeridas()
    if existe_en_dataset:
        print(f"Se agregaran {cantidad} muestras nuevas a '{etiqueta}'.")
        print(f"Total esperado al terminar: {muestras_actuales + cantidad}")
    capturar_sena(
        etiqueta,
        cantidad,
        frames_secuencia=frames_secuencia,
        manos_requeridas=manos_requeridas,
        fuente_camara=fuente_camara,
    )
