# Memoria del proyecto

Este archivo sirve para retomar el trabajo en futuras sesiones. Cuando vuelvas, puedes decir: "lee HANDOFF.md y seguimos".

## Proyecto

Traductor LSC con IA.

## Estado conocido

- Repositorio local: `traductor_lsc_ia`.
- App principal visible: `app.py`.
- Documentacion visible: `README.md`.
- Dependencias visibles: `requirements.txt`.
- Carpetas relevantes: `src/`, `data/`, `models/`, `audio_cache/`.

## Ultimo acuerdo

- Crear una memoria persistente del trabajo dentro del proyecto.
- Usar este archivo como punto de partida para recordar decisiones, avances y pendientes.
- Convertir el vocabulario en una base organizada por categorias para soportar oraciones y parrafos.

## Sesion 2026-05-03

### Hecho
- Se agrego SQLite como base local en `data/traductor_lsc.db`.
- Se creo el esquema en `src/database/schema.sql`.
- Se creo el inicializador en `src/database/seed.py`.
- Se agrego traduccion de texto por frases, palabras, sinonimos y deletreo en `src/services/traductor_texto.py`.
- Se agrego una nueva pantalla de Streamlit: `Traducir texto a LSC`.
- Se actualizo `src/capturar_dataset.py` para pedir categoria y sinonimos antes de capturar una nueva sena.
- Se actualizo `src/capturar_dataset.py` para seleccionar senas ya capturadas y agregarles mas muestras.
- Se mejoro la captura con resolucion de camara 1280x720, indicador de calidad de mano y descarte de muestras poco visibles.
- Se agrego modo de captura por duracion: corta 12 frames, media 20 frames, larga 32 frames.
- Se agrego cuenta regresiva de 3 segundos antes de grabar muestra.
- Se agrego seleccion de manos requeridas por captura: 1 o 2 manos.
- Se actualizo `src/entrenar_modelo.py` para comparar `RandomForest`, `ExtraTrees` e `HistGradientBoosting` y guardar el mejor.
- Con el dataset actual gano `ExtraTrees` con precision aproximada de 99.55%.
- Se creo `src/validar_camara.py` para medir precision real con camara y guardar resultados en `data/validacion_camara.csv`.
- Se agregaron puntos visibles de referencia en `src/detector_manos.py`: nariz, boca, orejas y pecho.
- Los nombres visibles de orejas se ajustaron para la vista en modo espejo; los datos internos no se invirtieron.
- Se agregaron caracteristicas explicitas de ubicacion por mano: zona mas cercana, lado del cuerpo y altura. `ENTRADA_MODELO` paso de 190 a 212 y el modo temporal de 570 a 636.
- Hay que reforzar/recapturar senas importantes y volver a entrenar para aprovechar las nuevas caracteristicas.
- La ubicacion lateral de la mano se ajusto a la vista espejo/persona: mano visible a la derecha se etiqueta como `derecha`.
- La ubicacion de mano ahora usa la punta del dedo indice como punto principal, para que senas de apuntar no queden clasificadas por la posicion de la palma.
- La zona mas cercana del dedo indice se calcula en 2D (`x`, `y`) para evitar errores por profundidad `z`.
- Se aumento la ventana temporal de captura/prediccion de 12 a 20 frames para senas mas largas.
- Se mejoro `src/predecir_sena.py` para pedir camara 1280x720, mostrar calidad de mano y pausar prediccion si la mano se ve mal.
- Se agrego `REQUISITOS_SENAS` en `src/config.py`; `saludos` requiere 2 manos visibles durante al menos 14 frames.
- Se agregaron categorias a las senas ya capturadas/entrenadas: `hola`, `saludos`, `ayuda`, `sordo`, `yo`, `tu`, `bien`, `mal`, `sin_sena`, `reposo`, `ninguna`.

### Decisiones
- Las categorias organizan el vocabulario, pero el usuario puede escribir oraciones mezclando categorias.
- El traductor busca primero frases completas, luego palabras individuales y finalmente deletrea palabras desconocidas.
- Los videos o imagenes de senas se guardaran como rutas en SQLite, no como archivos dentro de la base.
- El modelo sigue entrenando con etiquetas limpias; la categoria y los sinonimos viven en SQLite.
- Para mejorar una sena existente, se agregan mas filas con la misma etiqueta en `data/senas.csv` y luego se vuelve a entrenar el modelo.
- La captura exige varios frames con mano visible para evitar entrenar con muestras malas.
- Los sinonimos son para texto/voz transcrita. Si una palabra tiene una sena distinta, se captura como nueva etiqueta.
- Las etiquetas de control `sin_sena`, `reposo` y `ninguna` quedan en categoria `control` y no deben convertirse en voz.
- Regla de repeticion: si una misma sena aparece dos veces con pausa/transicion entre ambas, la segunda usa su primer sinonimo. Caso inicial: `yo` + `yo` -> `yo soy`.
- `hola` y `saludos` son senas diferentes. `saludo` queda como sinonimo de `saludos`, no de `hola`.

