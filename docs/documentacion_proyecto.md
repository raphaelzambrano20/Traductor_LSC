# Traductor bidireccional de Lengua de Senas Colombiana con Inteligencia Artificial

## 1. Descripcion del proyecto

Este proyecto es un prototipo academico de traduccion bidireccional para Lengua de Senas Colombiana, LSC. Permite capturar senas mediante camara, entrenar un modelo de clasificacion, reconocer senas en tiempo real y convertirlas en texto o voz. Tambien incluye una funcion de traduccion de texto a una secuencia sugerida de senas, usando una base de datos local organizada por categorias, palabras, frases y sinonimos.

El sistema esta pensado exclusivamente para Lengua de Senas Colombiana. No se recomienda entrenarlo directamente con ASL u otras lenguas de senas, porque cada lengua tiene vocabulario, gramatica, expresiones y movimientos propios.

## 2. Objetivo general

Desarrollar un prototipo de software basado en vision por computador e inteligencia artificial que apoye la comunicacion entre personas usuarias de Lengua de Senas Colombiana y personas oyentes, mediante reconocimiento de senas, traduccion a texto/voz y traduccion de texto a secuencias de senas.

## 3. Objetivos especificos

- Capturar muestras de senas LSC mediante camara web.
- Extraer caracteristicas de manos, rostro y referencias corporales usando MediaPipe Holistic.
- Entrenar modelos de machine learning para clasificar senas.
- Comparar varios clasificadores y guardar automaticamente el mejor modelo.
- Reconocer senas en tiempo real con OpenCV.
- Convertir las senas reconocidas en texto acumulado y voz.
- Organizar vocabulario, categorias, frases y sinonimos en una base de datos SQLite.
- Traducir texto escrito a una secuencia de senas conocidas o deletreo.

## 4. Alcance del proyecto

El proyecto funciona como un prototipo local. Su flujo principal permite:

- Registrar nuevas senas.
- Agregar mas muestras a senas existentes.
- Entrenar un modelo con el dataset capturado.
- Validar el modelo con camara.
- Ejecutar prediccion en tiempo real.
- Convertir texto a voz.
- Transcribir voz a texto desde la interfaz.
- Traducir texto escrito a una secuencia de senas.

Actualmente, la prediccion estable se ejecuta en una ventana local de OpenCV. La camara todavia no esta integrada de forma estable dentro del navegador.

## 5. Tecnologias utilizadas

- Python: lenguaje principal del proyecto.
- OpenCV: captura, procesamiento y visualizacion de video.
- MediaPipe Holistic: deteccion de manos, rostro y pose corporal.
- Scikit-learn: entrenamiento y evaluacion de modelos de clasificacion.
- Pandas: manejo y resumen del dataset.
- NumPy: operaciones numericas.
- Joblib: guardado y carga del modelo entrenado.
- Streamlit: interfaz grafica principal del prototipo.
- SQLite: base de datos local para vocabulario.
- gTTS: generacion de audio desde texto.
- pyttsx3 / Windows SAPI: reproduccion de voz local.
- SpeechRecognition: transcripcion de voz a texto.

## 6. Estructura del proyecto

```text
traductor_lsc_ia/
├─ app.py
├─ README.md
├─ HANDOFF.md
├─ requirements.txt
├─ data/
│  ├─ senas.csv
│  ├─ traductor_lsc.db
│  └─ validacion_camara.csv
├─ models/
│  └─ modelo_lsc.pkl
├─ audio_cache/
└─ src/
   ├─ capturar_dataset.py
   ├─ entrenar_modelo.py
   ├─ predecir_sena.py
   ├─ validar_camara.py
   ├─ ver_dataset.py
   ├─ borrar_sena.py
   ├─ detector_manos.py
   ├─ caracteristicas_temporales.py
   ├─ config.py
   ├─ voz.py
   ├─ preparar_audios.py
   ├─ probar_voz.py
   ├─ importar_lsc54.py
   ├─ database/
   │  ├─ schema.sql
   │  ├─ seed.py
   │  ├─ connection.py
   │  └─ registro_vocabulario.py
   └─ services/
      ├─ traductor_texto.py
      └─ normalizacion.py
```

## 7. Modulos principales

### 7.1 app.py

Es la interfaz principal del prototipo usando Streamlit. Permite ver el estado del dataset, acceder a comandos de captura, entrenamiento y prediccion, traducir texto a LSC, generar voz desde texto y probar transcripcion de voz a texto.

