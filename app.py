import csv
import hashlib
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS

from src.config import DATASET_PATH, LEGACY_DATASET_PATH, MODEL_PATH, PROJECT_ROOT
from src.database.seed import seed_database
from src.services.avatar_animado import html_avatar_animado
from src.services.avatar_lsc import construir_secuencia_avatar
from src.services.recursos_lsc import (
    guardar_archivo_recurso,
    listar_items_lsc,
    mapa_recursos_embebibles,
)
from src.services.traductor_texto import traducir_texto
from src.services.transcriptor_voz import TranscripcionError, transcribir_audio, vosk_configurado
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

    filas = []
    with dataset.open("r", encoding="utf-8", newline="") as archivo:
        lector = csv.reader(archivo)
        for fila in lector:
            if fila and fila[0].strip():
                filas.append(fila[:8])

    if not filas:
        return None, None

    max_columnas = max(len(fila) for fila in filas)
    for fila in filas:
        fila.extend([""] * (max_columnas - len(fila)))

    columnas = ["sena"] + [f"p{i}" for i in range(max_columnas - 1)]
    datos = pd.DataFrame(filas, columns=columnas)
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


def mostrar_secuencia_lsc(traduccion):
    pasos = construir_secuencia_avatar(traduccion)
    if not pasos:
        return

    recursos_reales = [paso for paso in pasos if paso["recurso_tipo"] and paso["recurso_data"]]
    recursos_sin_embebido = [
        paso for paso in pasos if paso["recurso_tipo"] and not paso["recurso_data"]
    ]
    faltantes = [paso for paso in pasos if not paso["recurso_tipo"]]
    if recursos_reales:
        st.success(f"Usando {len(recursos_reales)} recurso(s) real(es) validado(s).")
    if recursos_sin_embebido:
        st.warning(
            "Hay recursos reales registrados, pero son muy pesados para reproducirlos "
            "dentro del avatar. Use clips cortos o comprimidos."
        )
    if faltantes:
        st.info(
            f"{len(faltantes)} paso(s) aun usan animacion aproximada o deletreo."
        )

    st.write("Avatar / secuencia visual:")
    components.html(
        html_avatar_animado(pasos, reproducir_auto=True),
        height=560,
        scrolling=False,
    )


def mostrar_avatar_en_vivo():
    st.write("Avatar en vivo:")
    components.html(
        html_avatar_animado(en_vivo=True, recursos=mapa_recursos_embebibles()),
        height=560,
        scrolling=False,
    )


def mostrar_gestor_recursos_lsc():
    with st.expander("Cargar videos reales de LSC"):
        st.write(
            "Asocie cada palabra o frase con un video validado. Cuando exista video, "
            "el sistema lo usara antes que la animacion aproximada."
        )
        st.caption("Tambien puede grabar con camara desde terminal:")
        st.code(f"{comando('capturar_video_lsc')} hola --duracion 3", language="powershell")
        items = listar_items_lsc()
        if not items:
            st.warning("Inicialice la base de datos antes de registrar recursos.")
            return

        opciones = {
            f"{item['tipo']} | {item['texto']} | {item['categoria']}": item
            for item in items
        }
        seleccion = st.selectbox("Palabra o frase", list(opciones.keys()))
        item = opciones[seleccion]
        tipos_recurso = ["video"] if item["tipo"] == "frase" else ["video", "imagen"]
        tipo_recurso = st.radio("Tipo de recurso", tipos_recurso, horizontal=True)
        archivo = st.file_uploader(
            "Archivo validado",
            type=["mp4", "mov", "avi", "webm", "mkv"] if tipo_recurso == "video" else ["jpg", "jpeg", "png", "webp"],
        )

        ruta_actual = item["ruta_video"] if tipo_recurso == "video" else item["ruta_imagen"]
        if ruta_actual:
            st.caption(f"Recurso actual: {ruta_actual}")

        if st.button("Guardar recurso LSC"):
            if archivo is None:
                st.error("Seleccione un archivo.")
            else:
                try:
                    ruta = guardar_archivo_recurso(
                        archivo,
                        item["texto"],
                        item["tipo"],
                        tipo_recurso,
                    )
                    st.success(f"Recurso guardado: {ruta}")
                except Exception as exc:
                    st.error(f"No se pudo guardar el recurso: {exc}")

        resumen = pd.DataFrame(items)
        resumen["tiene_video"] = resumen["ruta_video"].fillna("").ne("")
        resumen["tiene_imagen"] = resumen["ruta_imagen"].fillna("").ne("")
        st.dataframe(
            resumen[["tipo", "texto", "categoria", "tiene_video", "tiene_imagen"]],
            use_container_width=True,
            hide_index=True,
        )


