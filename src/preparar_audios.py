import pandas as pd
from gtts import gTTS

from config import DATASET_PATH, LEGACY_DATASET_PATH
from voz import AUDIO_CACHE


def preparar_audios():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH

    if not dataset.exists():
        print("Todavia no existe el dataset.")
        return

    etiquetas = sorted(pd.read_csv(dataset, header=None).iloc[:, 0].dropna().unique())

    if not etiquetas:
        print("No hay senas en el dataset.")
        return

    print("Preparando audios para:")
    for etiqueta in etiquetas:
        texto = str(etiqueta).replace("_", " ")
        ruta_audio = AUDIO_CACHE / f"{texto}.mp3"

        if ruta_audio.exists():
            print(f"- {texto}: ya existe")
            continue

        print(f"- {texto}: generando")
        gTTS(text=texto, lang="es").save(str(ruta_audio))

    print(f"Audios guardados en: {AUDIO_CACHE}")


if __name__ == "__main__":
    preparar_audios()