### Pendiente
- Conectar cada sena/frase con videos o imagenes reales en `data/videos/`.
- Crear herramientas para agregar nuevas palabras, categorias y sinonimos desde la interfaz.
- Integrar la base de datos con las etiquetas usadas al capturar y entrenar el modelo.
- Proxima sesion: reforzar muestras de `tu`, `yo` y `sordo`, luego reentrenar y volver a validar.

### Validacion real de camara
- Archivo de resultados: `data/validacion_camara.csv`.
- `hola`: fuerte, 88/88 predicciones correctas, confianza promedio aproximada 89.85%.
- `sordo`: bueno, pero se confundio con `hola` 11 veces; confianza promedio aproximada 73.67%.
- `yo`: acierta, pero confianza baja, aproximada 44.87%; se confundio con `sordo` 2 veces.
- `tu`: acierta como prediccion final, pero esta debil; se confundio con `saludos`, `sordo`, `yo`, `bien` y `mal`; confianza promedio aproximada 45.69%.
- Prioridad de refuerzo: `tu` primero, despues `yo`, despues `sordo`.
- Tambien conviene reforzar `reposo`, `sin_sena` y `ninguna` para reducir activaciones falsas.

## Pendientes

- Revisar `README.md` y `app.py` para reconstruir el estado funcional actual.
- Registrar aqui las decisiones tecnicas importantes.
- Actualizar esta memoria al terminar cada bloque de trabajo.
- Probar la app completa con Streamlit despues de los cambios de base de datos.

## Sesion 2026-05-04

### Hecho
- Se intento mejorar la interfaz de Streamlit con modo cliente/desarrollador y camara embebida.
- El usuario pidio volver al estado anterior del dia porque la camara embebida no funcionaba bien.
- Se revirtieron los cambios de interfaz/camara embebida en `app.py`, `src/detector_manos.py` y `src/voz.py`.
- Se elimino `src/services/voz_a_texto.py`, creado durante el intento de mejora de voz a texto.
- La prediccion estable vuelve a ser la de `src/predecir_sena.py` con ventana local de OpenCV.
- Se quito el sinonimo de la sena `sordo` en `data/traductor_lsc.db`.
- Se actualizo `src/database/seed.py` para que `sordo` quede sin sinonimos y no se vuelva a insertar `persona sorda`.

### Decisiones
- No volver a tocar la prediccion estable sin separar primero la logica en un modulo reutilizable.
- La interfaz grafica puede trabajarse, pero primero hay que proteger el flujo que ya predice bien con OpenCV.
- Para llevar la camara al navegador conviene evaluar una solucion especifica para video en tiempo real, como `streamlit-webrtc`, en vez de improvisar con refrescos de `st.image`.
- La base de datos conserva `sordo` como sena, pero sin sinonimos.

### Pendiente
- Si se retoma UI/UX, planear primero la arquitectura: motor de prediccion reutilizable + frontend.
- Probar que `src/predecir_sena.py` sigue abriendo camara y prediciendo correctamente.
- Mantener `sordo` sin sinonimos salvo que el usuario indique lo contrario.

## Comandos utiles

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

## Sesion 2026-05-07

