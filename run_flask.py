import os
import secrets
import sys
import webbrowser
from pathlib import Path
from threading import Timer
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from flask import Flask, render_template, request, jsonify, session
from src.database.seed import seed_database
from src.services.traductor_texto import traducir_texto
from src.services.transcriptor_voz import TranscripcionError, transcribir_audio, vosk_configurado
from src.services.landmarks_avatar import obtener_landmarks_sena, listar_senas_con_landmarks
from src.config import MODEL_PATH, DATASET_PATH, LEGACY_DATASET_PATH
import subprocess
import csv

app = Flask(__name__)
# Las credenciales se leen del archivo .env (ver .env.example); nunca van en el codigo.
# Sin LSC_SECRET_KEY se genera una llave temporal (las sesiones se pierden al reiniciar).
# Sin LSC_DEV_PASSWORD el modo desarrollador queda deshabilitado.
app.secret_key = os.environ.get("LSC_SECRET_KEY") or secrets.token_hex(32)
DEV_PASSWORD = os.environ.get("LSC_DEV_PASSWORD", "")
seed_database()


def contar_muestras():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return 0, 0
    conteo = {}
    with dataset.open("r", encoding="utf-8") as f:
        for linea in f:
            etiqueta = linea.split(",", 1)[0].strip()
            if etiqueta:
                conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
    return sum(conteo.values()), len(conteo)


@app.route("/")
def index():
    muestras, clases = contar_muestras()
    modelo_listo = MODEL_PATH.exists()
    return render_template("index.html", muestras=muestras, clases=clases, modelo_listo=modelo_listo)


@app.route("/predecir")
def predecir():
    return render_template("predecir.html", modelo_listo=MODEL_PATH.exists())