def mostrar_resultado_traduccion_lsc(texto):
    traduccion = traducir_texto(texto)
    if not traduccion:
        st.warning("No se encontraron palabras para traducir.")
        return

    secuencia = []
    filas = []
    for item in traduccion:
        if item["estado"] == "deletrear":
            secuencia.append("-".join(item["letras"]))
        else:
            secuencia.append(item["texto"])
        filas.append(
            {
                "entrada": item["encontrado_por"],
                "traduccion": item["texto"],
                "categoria": item["categoria"],
                "tipo": item["tipo"],
                "estado": item["estado"],
            }
        )

    st.write("Secuencia sugerida:")
    st.code(" | ".join(secuencia), language="text")
    mostrar_secuencia_lsc(traduccion)
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


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
        "Traducir voz/texto a LSC",
        "Ver dataset",
        "Texto a voz",
        "Acerca del proyecto",
    ],
)

if opcion == "Inicio":
    st.subheader("Flujo recomendado")
    st.write("1. Capture muestras por cada sena LSC con la camara, incluyendo ubicacion y movimiento.")
    st.write("2. Entrene el modelo con el dataset capturado.")
    st.write("3. Ejecute la prediccion en tiempo real.")
    st.info(
        "La captura usa manos, rostro y pose corporal para diferenciar senas cerca de "
        "la boca, orejas, cara o pecho."
    )
    st.info(
        "Capture tambien muestras con la etiqueta sin_sena o reposo para que el modelo "
        "aprenda cuando no debe agregar palabras."
    )
    st.info(f"Carpeta del proyecto: {PROJECT_ROOT}")
    st.write("Vocabulario inicial sugerido:")
    st.write(", ".join(VOCABULARIO_INICIAL_LSC))

elif opcion == "Capturar dataset":
    st.subheader("Capturar dataset")
    st.write(
        "Ejecute este comando en una terminal, prepare la mano y use la tecla R justo "
        "antes de hacer cada sena LSC. Mantenga visibles rostro y hombros para guardar "
        "la altura relativa de la mano."
    )
    st.caption(
        "Para reducir falsos positivos, capture una etiqueta llamada sin_sena con manos "
        "en reposo y movimientos de transicion."
    )
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
    st.write(
        "La prediccion usa OpenCV y MediaPipe Holistic en una ventana local de camara. "
        "La vista se muestra en modo espejo, acumula un parrafo sin repetir palabras "
        "seguidas y limpia el parrafo cuando la voz lo reproduce tras 2 segundos sin "
        "movimiento de manos."
    )
    st.caption("Si el modelo predice sin_sena, reposo o transicion, no se agrega texto al parrafo.")
    st.code(comando("predecir_sena"), language="powershell")

elif opcion == "Traducir voz/texto a LSC":
    st.subheader("Traducir voz/texto a LSC")
    st.write(
        "Grabe voz o escriba texto. El texto reconocido queda editable antes de mostrar "
        "la secuencia LSC."
    )

    if "texto_lsc" not in st.session_state:
        st.session_state.texto_lsc = ""
    if "ultimo_audio_lsc" not in st.session_state:
        st.session_state.ultimo_audio_lsc = None
    if "traducir_lsc_ahora" not in st.session_state:
        st.session_state.traducir_lsc_ahora = False

    if st.button("Inicializar o actualizar base de datos", key="seed_voz_texto_lsc"):
        seed_database()
        st.success("Base de datos LSC lista.")

    mostrar_gestor_recursos_lsc()
    mostrar_avatar_en_vivo()

    motor_opciones = {
        "Automatico": "auto",
        "Vosk local": "vosk",
        "Google online": "google",
    }
    motor_label = st.selectbox("Motor de voz a texto", list(motor_opciones.keys()))
    if motor_label == "Vosk local" and not vosk_configurado():
        st.warning(
            "Vosk local aun no esta configurado. Puede usar Google online o escribir el texto."
        )
    elif motor_label == "Automatico" and not vosk_configurado():
        st.caption("Automatico usara Google online mientras no exista el modelo local Vosk.")

    audio = st.audio_input("Grabar voz")
    if audio is not None:
        audio_bytes = audio.getvalue()
        audio_id = hashlib.sha1(audio_bytes).hexdigest()
        if st.button("Transcribir voz"):
            try:
                texto_reconocido, motor_usado = transcribir_audio(
                    audio_bytes,
                    motor=motor_opciones[motor_label],
                )
                st.session_state.texto_lsc = texto_reconocido
                st.session_state.ultimo_audio_lsc = audio_id
                st.session_state.traducir_lsc_ahora = True
                st.success(f"Texto reconocido con {motor_usado}: {texto_reconocido}")
            except TranscripcionError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"No se pudo transcribir el audio: {exc}")

    texto = st.text_area(
        "Texto reconocido o escrito",
        key="texto_lsc",
        placeholder="Ejemplo: hola mama quiero agua azul por favor",
    )

    traducir_click = st.button("Traducir a LSC")
    traducir_ahora = traducir_click or st.session_state.traducir_lsc_ahora
    st.session_state.traducir_lsc_ahora = False

    if traducir_ahora:
        if not texto.strip():
            st.error("Debe grabar voz o escribir un texto.")
        else:
            mostrar_resultado_traduccion_lsc(texto)

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
        "SpeechRecognition, Vosk y Pandas."
    )
