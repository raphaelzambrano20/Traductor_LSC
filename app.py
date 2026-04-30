import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from gtts import gTTS

from src.config import DATASET_PATH, ENTRADA_MODELO, LEGACY_DATASET_PATH, MODEL_PATH, PROJECT_ROOT
from src.vocabulario_lsc import VOCABULARIO_INICIAL_LSC


st.set_page_config(
    page_title="Traductor LSC con IA",
    page_icon="🤟",
    layout="centered",
)


def contar_muestras():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return 0, 0, dataset

    conteo = {}
    with dataset.open("r", encoding="utf-8") as archivo:
        for linea in archivo:
            etiqueta = linea.split(",", 1)[0].strip()
            if etiqueta:
                conteo[etiqueta] = conteo.get(etiqueta, 0) + 1

    return sum(conteo.values()), len(conteo), dataset


def cargar_resumen_dataset():
    dataset = DATASET_PATH if DATASET_PATH.exists() else LEGACY_DATASET_PATH
    if not dataset.exists():
        return None, None

    columnas = ["sena"] + [f"p{i}" for i in range(ENTRADA_MODELO)]
    datos = pd.read_csv(dataset, header=None, names=columnas, usecols=range(ENTRADA_MODELO + 1))
    resumen = (
        datos["sena"]
        .value_counts()
        .rename_axis("sena")
        .reset_index(name="muestras")
        .sort_values(["muestras", "sena"], ascending=[False, True])
    )
    return datos, resumen


def comando(modulo):
    python = Path(sys.executable).name
    return f"{python} src/{modulo}.py"


st.title("Traductor LSC con Inteligencia Artificial")
st.write(
    "Prototipo para apoyar la comunicacion entre estudiantes con discapacidad auditiva, "
    "docentes y companeros mediante reconocimiento de Lengua de Senas Colombiana, texto y voz."
)

muestras, clases, dataset = contar_muestras()

col1, col2, col3 = st.columns(3)
col1.metric("Muestras", muestras)
col2.metric("Senas registradas", clases)
col3.metric("Modelo", "Listo" if MODEL_PATH.exists() else "Pendiente")

st.divider()

opcion = st.sidebar.radio(
    "Seleccione una opcion",
    [
        "Inicio",
        "Capturar dataset",
        "Entrenar modelo",
        "Traducir sena a texto",
        "Ver dataset",
        "Texto a voz",
        "Voz a texto",
        "Acerca del proyecto",
    ],
)

if opcion == "Inicio":
    st.subheader("Flujo recomendado")
    st.write("1. Capture muestras por cada sena LSC con la camara.")
    st.write("2. Entrene el modelo con el dataset capturado.")
    st.write("3. Ejecute la prediccion en tiempo real.")
    st.info(f"Carpeta del proyecto: {PROJECT_ROOT}")
    st.write("Vocabulario inicial sugerido:")
    st.write(", ".join(VOCABULARIO_INICIAL_LSC))

elif opcion == "Capturar dataset":
    st.subheader("Capturar dataset")
    st.write("Ejecute este comando en una terminal y use la tecla S para guardar cada muestra LSC.")
    st.code(comando("capturar_dataset"), language="powershell")
    st.caption(f"Dataset actual: {dataset}")

elif opcion == "Entrenar modelo":
    st.subheader("Entrenar modelo")
    if muestras == 0:
        st.warning("Aun no hay muestras. Primero capture senas LSC con la camara.")
    else:
        st.write("Entrene el clasificador despues de capturar varias muestras por sena LSC.")
        st.code(comando("entrenar_modelo"), language="powershell")

elif opcion == "Traducir sena a texto":
    st.subheader("Traducir sena a texto")
    if not MODEL_PATH.exists():
        st.warning("Primero debe entrenar el modelo.")
    st.write("La prediccion usa OpenCV y MediaPipe en una ventana local de camara.")
    st.code(comando("predecir_sena"), language="powershell")

elif opcion == "Ver dataset":
    st.subheader("Dataset capturado")
    datos, resumen = cargar_resumen_dataset()

    if datos is None:
        st.warning("Todavia no existe el dataset. Capture primero algunas muestras LSC.")
    else:
        minimo_recomendado = 30
        st.write(f"Archivo: `{dataset}`")
        st.dataframe(resumen, use_container_width=True, hide_index=True)

        clases_bajas = resumen[resumen["muestras"] < minimo_recomendado]
        if not clases_bajas.empty:
            st.warning(
                "Algunas senas tienen pocas muestras. Para una primera prueba, "
                f"intente llegar minimo a {minimo_recomendado} por cada sena."
            )
        else:
            st.success("El dataset ya tiene una cantidad inicial razonable por sena.")

        st.write("Ultimas muestras capturadas:")
        st.dataframe(datos.tail(10).iloc[:, :8], use_container_width=True, hide_index=True)

elif opcion == "Texto a voz":
    st.subheader("Convertir texto a voz")
    texto = st.text_area("Escriba el texto que desea convertir a voz:")

    if st.button("Generar voz"):
        if not texto.strip():
            st.error("Debe escribir un texto.")
        else:
            try:
                tts = gTTS(text=texto, lang="es")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as archivo:
                    tts.save(archivo.name)
                    st.audio(archivo.name, format="audio/mp3")
                st.success("Audio generado correctamente.")
            except Exception as exc:
                st.error(f"No se pudo generar el audio: {exc}")

elif opcion == "Voz a texto":
    st.subheader("Voz a texto")
    st.write("Puede grabar o cargar un audio corto en espanol para transcribirlo.")
    audio = st.audio_input("Grabar audio")

    if audio is None:
        st.info("Cuando grabe un audio, se intentara transcribir con SpeechRecognition.")
    else:
        try:
            import speech_recognition as sr

            reconocedor = sr.Recognizer()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as archivo:
                archivo.write(audio.getbuffer())
                ruta_audio = archivo.name

            with sr.AudioFile(ruta_audio) as fuente:
                datos_audio = reconocedor.record(fuente)

            texto = reconocedor.recognize_google(datos_audio, language="es-CO")
            st.success(texto)
        except Exception as exc:
            st.error(f"No se pudo transcribir el audio: {exc}")

elif opcion == "Acerca del proyecto":
    st.subheader("Acerca del proyecto")
    st.write(
        "Proyecto academico orientado al desarrollo de un software de traduccion "
        "bidireccional de Lengua de Senas Colombiana mediante inteligencia artificial, "
        "vision por computador y procesamiento de voz."
    )
    st.write(
        "El entrenamiento debe realizarse con muestras propias de LSC o con datasets "
        "academicos de Lengua de Senas Colombiana como LSC50, LSC70 o LSC-54."
    )
    st.write(
        "Tecnologias: Python, OpenCV, MediaPipe, Scikit-learn, Streamlit, gTTS, "
        "SpeechRecognition y Pandas."
    )
