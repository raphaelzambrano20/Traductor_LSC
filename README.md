# Traductor LSC con IA

Prototipo academico de traduccion bidireccional para Lengua de Senas Colombiana (LSC).
Incluye captura de dataset con camara, entrenamiento de un clasificador y prediccion en
tiempo real usando MediaPipe, OpenCV y Scikit-learn.

El proyecto esta pensado solo para LSC. No se recomienda entrenarlo con ASL u otras
lenguas de senas, porque cada lengua tiene vocabulario, gramatica y gestos propios.

## Ejecutar la app

```powershell
venv\Scripts\streamlit.exe run app.py
```

Luego abra la URL que muestre Streamlit, normalmente:

```text
http://localhost:8501
```

## Flujo de trabajo

1. Capturar muestras de una sena LSC:

```powershell
venv\Scripts\python.exe src\capturar_dataset.py
```

Digite el nombre de la sena, indique la cantidad de muestras y presione `S` para guardar
cada muestra. Presione `Q` para salir.

2. Entrenar el modelo:

```powershell
venv\Scripts\python.exe src\entrenar_modelo.py
```

3. Ver el avance del dataset:

```powershell
venv\Scripts\python.exe src\ver_dataset.py
```

4. Borrar una sena completa del dataset:

```powershell
venv\Scripts\python.exe src\borrar_sena.py nombre_de_la_sena
```

Ejemplo:

```powershell
venv\Scripts\python.exe src\borrar_sena.py hola
```

5. Probar prediccion en tiempo real:

```powershell
venv\Scripts\python.exe src\predecir_sena.py
```

Si la deteccion muestra la sena pero no se escucha la voz, prepare primero los audios:

```powershell
venv\Scripts\python.exe src\preparar_audios.py
```

Ese comando requiere internet solo para generar los MP3. Despues la prediccion puede
reproducir esos audios desde `audio_cache/`.

Presione `Q` para cerrar la ventana de camara.

## Archivos generados

- `data/senas.csv`: dataset de landmarks capturados.
- `models/modelo_lsc.pkl`: modelo entrenado.

## Vocabulario inicial sugerido

Para una primera version, capture pocas senas LSC y con muchas muestras por etiqueta:

- `hola`
- `gracias`
- `si`
- `no`
- `ayuda`
- `profesor`
- `estudiante`
- `buenos_dias`
- `permiso`
- `por_favor`

## Datasets LSC sugeridos

Si desea acelerar el proyecto con datos externos, use solamente datasets de Lengua de
Senas Colombiana:

- LSC50: Colombian Sign Language Video and Inertial Measurement dataset.
- LSC70: Dynamic Colombian Sign Language dataset for basic conversation.
- LSC-54: Landmark-Based Dataset for Colombian Sign Language.

## Recomendaciones

- Capture al menos 30 a 100 muestras por sena.
- Use buena iluminacion y un fondo sencillo.
- Mantenga la misma distancia a la camara durante captura y prediccion.
- Comience con pocas senas LSC, por ejemplo: hola, gracias, si, no, ayuda.
