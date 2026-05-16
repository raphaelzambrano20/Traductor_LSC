import sys
import webbrowser
from pathlib import Path
from threading import Timer

PROJECT_ROOT = Path(__file__).resolve().parent
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
app.secret_key = "lsc_dev_2026"
DEV_PASSWORD = "lsc2026"
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
    try:
        subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "src" / "predecir_sena.py")],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
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
    password = request.json.get("password", "")
    if password == DEV_PASSWORD:
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