### Hecho
- Se agrego en `src/predecir_sena.py` un bloqueo para no repetir la misma sena mientras la persona mantiene la misma postura.
- La misma sena solo se acepta otra vez cuando primero aparece `sin_sena`, baja la mano/calidad, se limpia el parrafo, o se detecta otra sena.
- Se incorporo una primera version de comunicacion bidireccional voz/texto a LSC en `app.py`.
- Se creo `src/services/avatar_lsc.py` para construir una secuencia visual: usa `ruta_video` o `ruta_imagen` desde SQLite si existen, y si no muestra un avatar basico como marcador inicial.
- Se agrego la opcion `Traducir voz a LSC` en Streamlit: graba audio, transcribe con SpeechRecognition, traduce a secuencia LSC y muestra el avatar/recurso visual.
- Se reemplazaron las opciones separadas `Traducir texto a LSC`, `Traducir voz a LSC` y `Voz a texto` por una sola pagina `Traducir voz/texto a LSC`.
- La nueva pagina permite grabar voz, convertirla a texto, corregir/escribir texto en el mismo campo y luego traducirlo a LSC sin cambiar de pantalla.
- Se creo `src/services/transcriptor_voz.py` con motores `Automatico`, `Vosk local` y `Google online`.
- Se instalo `vosk==0.3.45` en el entorno virtual y se descargo el modelo local `models/vosk-model-small-es-0.42`.
- Se actualizo `requirements.txt` con `vosk`, `srt`, `tqdm` y `websockets`.
- Se actualizo `.gitignore` para no versionar el zip/modelo descargado de Vosk.
- Se creo `src/services/avatar_animado.py` con un avatar en canvas que anima poses por sena conocida.
- La pagina `Traducir voz/texto a LSC` ahora muestra un avatar en vivo con reconocimiento del navegador y reproduce la secuencia animada al traducir texto/audio.
- El avatar animado tiene movimientos iniciales para `hola`, `saludos`, `yo`, `tu`, `ayuda`, `sordo`, `bien` y `mal`; las palabras desconocidas se muestran por deletreo.
- Se creo `src/services/recursos_lsc.py` para cargar/listar videos o imagenes validadas y enlazarlas con `senas.ruta_video`, `senas.ruta_imagen` o `frases.ruta_video`.
- Se agrego en la pagina `Traducir voz/texto a LSC` un panel `Cargar videos reales de LSC` para asociar recursos precisos a cada palabra/frase.
- Se actualizo el reproductor del avatar para preferir videos/imagenes reales embebibles; si no existen, vuelve a la animacion aproximada.
- Se creo `src/capturar_video_lsc.py` para grabar clips desde camara y enlazarlos automaticamente a la base de datos.

### Decisiones
- La pausa de voz de 1.5 segundos sigue sirviendo para reproducir lo detectado, pero no debe volver a crear `yo, yo, yo` si la mano sigue quieta en la misma sena.
- El avatar inicia como representacion basica y se puede ir reemplazando por videos, imagenes o animaciones reales vinculadas en SQLite.
- Para voz a texto se prioriza Vosk local cuando este configurado, porque no depende de internet ni de Google.
- Las animaciones actuales del avatar son aproximaciones programadas para demostrar el flujo en tiempo real; para precision LSC real se deben capturar o modelar movimientos validados por cada sena.
- La precision LSC se construira por recursos reales validados primero: `palabra/frase -> video corto validado`. El avatar programado queda como respaldo hasta que exista recurso real.
- Tambien se puede usar el dataset propio capturado para alimentar el avatar: `data/senas.csv` contiene landmarks de manos y referencias corporales como orejas, boca, nariz/rostro y pecho.
- Para animar desde el dataset se necesita conservar o reconstruir la secuencia temporal por muestra: `frame 1 -> puntos`, `frame 2 -> puntos`, etc. Con eso se pueden generar plantillas tipo `data/avatar_movimientos/hola.json`.
- La ruta futura para avatar preciso queda: `dataset de senas -> plantilla temporal normalizada por cuerpo -> movimiento del avatar`; los videos validados siguen siendo la referencia visual para comparar y validar.

## Sesion 2026-05-12

### Hecho
- Se reviso la estructura completa del proyecto y el estado actual del codigo.
- Se identificaron todos los datasets en `data/` y se determino cuales se usan realmente.

### Decisiones
- El dataset activo es `data/senas.csv`. Todo lo que captura `capturar_dataset.py` va ahi.
- `data/señas.csv` (con tilde) es legacy, solo funciona como fallback de emergencia si `senas.csv` no existe.
- `data/senas_antes_lsc54.csv` es un backup manual, ningun script lo referencia.
- `data/lsc54_convertido.csv` es la salida de `importar_lsc54.py` pero el entrenador nunca lo lee; no aporta al modelo actual.
- `data/lsc54_util.csv` tampoco esta referenciado en ningun script.
- `data/validacion_camara.csv` es solo un log de resultados, no es dataset de entrenamiento.
- No existe ningun dataset publico directamente compatible con `senas.csv`. El formato es muy especifico: 212 caracteristicas que incluyen contexto corporal (zona, lado, altura, referencias nariz/boca/orejas/pecho) + secuencia temporal de 20 frames generada por la combinacion exacta de `detector_manos.py` + `extraer_caracteristicas_temporales()`. Para usar datos de LSC54/LSC50/LSC70 habria que procesar sus videos con el pipeline propio.
- El dataset propio es personalizado, no completo: muy preciso para quien lo capturo, pero poco generalizable (una sola persona, una sola camara). Datasets publicos tienen mas vocabulario y mas personas pero son incompatibles en formato.