### 7.2 src/capturar_dataset.py

Modulo encargado de capturar muestras de senas usando la camara. Permite seleccionar una sena existente o registrar una nueva. Antes de capturar pregunta:

- Nombre de la sena.
- Categoria.
- Sinonimos opcionales.
- Cantidad de muestras.
- Tipo de sena: corta, media o larga.
- Cantidad de manos requeridas: una o dos.

La captura usa una cuenta regresiva de 3 segundos antes de grabar. Tambien valida la calidad de la mano, la cantidad de manos visibles y la cantidad minima de frames validos antes de guardar una muestra.

### 7.3 src/entrenar_modelo.py

Modulo encargado de entrenar el modelo de reconocimiento de senas. Lee el dataset, separa etiquetas y caracteristicas, entrena varios clasificadores y guarda automaticamente el mejor.

Modelos evaluados:

- RandomForestClassifier.
- ExtraTreesClassifier.
- HistGradientBoostingClassifier.

El modelo final se guarda en:

```text
models/modelo_lsc.pkl
```

### 7.4 src/predecir_sena.py

Modulo encargado de la prediccion en tiempo real. Abre una ventana local con OpenCV, detecta landmarks con MediaPipe, prepara la entrada para el modelo y predice la sena.

Funciones principales:

- Cargar el modelo entrenado.
- Preparar caracteristicas segun el numero de entradas del modelo.
- Validar requisitos especiales de algunas senas.
- Evitar repetir palabras de forma innecesaria.
- Acumular palabras en un parrafo.
- Reproducir voz cuando pasan unos segundos sin movimiento de manos.

### 7.5 src/detector_manos.py

Modulo que encapsula la deteccion usando MediaPipe Holistic. Obtiene landmarks de manos, rostro y cuerpo. Tambien dibuja referencias visibles como nariz, boca, orejas y pecho, y calcula ubicaciones relativas de la mano.

### 7.6 src/caracteristicas_temporales.py

Modulo que transforma una secuencia de frames en caracteristicas temporales. Esto permite que el modelo aprenda movimiento, desplazamiento y cambios en la postura de la mano.

### 7.7 src/database/schema.sql

Archivo que define la estructura de la base de datos SQLite. Contiene tablas para categorias, senas, frases y sinonimos.

### 7.8 src/services/traductor_texto.py

Modulo encargado de traducir texto escrito a una secuencia sugerida de senas. Busca primero frases completas, luego palabras individuales y finalmente marca palabras desconocidas para deletreo.

### 7.9 src/validar_camara.py

Modulo usado para validar la precision real del modelo con camara. El usuario indica la sena esperada, el sistema predice durante unos segundos y guarda resultados en:

```text
data/validacion_camara.csv
```

## 8. Flujo general del sistema

1. El usuario captura muestras de una sena.
2. El sistema detecta landmarks de manos, rostro y cuerpo.
3. Se guardan las caracteristicas en `data/senas.csv`.
4. El usuario entrena el modelo.
5. El sistema compara varios clasificadores.
6. Se guarda el mejor modelo en `models/modelo_lsc.pkl`.
7. En prediccion, la camara detecta una nueva sena.
8. El modelo clasifica la sena.
9. La sena se agrega al parrafo si cumple estabilidad, confianza y requisitos.
10. Tras una pausa sin movimiento, el texto acumulado se reproduce como voz.

## 9. Extraccion de caracteristicas

El sistema no entrena directamente con imagenes completas. En cambio, usa puntos clave o landmarks extraidos por MediaPipe. Esto reduce el tamano de los datos y permite entrenar modelos de machine learning tradicionales.

Caracteristicas consideradas:

- 21 puntos por mano.
- Coordenadas `x`, `y`, `z`.
- Hasta 2 manos.
- Referencias del cuerpo y rostro: nariz, boca, orejas y pecho.
- Zona corporal mas cercana a la mano.
- Lado del cuerpo: izquierda, centro o derecha.
- Altura relativa: arriba, medio o abajo.
- Secuencia temporal de frames para representar movimiento.

Valores importantes definidos en `src/config.py`:

```text
FRAMES_SECUENCIA = 20
ENTRADA_MODELO = 212
ENTRADA_MODELO_TEMPORAL = 636
MIN_FRAMES_MANO_CAPTURA = 14
```

## 10. Base de datos de vocabulario

La base de datos local esta ubicada en:

```text
data/traductor_lsc.db
```

