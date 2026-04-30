import subprocess
import os
from pathlib import Path
import sys
import types
import hashlib

from gtts import gTTS
import pygame

PYTHON_USER_BASE = Path(__file__).resolve().parents[1] / ".python_user_base"
PYTHON_USER_BASE.mkdir(exist_ok=True)
os.environ.setdefault("PYTHONUSERBASE", str(PYTHON_USER_BASE))

COMTYPES_CACHE = Path(__file__).resolve().parents[1] / ".comtypes_cache"
COMTYPES_CACHE.mkdir(exist_ok=True)
AUDIO_CACHE = Path(__file__).resolve().parents[1] / "audio_cache"
AUDIO_CACHE.mkdir(exist_ok=True)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import comtypes

    gen_module = types.ModuleType("comtypes.gen")
    gen_module.__path__ = [str(COMTYPES_CACHE)]
    comtypes.gen = gen_module
    sys.modules["comtypes.gen"] = gen_module
except Exception:
    pass

import pyttsx3

_motor = None
_pygame_iniciado = False


def literal_powershell(texto):
    return "'" + texto.replace("'", "''") + "'"


def hablar_pyttsx3(texto):
    global _motor

    if _motor is None:
        _motor = pyttsx3.init()
        _motor.setProperty("rate", 165)
        _motor.setProperty("volume", 1.0)

    _motor.say(texto)
    _motor.runAndWait()


def hablar_powershell(texto, esperar=False):
    comando = (
        "Add-Type -AssemblyName System.Speech; "
        "$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$voz.Rate = 0; "
        "$voz.Volume = 100; "
        f"$voz.Speak({literal_powershell(texto)})"
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if esperar:
        resultado = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", comando],
            capture_output=True,
            creationflags=flags,
            text=True,
            timeout=20,
        )
        if resultado.returncode != 0 and resultado.stderr:
            print("No se pudo hablar con PowerShell:")
            print(resultado.stderr.strip())
        return

    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-Command", comando],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def hablar_gtts(texto, esperar=False):
    global _pygame_iniciado

    nombre_legible = texto.lower().strip().replace(" ", "_") + ".mp3"
    nombre_hash = hashlib.sha1(texto.encode("utf-8")).hexdigest() + ".mp3"
    ruta_audio = AUDIO_CACHE / nombre_legible

    if not ruta_audio.exists():
        ruta_audio = AUDIO_CACHE / nombre_hash

    if not ruta_audio.exists():
        gTTS(text=texto, lang="es").save(str(ruta_audio))

    if not _pygame_iniciado:
        pygame.mixer.init()
        _pygame_iniciado = True

    pygame.mixer.music.load(str(ruta_audio))
    pygame.mixer.music.play()

    if esperar:
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)


def hablar_windows(texto, esperar=False):
    try:
        hablar_gtts(texto, esperar=esperar)
        return
    except Exception as exc:
        print(f"No se pudo hablar con gTTS/pygame: {exc}")

    try:
        hablar_pyttsx3(texto)
        return
    except Exception as exc:
        print(f"No se pudo hablar con pyttsx3: {exc}")

    hablar_powershell(texto, esperar=esperar)
