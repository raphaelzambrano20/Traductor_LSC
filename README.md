# Traductor LSC con IA

Prototipo academico de traduccion bidireccional para Lengua de Senas Colombiana (LSC).
Incluye captura de dataset con camara, entrenamiento de un clasificador y prediccion en
tiempo real usando MediaPipe Holistic, OpenCV y Scikit-learn.

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

Digite el nombre de la sena, indique la cantidad de muestras, prepare la mano y presione
`R` justo antes de hacer el movimiento. Mantenga visibles rostro y hombros: cada muestra
guarda manos, referencias de cara/cuerpo y una secuencia corta para que el modelo aprenda
ubicacion, postura, desplazamiento y velocidad. Presione `Q` para salir.

Antes de abrir la camara, el capturador tambien pregunta la categoria y sinonimos
opcionales. La categoria se guarda en SQLite para organizar el vocabulario, pero el modelo
entrena con una etiqueta limpia como `hola`, `rojo` o `buenos_dias`.

Si la sena ya existe en el dataset, el capturador permite seleccionarla por numero y
agregar mas muestras a las que ya tenia. Por ejemplo, si `yo` tiene 100 muestras, puede
seleccionarla y sumar 50 mas para entrenar luego con 150 muestras.
Tambien permite escoger el tipo de sena antes de capturar:

- corta: 12 frames.
- media: 20 frames.
- larga: 32 frames.

Antes de grabar, el capturador hace una cuenta regresiva de 3 segundos. Tambien pregunta
si la sena requiere 1 o 2 manos; si requiere 2, descarta muestras donde no aparezcan ambas
manos durante suficiente tiempo.

La captura intenta usar la camara en 1280x720 y muestra un indicador de calidad de mano.
Si la mano esta muy lejos, fuera de cuadro o con poca luz, la muestra se descarta para no
ensuciar el entrenamiento.
Cada muestra captura una secuencia segun el tipo elegido. Esto da mas tiempo para senas
largas sin cambiar el tamano final de las caracteristicas usadas por el modelo.
La vista de camara dibuja referencias visibles de nariz, boca, orejas y pecho para revisar
si las senas cerca de cara o torso se estan capturando en la posicion correcta. Los nombres
visibles de las orejas estan ajustados para la vista en modo espejo.
Tambien muestra una descripcion de ubicacion por mano, por ejemplo `oreja der | derecha |
arriba` o `pecho | centro | medio`. Esas senales se guardan como caracteristicas para que
el modelo distinga mejor senas cerca de cara, orejas, pecho, izquierda o derecha.
Para calcular esa ubicacion se usa la punta del dedo indice, no el centro de la palma,
porque muchas senas apuntan a nariz, boca, oreja o pecho.
La zona mas cercana se decide por distancia visual en pantalla (`x`, `y`), para que la
profundidad estimada (`z`) no haga que un dedo cerca de la cara se marque como pecho.

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

La voz se reproduce cuando pasan 2 segundos sin detectar movimiento de manos despues de
una o varias senas. El sistema acumula un parrafo y evita repetir la misma palabra de
forma seguida; por ejemplo, `hola gracias hola` se permite, pero `hola hola` no se agrega
dos veces seguidas. Cuando la voz reproduce el texto, el parrafo se limpia en pantalla.
Presione
`V` para hablar el parrafo completo, `C` para limpiar el parrafo acumulado y `Q` para
cerrar la ventana de camara.
Si el modelo predice `sin_sena`, `reposo`, `ninguna`, `no_sena` o `transicion`, no agrega
texto al parrafo.
La vista de camara se muestra en modo espejo, de modo que la mano derecha aparece a la
derecha en pantalla.
La prediccion tambien intenta usar la camara en 1280x720 y muestra la calidad de mano. Si
la mano se ve muy pequena, borrosa o con poca luz, la prediccion se pausa hasta que mejore
la visibilidad.
Algunas senas pueden tener requisitos propios. Por ahora `saludos` exige 2 manos visibles
durante la secuencia para evitar que se active al levantar solo una mano.

## Archivos generados

- `data/senas.csv`: dataset de landmarks capturados.
- `models/modelo_lsc.pkl`: modelo entrenado.
- `data/traductor_lsc.db`: base de datos SQLite con categorias, senas, frases y sinonimos.

## Base de datos de vocabulario

El proyecto usa SQLite para organizar el vocabulario por categorias y evitar que el
traductor busque todas las palabras sin contexto.

Inicializar o actualizar la base:

```powershell
venv\Scripts\python.exe src\database\seed.py
```

La estructura principal es:

- `categorias`: cordialidad, colores, numeros, alfabeto, familia, acciones, objetos, etc.
- `senas`: palabras individuales con su categoria.
- `frases`: expresiones completas como `buenos dias` o `como estas`.
- `sinonimos`: variantes como `roja -> rojo`, `mamá -> mama` o `por_favor -> por favor`.

Cuando se traduce una oracion, el sistema busca primero frases completas, despues palabras
individuales y, si no encuentra una palabra, la marca para deletrearla con el alfabeto LSC.

Los sinonimos ayudan a entender texto escrito o voz transcrita. No son etiquetas nuevas del
modelo. Si dos palabras tienen gestos diferentes, deben capturarse como senas diferentes.
En LSC a voz, si la misma sena se detecta dos veces con una pausa entre ambas, la segunda
puede convertirse en su primer sinonimo; por ejemplo, `yo` + `yo` se expresa como
`yo soy`.

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
- Capture tambien 30 a 100 muestras con la etiqueta `sin_sena` o `reposo`: manos quietas,
  manos entrando/saliendo del cuadro y movimientos entre una sena y otra.
- Para senas con movimiento, presione `R`, haga el gesto completo y espere a que se guarde
  automaticamente.
- Use buena iluminacion y un fondo sencillo.
- Mantenga visibles la cara y los hombros, especialmente en senas cerca de boca, orejas,
  rostro o pecho.
- Mantenga la misma distancia a la camara durante captura y prediccion.
- Comience con pocas senas LSC, por ejemplo: hola, gracias, si, no, ayuda.
- Si ya tenia un modelo entrenado solo con manos, capture nuevas muestras y vuelva a
  entrenar para aprovechar las referencias corporales.