La estructura principal incluye:

- `categorias`: organiza el vocabulario por grupos.
- `senas`: palabras individuales con categoria.
- `frases`: expresiones completas.
- `sinonimos`: variantes asociadas a senas o frases.

Ejemplos de categorias:

- cordialidad.
- colores.
- numeros.
- alfabeto.
- familia.
- acciones.
- objetos.
- control.

Las etiquetas de control son:

```text
sin_sena
reposo
ninguna
no_sena
transicion
```

Estas etiquetas sirven para que el modelo aprenda cuando no debe agregar texto ni activar voz.

## 11. Traduccion de texto a LSC

La traduccion de texto escrito funciona mediante un catalogo cargado desde SQLite.

Proceso:

1. Se normaliza el texto.
2. Se divide el texto en palabras.
3. Se buscan frases completas de hasta 5 palabras.
4. Si no se encuentra una frase, se buscan palabras individuales.
5. Si una palabra no existe, se marca para deletreo.
6. Se devuelve una secuencia sugerida de senas.

Ejemplo:

```text
Entrada:
hola mama quiero agua azul por favor

Salida:
hola | mama | quiero | agua | azul | por favor
```

Si una palabra no existe en la base:

```text
Entrada:
computador

Salida:
c-o-m-p-u-t-a-d-o-r
```

## 12. Entrenamiento del modelo

El entrenamiento usa el archivo:

```text
data/senas.csv
```

El flujo de entrenamiento es:

1. Cargar el dataset.
2. Separar etiquetas y caracteristicas.
3. Dividir los datos en entrenamiento y prueba si hay suficientes muestras.
4. Entrenar varios modelos candidatos.
5. Calcular la precision de cada modelo.
6. Seleccionar el mejor.
7. Guardar el artefacto entrenado.

El artefacto guardado contiene:

- Modelo entrenado.
- Nombre del modelo seleccionado.
- Precision obtenida.
- Resultados de los modelos evaluados.
- Numero de caracteristicas.
- Tipo de caracteristicas.

Segun el estado conocido del proyecto, con el dataset actual gano:

```text
ExtraTrees
Precision aproximada: 99.55%
```

## 13. Prediccion en tiempo real

La prediccion en tiempo real se ejecuta con:

```powershell
python src/predecir_sena.py
```

Durante la prediccion:

- Se abre una ventana local de camara.
- La vista se muestra en modo espejo.
- Se detectan landmarks de manos, rostro y cuerpo.
- Se predice la sena con el modelo entrenado.
- Se muestra la confianza si el modelo la permite.
- Se acumulan palabras en un parrafo.
- Se evita repetir la misma palabra seguida sin pausa.
- Se reproduce voz tras una pausa sin movimiento de manos.

Teclas disponibles:

- `Q`: salir.
- `C`: limpiar el parrafo acumulado.
- `V`: hablar manualmente el parrafo acumulado.

## 14. Reglas de voz y repeticion

La voz se reproduce cuando pasan aproximadamente 1.5 o 2 segundos sin detectar movimiento de manos despues de una o varias senas.

El sistema evita repetir la misma palabra de forma seguida. Por ejemplo:

```text
hola hola
```

No se agrega dos veces si no hay pausa o transicion clara.

Tambien existe una regla de repeticion con sinonimos. Si una misma sena aparece dos veces con pausa entre ambas, la segunda puede usar su primer sinonimo. Caso inicial:

```text
yo + yo -> yo soy
```

Las etiquetas de control no se convierten en voz:

```text
sin_sena
reposo
ninguna
no_sena
transicion
```

## 15. Validacion real con camara

La validacion real se ejecuta con:

```powershell
python src/validar_camara.py
```

El resultado se guarda en:

```text
data/validacion_camara.csv
```

Resultados conocidos:

- `hola`: fuerte, 88/88 predicciones correctas, confianza promedio aproximada 89.85%.
- `sordo`: bueno, pero se confundio con `hola` 11 veces; confianza promedio aproximada 73.67%.
- `yo`: acierta, pero confianza baja, aproximada 44.87%; se confundio con `sordo` 2 veces.
- `tu`: acierta como prediccion final, pero esta debil; se confundio con `saludos`, `sordo`, `yo`, `bien` y `mal`; confianza promedio aproximada 45.69%.

Prioridad de refuerzo:

1. `tu`.
2. `yo`.
3. `sordo`.
4. `reposo`, `sin_sena` y `ninguna`.

