import json
import tempfile
from pathlib import Path

import speech_recognition as sr

from src.config import PROJECT_ROOT


MODELO_VOSK_ES = PROJECT_ROOT / "models" / "vosk-model-small-es-0.42"


class TranscripcionError(RuntimeError):
    pass


def _audio_data_desde_bytes(audio_bytes):
    reconocedor = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as archivo:
        archivo.write(audio_bytes)
        ruta_audio = archivo.name

    try:
        with sr.AudioFile(ruta_audio) as fuente:
            return reconocedor, reconocedor.record(fuente)
    finally:
        Path(ruta_audio).unlink(missing_ok=True)


def vosk_configurado():
    try:
        import vosk  # noqa: F401
    except Exception:
        return False

    return MODELO_VOSK_ES.exists()


def transcribir_google(audio_bytes):
    reconocedor, datos_audio = _audio_data_desde_bytes(audio_bytes)
    try:
        return reconocedor.recognize_google(datos_audio, language="es-CO").strip()
    except sr.UnknownValueError as exc:
        raise TranscripcionError("No se entendio el audio. Intente hablar mas claro o mas cerca.") from exc
    except Exception as exc:
        raise TranscripcionError(
            "No se pudo conectar con el reconocimiento de Google. "
            "Revise internet/firewall o use el motor local Vosk."
        ) from exc


def transcribir_vosk(audio_bytes):
    if not MODELO_VOSK_ES.exists():
        raise TranscripcionError(f"No se encontro el modelo local Vosk en {MODELO_VOSK_ES}.")

    try:
        from vosk import KaldiRecognizer, Model, SetLogLevel
    except Exception as exc:
        raise TranscripcionError("Falta instalar la dependencia local: vosk.") from exc

    _, datos_audio = _audio_data_desde_bytes(audio_bytes)
    SetLogLevel(-1)
    reconocedor = KaldiRecognizer(Model(str(MODELO_VOSK_ES)), 16000)
    reconocedor.AcceptWaveform(datos_audio.get_raw_data(convert_rate=16000, convert_width=2))
    resultado = json.loads(reconocedor.FinalResult())
    texto = resultado.get("text", "").strip()

    if not texto:
        raise TranscripcionError("No se entendio el audio con Vosk. Intente grabar otra vez.")

    return texto


def transcribir_audio(audio_bytes, motor="auto"):
    motor = str(motor or "auto").lower()

    if motor == "vosk":
        return transcribir_vosk(audio_bytes), "Vosk local"

    if motor == "google":
        return transcribir_google(audio_bytes), "Google online"

    errores = []
    if vosk_configurado():
        try:
            return transcribir_vosk(audio_bytes), "Vosk local"
        except TranscripcionError as exc:
            errores.append(str(exc))

    try:
        return transcribir_google(audio_bytes), "Google online"
    except TranscripcionError as exc:
        errores.append(str(exc))

    raise TranscripcionError(" ".join(errores) or "No se pudo transcribir el audio.")