@app.route("/predecir/lanzar", methods=["POST"])
def lanzar_prediccion():
    datos = request.get_json(silent=True) or {}
    tipo_fuente = str(datos.get("fuente", "local")).strip().lower()

    if tipo_fuente not in {"local", "ip"}:
        return jsonify({"ok": False, "error": "Fuente de cámara no válida."}), 400

    ejecutable = Path(sys.executable)
    if sys.platform == "win32":
        pythonw = ejecutable.with_name("pythonw.exe")
        if pythonw.exists():
            ejecutable = pythonw

    comando = [str(ejecutable), str(PROJECT_ROOT / "src" / "predecir_sena.py"), "--fuente", tipo_fuente]
    if tipo_fuente == "ip":
        url_camara = str(datos.get("url", "")).strip()
        url_analizada = urlparse(url_camara)
        if url_analizada.scheme not in {"http", "https"} or not url_analizada.netloc:
            return jsonify({"ok": False, "error": "Escribe una URL válida para DroidCam."}), 400
        comando.extend(["--url", url_camara])

    try:
        opciones_proceso = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            opciones_proceso["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            opciones_proceso["start_new_session"] = True

        subprocess.Popen(comando, **opciones_proceso)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/comunicar")
def comunicar():
    return render_template("comunicar.html", vosk_ok=vosk_configurado())


@app.route("/api/traducir", methods=["POST"])
def api_traducir():
    texto = request.json.get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Texto vacio"}), 400
    try:
        resultado = traducir_texto(texto)
        secuencia = []
        for item in resultado:
            if item["estado"] == "deletrear":
                secuencia.append("-".join(item["letras"]))
            else:
                secuencia.append(item["texto"])
        return jsonify({"ok": True, "secuencia": secuencia, "items": resultado})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/transcribir", methods=["POST"])
def api_transcribir():
    motor = request.form.get("motor", "auto")
    if "audio" not in request.files:
        return jsonify({"error": "Sin audio"}), 400
    audio_bytes = request.files["audio"].read()
    try:
        texto, motor_usado = transcribir_audio(audio_bytes, motor=motor)
        return jsonify({"ok": True, "texto": texto, "motor": motor_usado})
    except TranscripcionError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/animacion/<sena>", methods=["GET"])
def api_animacion(sena):
    """Devuelve la secuencia temporal completa de una seña para el avatar."""
    import json as _json
    ruta = PROJECT_ROOT / "data" / "avatar_movimientos" / f"{sena}.json"
    if not ruta.exists():
        return jsonify({"ok": False, "error": f"Sin animacion para '{sena}'"}), 404
    with open(ruta, "r", encoding="utf-8") as fh:
        datos = _json.load(fh)
    return jsonify({"ok": True, **datos})


@app.route("/api/animacion/<sena>", methods=["POST"])
def api_guardar_animacion(sena):
    """Guarda una animación de seña en formato rotaciones_v2 desde el browser."""
    import json as _json
    if not session.get("dev"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    datos = request.get_json(silent=True)
    if not datos or "frames" not in datos:
        return jsonify({"ok": False, "error": "Payload inválido (falta 'frames')"}), 400
    ruta = PROJECT_ROOT / "data" / "avatar_movimientos" / f"{sena}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        ruta.rename(ruta.with_name(f"{sena}.bak.json"))
    with open(ruta, "w", encoding="utf-8") as fh:
        _json.dump(datos, fh, ensure_ascii=False, separators=(",", ":"))
    return jsonify({"ok": True, "frames": len(datos["frames"])})


@app.route("/api/landmarks/<sena>")
def api_landmarks(sena):
    data = obtener_landmarks_sena(sena)
    if data is None:
        return jsonify({"ok": False, "error": "Sin datos"}), 404
    return jsonify({"ok": True, **data})


@app.route("/api/landmarks")
def api_landmarks_lista():
    return jsonify({"ok": True, "senas": listar_senas_con_landmarks()})


@app.route("/aprender")
def aprender():
    return render_template("aprender.html")


@app.route("/acerca")
def acerca():
    return render_template("acerca.html")


@app.route("/api/dev/login", methods=["POST"])
def dev_login():
    if not DEV_PASSWORD:
        return jsonify({"ok": False, "error": "Modo desarrollador no configurado (falta LSC_DEV_PASSWORD en .env)"}), 403
    password = request.json.get("password", "")
    if secrets.compare_digest(str(password), DEV_PASSWORD):
        session["dev"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Contraseña incorrecta"}), 401


@app.route("/api/dev/logout", methods=["POST"])
def dev_logout():
    session.pop("dev", None)
    return jsonify({"ok": True})


@app.route("/dev")
def dev_panel():
    if not session.get("dev"):
        return render_template("dev/login_requerido.html")
    muestras, clases = contar_muestras()
    modelo_listo = MODEL_PATH.exists()
    return render_template("dev/panel.html", muestras=muestras, clases=clases, modelo_listo=modelo_listo)


@app.route("/dev/capturar")
def dev_capturar():
    if not session.get("dev"):
        return render_template("dev/login_requerido.html")
    return render_template("dev/capturar.html")


@app.route("/dev/capturar-avatar")
def dev_capturar_avatar():
    if not session.get("dev"):
        return render_template("dev/login_requerido.html")
    return render_template("dev/capturar_avatar.html")


@app.route("/dev/capturar/lanzar", methods=["POST"])
def dev_lanzar_captura():
    if not session.get("dev"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "src" / "capturar_dataset.py")],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/dev/entrenar")
def dev_entrenar():
    if not session.get("dev"):
        return render_template("dev/login_requerido.html")
    muestras, clases = contar_muestras()
    return render_template("dev/entrenar.html", muestras=muestras, clases=clases)


@app.route("/dev/entrenar/lanzar", methods=["POST"])
def dev_lanzar_entrenamiento():
    if not session.get("dev"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403
    try:
        subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "src" / "entrenar_modelo.py")],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/dev/dataset")
def dev_dataset():
    if not session.get("dev"):
        return render_template("dev/login_requerido.html")
    conteo = {}
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if dataset.exists():
        with dataset.open("r", encoding="utf-8") as f:
            for linea in f:
                etiqueta = linea.split(",", 1)[0].strip()
                if etiqueta:
                    conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
    senas = sorted(conteo.items(), key=lambda x: -x[1])
    return render_template("dev/dataset.html", senas=senas, total=sum(conteo.values()))


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    Timer(1.2, abrir_navegador).start()
    app.run(debug=False, port=5000)