## 16. Comandos de uso

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Ejecutar la app:

```powershell
python -m streamlit run app.py
```

Capturar dataset:

```powershell
python src/capturar_dataset.py
```

Entrenar modelo:

```powershell
python src/entrenar_modelo.py
```

Predecir sena en tiempo real:

```powershell
python src/predecir_sena.py
```

Ver dataset:

```powershell
python src/ver_dataset.py
```

Validar con camara:

```powershell
python src/validar_camara.py
```

Inicializar base de datos:

```powershell
python src/database/seed.py
```

Preparar audios:

```powershell
python src/preparar_audios.py
```

Borrar una sena:

```powershell
python src/borrar_sena.py nombre_de_la_sena
```

## 17. Recomendaciones para capturar buenas muestras

- Usar buena iluminacion.
- Usar un fondo sencillo.
- Mantener rostro y hombros visibles.
- Mantener la misma distancia a la camara.
- Capturar entre 30 y 100 muestras por sena.
- Capturar tambien muestras de `reposo` o `sin_sena`.
- Para senas con movimiento, hacer el gesto completo despues de presionar `R`.
- Usar etiquetas limpias como `hola`, `yo`, `buenos_dias` o `por_favor`.
- Reentrenar el modelo despues de agregar nuevas muestras.

## 18. Reglas importantes del proyecto

- `hola` y `saludos` son senas diferentes.
- `saludo` es sinonimo de `saludos`, no de `hola`.
- `sordo` debe mantenerse sin sinonimos.
- Los sinonimos ayudan en texto o voz transcrita, pero no son etiquetas nuevas del modelo.
- Si dos palabras tienen gestos diferentes, deben capturarse como senas diferentes.
- Para mejorar una sena existente, se agregan mas muestras con la misma etiqueta y luego se reentrena.
- La prediccion estable actual es la de OpenCV en `src/predecir_sena.py`.
- No conviene modificar la prediccion estable sin separar primero la logica en un motor reutilizable.

## 19. Limitaciones actuales

- La camara en navegador todavia no esta integrada de forma estable.
- La prediccion se ejecuta en una ventana local de OpenCV.
- El rendimiento depende mucho de la calidad del dataset.
- Algunas senas tienen baja confianza y requieren mas muestras.
- El sistema reconoce vocabulario limitado al dataset capturado.
- No interpreta todavia la gramatica completa de LSC.
- La traduccion texto a LSC genera una secuencia sugerida, no animaciones completas.
- Los videos o imagenes de senas aun estan pendientes de conectar en `data/videos/`.

## 20. Pendientes del proyecto

- Reforzar muestras de `tu`, `yo` y `sordo`.
- Reentrenar despues del refuerzo.
- Validar nuevamente con camara.
- Conectar senas y frases con videos o imagenes reales.
- Crear herramientas desde la interfaz para agregar palabras, categorias y sinonimos.
- Separar el motor de prediccion en un modulo reutilizable.
- Evaluar `streamlit-webrtc` si se quiere llevar camara en tiempo real al navegador.
- Probar la app completa despues de cambios en base de datos.

## 21. Propuesta de indice para documento final

1. Introduccion.
2. Planteamiento del problema.
3. Justificacion.
4. Objetivos.
5. Alcance y limitaciones.
6. Marco teorico.
7. Tecnologias utilizadas.
8. Arquitectura del sistema.
9. Estructura del proyecto.
10. Base de datos de vocabulario.
11. Captura del dataset.
12. Extraccion de caracteristicas.
13. Entrenamiento del modelo.
14. Prediccion en tiempo real.
15. Traduccion texto a LSC.
16. Validacion y resultados.
17. Manual de instalacion.
18. Manual de usuario.
19. Problemas conocidos.
20. Trabajo futuro.
21. Conclusiones.
22. Anexos.

## 22. Conclusion sugerida

El proyecto demuestra la viabilidad de construir un prototipo local para reconocimiento de Lengua de Senas Colombiana usando vision por computador e inteligencia artificial. Aunque el sistema aun requiere fortalecer el dataset, ampliar vocabulario y mejorar la integracion de camara en interfaz web, ya cuenta con un flujo funcional de captura, entrenamiento, prediccion, traduccion a texto/voz y organizacion de vocabulario mediante una base de datos local.

Este avance permite continuar el desarrollo hacia una herramienta mas completa, accesible y orientada al apoyo comunicativo entre personas sordas usuarias de LSC y personas oyentes.