### Pendiente
- Reforzar muestras de `tu`, `yo` y `sordo` y reentrenar (prioridad alta).
- Evaluar si vale la pena procesar videos de LSC54 con el pipeline propio para sumar muestras.

## Sesion 2026-05-15

### Decisiones
- Para capturar muestras de distintas personas no se migrara a app movil.
- Se usara el celular como camara IP via WiFi (DroidCam o IP Webcam) conectado al portatil.
- Los dos integrantes del proyecto estaran presentes controlando la calidad de cada captura.
- El pipeline actual (212 features, 20 frames, calidad de mano, cuenta regresiva) queda intacto.
- El unico cambio necesario sera configurar la URL de la camara IP en `src/capturar_dataset.py`.

### Pendiente
- Instalar DroidCam o IP Webcam en el celular.
- Ajustar la URL de camara en `src/capturar_dataset.py` para aceptar camara IP ademas de la local.
- Probar la conexion en campo antes de la primera sesion de captura grupal.

### Alcance del sistema y plan de 3 meses
- El sistema es un traductor LSC bidireccional en tiempo real para aula fija.
- Flujo 1: no oyente hace senas frente a camara → texto → voz para oyente.
- Flujo 2: oyente habla por microfono → texto → avatar LSC para no oyente.
- El proyecto es academico con 3 meses de plazo (desde 2026-05-15).
- Decision: enfocarse en que todo funcione bien en PC. No se implementa version movil ni multi-dispositivo en esta entrega; se documenta como trabajo futuro.
- Plan:
  - Mes 1: reforzar muestras de `tu`, `yo`, `sordo`, ampliar vocabulario, reentrenar modelo.
  - Mes 2: pulir flujo bidireccional completo en PC (estable y fluido).
  - Mes 3: pruebas con usuarios reales, ajustes finales y documentacion de entrega.

## Arquitectura objetivo del software (decidida 2026-05-15)

### Vision
Software descargable como WhatsApp: se instala una vez, se actualiza automaticamente sin reinstalar.
Cualquier colegio o institucion puede descargarlo y usarlo en sus salones.

### Arquitectura
```
SERVIDOR CENTRAL (nube, ~$6/mes VPS)
├── API Flask/FastAPI
├── MariaDB (vocabulario, contenido pedagogico, versiones del modelo)
└── Modelo entrenado (descargable por el cliente)
         │ Internet
         ↓
SOFTWARE INSTALADO EN EL PC DEL AULA (.exe via PyInstaller)
├── Camara + MediaPipe (corre 100% local)
├── Descarga modelo actualizado del servidor
├── Consulta vocabulario del servidor
└── Interfaz HTML/CSS/JS via Flask local
```

### Lo que se actualiza automaticamente (sin reinstalar)
- Modelo entrenado (nuevas senas)
- Vocabulario LSC en base de datos
- Contenido pedagogico

### Lo que requiere nueva descarga
- Cambios grandes de interfaz
- Nuevas funcionalidades mayores

### Pantallas del software
1. Inicio — accesos rapidos a funciones principales
2. Predecir seña — deteccion en tiempo real (camara local)
3. Voz/texto a LSC — avatar animado con microfono
4. Aprender LSC — contenido pedagogico basico
5. Acerca del proyecto

### Funciones admin (ocultas al usuario final)
- Capturar dataset
- Entrenar modelo
- Ver dataset
- Gestionar vocabulario

### Base de datos
- Servidor: MariaDB (central, en la nube)
- Cliente local: cache SQLite para funcionar sin internet

### Stack tecnologico
- Backend servidor: Flask o FastAPI + MariaDB
- Backend cliente: Flask local (servidor embebido en el .exe)
- Frontend: HTML + CSS + JS (responsive, disenado para ninos/jovenes)
- Empaquetado: PyInstaller (.exe instalable)
- ML: modelo actual intacto (sklearn ExtraTrees)
- Camara: OpenCV + MediaPipe (local)

### Plan de construccion por fases
- Fase 1: Redisenar interfaz con Flask + HTML/CSS/JS (reemplaza Streamlit)
- Fase 2: Migrar base de datos a MariaDB con SQLAlchemy
- Fase 3: Montar servidor central con API REST
- Fase 4: Implementar auto-update del modelo y vocabulario
- Fase 5: Empaquetar con PyInstaller como .exe instalable

## Plantilla para actualizar

```md
## Sesion YYYY-MM-DD

### Hecho
- 

### Decisiones
- 

### Pendiente
- 

### Problemas conocidos
- 
```
