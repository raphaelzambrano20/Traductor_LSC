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

## Sesion 2026-05-16

### Hecho
- Se migro la interfaz completa de Streamlit a Flask + HTML/CSS/JS.
- Se creo `run_flask.py` como nuevo punto de entrada (reemplaza `app.py`). Abre el navegador automaticamente en `http://127.0.0.1:5000`.
- Se creo `src/camara_stream.py`: clase `CamaraStream` que lee frames en hilo de fondo, elimina el retraso acumulado en camaras IP. Usa `threading.Event` para bloquear hasta recibir el primer frame.
- Se agrego soporte DroidCam en `src/capturar_dataset.py` y `src/predecir_sena.py`: funcion `elegir_camara()` que pregunta si usar camara local (0) o URL de DroidCam.
- Se creo `src/services/landmarks_avatar.py`: lee `data/senas.csv`, promedia todos los frames de una sena y devuelve puntos `[x,y]` de `mano_der` y `mano_izq`. Tiene cache en memoria y usa las mismas `HAND_CONNECTIONS` de MediaPipe.
- Se crearon todas las plantillas HTML en `templates/`: `base.html` (navbar + modal dev), `index.html`, `predecir.html`, `comunicar.html`, `aprender.html`, `acerca.html`, `dev/panel.html`, `dev/capturar.html`, `dev/entrenar.html`, `dev/dataset.html`, `dev/login_requerido.html`.
- Se creo `static/css/style.css` con variables CSS, layout de dos paneles `.rt-layout`, animacion `.btn-mic-activo`, estilos de cola de senas, avatar fallback, panel dev y tablas dataset.
- Se implemento la pagina `comunicar.html` con:
  - Panel izquierdo: microfono (Web Speech API), caja de transcripcion, cola de senas visible, campo de texto manual como fallback.
  - Panel derecho: canvas 400x420 con avatar cartoon (cabeza, cabello, camisa, corbata, brazos, manos) dibujado con Canvas 2D API.
  - Cola de signos secuencial tipo interprete humano.
  - Landmarks reales desde `GET /api/landmarks/<sena>` con transicion interpolada (easing ease-in-out, 450ms).
- Se corrigio bug de microfono: cambiado de `continuous=true` (inestable en Windows/Chrome) a `continuous=false` con patron `crearReconocimiento()` que crea un nuevo objeto por frase y se reinicia automaticamente en `onend`.
- Se corrigio bug de avatar: `mostrandoSigno` podia quedar en `true` si habia error al obtener pose. Se creo `finalizarSigno()` helper y se agrego timeout de 900ms para senas sin landmarks.
- Se agrego campo de texto manual en `comunicar.html` como fallback cuando el microfono no funciona.
- Se mejoro HUD en `predecir_sena.py`: barras semi-transparentes arriba/abajo, texto prediccion verde, calidad rojo puro cuando mala, atajo C/V/Q visibles.
- Se agrego `cv2.WINDOW_NORMAL` en `capturar_dataset.py` y `predecir_sena.py` para ventana redimensionable.
- Se agrego autenticacion de modo desarrollador con Flask session: la clave y la llave secreta se leen del archivo `.env` (ver `.env.example`). Las rutas `/dev/*` estan ocultas al usuario final.
- Se agregaron rutas API: `POST /api/traducir`, `POST /api/transcribir`, `GET /api/landmarks/<sena>`, `GET /api/landmarks`, `POST /api/dev/login`, `POST /api/dev/logout`.
- Se instalo Flask en el entorno virtual correcto (`traductor_lsc_ia - copia\venv`).

### Decisiones
- Streamlit queda abandonado. Flask + HTML/CSS/JS es la interfaz definitiva.
- El avatar usa landmarks reales del dataset propio (promedio de muestras), no poses programadas a mano.
- `continuous=false` en Web Speech API es mas estable que `continuous=true` en Windows/Chrome; se reinicia manualmente via `onend`.
- La resolucion de DroidCam no se fuerza por codigo (evita pixelado al hacer upscale); el usuario activa HD manualmente en la app.
- Las rutas de desarrollo estan protegidas por session Flask, no por middleware externo.

### Pendiente
- Probar flujo completo: microfono → transcripcion → cola → avatar muestra sena.
- Verificar que el campo de texto manual → avatar funciona correctamente.
- Reforzar muestras de `tu`, `yo`, `sordo` y reentrenar (prioridad alta, pendiente desde sesiones anteriores).
- Conectar senas con videos reales en `data/videos/`.
- Fase 2: Migrar base de datos a MariaDB con SQLAlchemy.
- Fase 3: Servidor central con API REST.
- Fase 4: Auto-update del modelo y vocabulario.
- Fase 5: Empaquetar con PyInstaller como .exe instalable.

### Problemas conocidos
- DroidCam gratuito: solo 1 hora/dia de HD. En modo SD la imagen es 640x480.
- Web Speech API requiere internet para el motor de Google; Vosk local no requiere.
- Si el microfono da error `not-allowed`, el usuario debe ir a configuracion del navegador y habilitar el permiso.

### Comando para iniciar
```powershell
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"
```

## Sesion 2026-05-16 (continuacion)

### Hecho
- Se corrigio bug de microfono en `comunicar.html`: `toggleEscucha` ahora siempre crea un objeto `SpeechRecognition` fresco al iniciar (antes reutilizaba el objeto detenido, fallaba silenciosamente).
- Se agrego barra de nivel de microfono (Web Audio API) para diagnosticar si el navegador capta audio.
- Se confirmo que Web Speech API funciona en Chrome pero no en Brave (Brave bloquea el envio de audio a Google por privacidad). Decision: usar Chrome para esta funcion.
- Se agrego mapeo fonetico de letras del abecedario en `comunicar.html`: "hache" → "h", "jota" → "j", "doble uve" → "w", etc. Solo aplica si la frase completa es el nombre de una letra (≤2 palabras).
- Se corrigio posicionamiento del avatar: `escalarPunto` ahora usa coordenadas corporales (`nariz`, `pecho`) del dataset para mapear manos relativo al cuerpo, en vez de offset fijo.
- Se actualizo `landmarks_avatar.py` para leer y retornar `nariz` y `pecho` del CSV (columnas 197-211), y usar umbral estricto de presencia de mano (≥15 de 21 landmarks no-cero).
- Se implementaron brazos dinamicos con curva bezier desde hombro hasta muneca.
- Se descarto el avatar Canvas 2D por no alcanzar calidad profesional despues de multiples iteraciones.

### Decisiones
- **Avatar 3D definitivo**: Three.js + Ready Player Me (cartoon, para ninos).
- Canvas 2D descartado permanentemente para el avatar — no volver a mejorar ese enfoque.
- Estilo del avatar: cartoon/animado (como Fortnite) porque el sistema es para ninos.
- Fuente del modelo: Ready Player Me (readyplayer.me) — gratis, sin cuenta Adobe requerida.
- El modelo se descargara como `.glb` y se servira desde `static/models/avatar.glb`.

### Pendiente (PRIORIDAD ALTA)
- Usuario debe: ir a readyplayer.me → crear avatar cartoon → descargar como `avatar.glb` → colocar en `static/models/avatar.glb`.
- Implementar `static/js/avatar3d.js`: escena Three.js, carga del modelo GLB, mapeo de 21 landmarks MediaPipe a huesos del esqueleto (rotaciones cuaternion), animacion SLERP entre poses.
- Reemplazar Canvas 2D y funciones `dibujarBrazo`/`dibujarCuerpo` en `comunicar.html` por el renderer Three.js.
- Pendientes anteriores siguen vigentes: reforzar `tu`, `yo`, `sordo`; Fase 2 MariaDB; Fases 3-5.

### Arquitectura Three.js (para retomar)
```
GET /api/landmarks/<sena>  →  {mano_der, mano_izq, nariz, pecho}
        ↓
vector entre landmarks consecutivos → cuaternion de rotacion por hueso
        ↓
Three.js aplica rotaciones al esqueleto del GLB de Ready Player Me
        ↓
WebGLRenderer en <canvas id="avatar-canvas"> (reemplaza Canvas 2D)
```

Huesos Ready Player Me (VRM-compatible):
- `RightHand`, `RightThumbProximal/Intermediate/Distal`
- `RightIndexProximal/Intermediate/Distal`
- `RightMiddleProximal/Intermediate/Distal`
- `RightRingProximal/Intermediate/Distal`
- `RightLittleProximal/Intermediate/Distal`
- (identico para Left*)

### Problemas conocidos
- Web Speech API no funciona en Brave (bloquea envio a Google). Usar Chrome.
- DroidCam gratuito: solo 1 hora/dia de HD.
- El abecedario LSC no esta en el dataset aun — el avatar mostrara texto de fallback para letras individuales hasta que se capturen.

## Sesion 2026-05-16 (continuacion 2 — Avatar 3D Three.js implementado)

### Contexto
El usuario descargo un avatar de Mixamo (personaje de futbol) como `Avatar.fbx` en T-pose y lo coloco en `static/models/Avatar.fbx`. El plan anterior era usar Ready Player Me (.glb), pero el usuario no tenia cuenta Adobe y Mixamo funciono sin registro.

### Hecho
- Se cambio la fuente del avatar de Ready Player Me (.glb) a **Mixamo (.fbx)** — mismo esqueleto, diferente formato.
- Se creo `static/js/avatar3d.js` con Three.js r160 + FBXLoader (CDN via importmap).
- Se reemplazo todo el codigo Canvas 2D en `comunicar.html` por el renderer Three.js:
  - Eliminadas: `dibujarBrazo`, `dibujarCuerpo`, `escalarPunto`, `interpolar`, `renderFrame`, `animarTransicion`.
  - Script convertido a `type="module"` con importmap para Three.js.
  - `window.toggleEscucha/traducirManual/limpiarTodo` expuestos para que los `onclick` HTML funcionen desde modulo.
  - Loading overlay sobre el canvas mientras carga el FBX.
- El avatar 3D cargo y se renderizo correctamente (modelo de futbolista en T-pose visible).
- Se identifico el bug principal: brazos en T-pose y señas sin efecto.
  - **Causa brazos**: rotacion por eje local Z (`setFromAxisAngle`) no funciona igual para todos los modelos Mixamo porque la orientacion de ejes locales varia por rigger.
  - **Causa señas**: la primera version guardaba `restWorldDir` en T-pose y usaba esa direccion como base para los dedos, pero despues de mover el brazo la direccion guardada ya no era valida → sin movimiento visible.
- Se reescribio `avatar3d.js` (v3) con el enfoque correcto:

### Enfoque tecnico final (avatar3d.js v3)

**Funcion clave: `_setBoneWorldDir(boneKey, targetWorldDir)`**
- Lee la **direccion world ACTUAL del hueso** (de hueso a primer hijo bone) en tiempo real via `getWorldPosition()`.
- Calcula delta de rotacion: `setFromUnitVectors(currentDir, targetDir)` — eje-independiente, funciona para cualquier modelo.
- Convierte delta de espacio-mundo a espacio-local del padre.
- Guarda en `S.targetQ[boneKey]`.

**Flujo en `setPose(poseData)`:**
1. Snapshot: `fromQ = currentQ`, `targetQ = restQ`.
2. Fase 1 — IK de brazos: `_armIK(side, wrist2D, nariz, pecho)` posiciona cada brazo usando ley de cosenos (dos huesos). El codo se empuja hacia afuera-atras para postura natural de señas.
3. Aplicacion temporal de brazos (`_applyNow`) + `updateMatrixWorld(true)` para que las matrices de los dedos queden correctas.
4. Fase 2 — dedos: `_poseFingers` computa la direccion de cada hueso de dedo desde landmarks consecutivos en pseudo-3D: `dx = -(pj[0]-pi[0])`, `dy = -(pj[1]-pi[1])`, `dz = 0`. Misma formula para ambas manos.
5. Restaurar bones a `currentQ` (el SLERP hace la transicion visual).
6. `slerpAlpha = 0` → inicia SLERP de 0.45s.

**Postura neutra de brazos (`_neutralArms`):**
- Usa `_setBoneWorldDir` con vectores de direccion mundo hardcodeados: rArm → `(0.35, -0.80, 0.35)`, rForeArm → `(0.10, -0.72, 0.52)` y espejeados para el lado izquierdo.
- Aplica con `_applyNow` + `updateMatrixWorld(true)` en secuencia (brazo primero, antebrazo despues para que el padre este correcto).
- Hace `_commitRest()` dos veces: despues de T-pose y despues de la postura neutra — la segunda commitada es la que sirve como punto de reposo para las transiciones.

**Conversion de 2D landmarks a 3D (`_cam3D`):**
- Referencia corporal: nariz → Y=1.55m, pecho → Y=1.22m en modelo 3D.
- Escala: `(NOSE_Y - CHEST_Y) / max(camDeltaY, 0.04)`.
- X: `-(pt[0] - nariz_x) * scale` (espejado).
- Y: `NOSE_Y - (pt[1] - nariz_y) * scale` (Y invertida).
- Z: `0.15` (manos ligeramente delante del cuerpo).

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `static/js/avatar3d.js` | Creado + reescrito (v3). 230 lineas. |
| `templates/comunicar.html` | Canvas 2D eliminado, script → modulo, importmap Three.js, loading overlay. |
| `static/models/Avatar.fbx` | Colocado por el usuario (Mixamo, modelo futbolista, T-pose). |

### Estado al cerrar sesion
- Avatar 3D renderiza. Postura neutra de brazos implementada con nuevo enfoque (pendiente verificar visualmente).
- Señas: logica implementada con `setFromUnitVectors` (pendiente probar en vivo).
- El usuario debe abrir Chrome en `http://127.0.0.1:5000/comunicar`, escribir una sena en el campo de texto y verificar si los dedos se mueven.

### Pendiente inmediato
1. **Probar señas en vivo**: escribir "hola" en el campo manual y ver si el avatar mueve brazos y dedos.
2. Si los dedos van en direccion contraria: en `avatar3d.js` funcion `_poseFingers`, cambiar `dx = -(pj[0]-pi[0])` a `dx = (pj[0]-pi[0])` (quitar el negativo).
3. Si los brazos en postura neutra aun se ven mal: ajustar los vectores de direccion en `_neutralArms()` (lineas con `0.35, -0.80, 0.35` etc.).
4. Reforzar muestras de `tu`, `yo`, `sordo` y reentrenar (pendiente desde sesiones anteriores).
5. Capturar abecedario LSC en dataset.
6. Fase 2: Migrar BD a MariaDB con SQLAlchemy.
7. Fases 3-5: servidor central, auto-update, PyInstaller.

### Nombres de huesos Mixamo (FBX)
```
mixamorig:RightArm         → rArm
mixamorig:RightForeArm     → rForeArm
mixamorig:RightHand        → rHand
mixamorig:RightHandThumb1  → rThumb1  (Thumb2, Thumb3)
mixamorig:RightHandIndex1  → rIndex1  (Index2, Index3)
mixamorig:RightHandMiddle1 → rMiddle1 (Middle2, Middle3)
mixamorig:RightHandRing1   → rRing1   (Ring2, Ring3)
mixamorig:RightHandPinky1  → rPinky1  (Pinky2, Pinky3)
(identico para Left*)
```
Patron regex usado: `/RightHandIndex1$/i` captura `mixamorig:RightHandIndex1` ✓

### MediaPipe landmarks → huesos de dedo
```
Hueso          fromLandmark  toLandmark
rThumb1        1 → 2
rThumb2        2 → 3
rThumb3        3 → 4
rIndex1        5 → 6
rIndex2        6 → 7
rIndex3        7 → 8
rMiddle1       9 → 10  (etc.)
```

### Comando para iniciar
```powershell
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"
```

## Sesion 2026-05-16 (nota rapida - fallo actual)

### Contexto visual reportado
- En la pantalla de comunicar se ve el texto **"hola"** en azul.
- El modelo 3D de futbolista carga correctamente dentro del contenedor.
- El avatar queda con los brazos completamente abiertos en T-pose.
- No se observa movimiento de brazos, manos ni dedos para la sena `hola`.

### Interpretacion actual
- El renderizado/carga del FBX si esta funcionando.
- El problema pendiente ya no parece ser de carga del modelo, sino de aplicacion de pose/animacion:
  - `static/js/avatar3d.js` puede no estar encontrando/aplicando los huesos correctos.
  - `setPose()` puede no estar recibiendo datos validos desde `main.js` o desde `/api/landmarks/<sena>`.
  - La postura neutra calculada en `_neutralArms()` no se esta aplicando visualmente, porque el avatar sigue en T-pose.
  - Tambien puede haber un error silencioso de JS en consola que detenga la animacion antes del SLERP.

### Archivos a revisar primero
- `static/js/avatar3d.js`
- `static/js/main.js`
- `templates/comunicar.html`
- `src/services/landmarks_avatar.py`
- `run_flask.py`

### Siguiente paso recomendado
1. Abrir DevTools en Chrome y revisar consola al cargar `/comunicar`.
2. Confirmar que `Avatar3D` se inicializa y que el FBX termina de cargar.
3. Agregar logs temporales en `avatar3d.js`:
   - cantidad de huesos detectados,
   - nombres reales de huesos del modelo,
   - llamadas a `setPose(poseData)`,
   - contenido/resumen de `poseData` para `hola`.
4. Probar directamente `/api/landmarks/hola` para confirmar que devuelve `mano_der`, `mano_izq`, `nariz` y `pecho`.
5. Si `setPose()` si se llama con datos, depurar `_setBoneWorldDir()` y `_neutralArms()` porque la T-pose indica que las rotaciones no estan llegando al esqueleto visible.

## Sesion 2026-05-16 (continuacion 3 — Avatar 3D depurado)

### Hecho
- Se identifico y corrigio el bug principal de T-pose: `rotateOnWorldAxis` era incorrecto para huesos anidados 5 niveles. La formula correcta es `localDelta = parentWorldQ⁻¹ · worldDelta · parentWorldQ` aplicada al quaternion local del hueso.
- Se corrigio bug de cache 304 del navegador: el servidor devolvía 304 (Not Modified) aunque el archivo habia cambiado. Solucion: bumpar el parametro `?v=` en el import de `comunicar.html`. Version actual: `?v=20260517c`.
- Se corrigio la direccion de la postura neutra de brazos: el brazo derecho en T-pose apunta en -X (no +X como se asumia). Vectores corregidos: `rArm (-0.35, -0.80, 0.35)`, `rForeArm (-0.10, -0.72, 0.52)`, `lArm (0.35, -0.80, 0.35)`, `lForeArm (0.10, -0.72, 0.52)`.
- Se agrego `BONE_CHILD_KEY` para evitar que `_boneWorldDir` agarre huesos twist/roll (Mixamo puede insertar `RightArmRoll` como primer hijo de `RightArm`). El mapa define el hijo canonico por key: `rArm→rForeArm`, `rForeArm→rHand`, etc.
- Se agrego `_computeRefs()`: calcula posiciones reales de nariz/boca/orejas/pecho desde los huesos del modelo (no valores hardcodeados). Log confirma `narizY: 1.594 pechoY: 1.197`.
- Se agregaron marcadores de referencia visuales (esferas coloreadas): rojo=nariz, naranja=boca, azul×2=orejas, verde=pecho.
- Se corrigio `_cam3D` para que las manos queden delante del avatar y en la posicion correcta:
  - X: sin negativo — datos no espejados, x<nariz.x → mundo negativo = derecha del avatar ✓
  - Y: multiplicado ×0.5 — el dataset fue capturado con cuerpo completo en frame (muñecas en y≈0.7-0.86), sin comprension las manos quedan por debajo de las caderas.
  - Z: `REF.noseZ + 0.22` — manos 22cm delante del plano de la cabeza, visibles desde la camara.
- Estado actual confirmado por el usuario: manos delante del cuerpo ✓, brazos se mueven ✓, precision de señas y dedos pendiente.

### Decisiones
- El sistema de coordenadas del CSV es no-espejado: la mano derecha del firmante esta en x<0.5 (lado izquierdo de la imagen).
- La compresion Y×0.5 en `_cam3D` es necesaria porque el dataset se capturo mostrando cuerpo completo, no solo manos.
- Los marcadores de referencia (esferas) quedan visibles en produccion para ayudar a calibrar visualmente las poses.

### Pendiente inmediato
1. **Precision de señas**: la posicion de manos mejoro pero no encaja perfectamente. Posible ajuste del factor de compresion Y (actualmente 0.5) o de la altura `_neutralArms`.
2. **Dedos**: `_poseFingers` esta implementado pero la direccion X puede estar negada incorrectamente. En `_poseFingers`, `dx = -(pj[0]-pi[0])` — si los dedos van al reves, quitar el `-`. Ademas `dz=0` hace que todos los dedos queden en el plano XY; se podria añadir un Z heuristico.
3. Reforzar muestras de `tu`, `yo`, `sordo` y reentrenar (prioridad alta, pendiente desde sesiones anteriores).
4. Capturar abecedario LSC en dataset.
5. Fase 2: Migrar BD a MariaDB con SQLAlchemy.
6. Fases 3-5: servidor central, auto-update, PyInstaller.

### Version del script
`comunicar.html` importa: `/static/js/avatar3d.js?v=20260517c`
Si hay dudas de cache, hacer Ctrl+Shift+R en Chrome y confirmar que el Network tab muestra 200 (no 304) para avatar3d.js.

### Comando para iniciar
```powershell
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"
```

## Sesion 2026-05-26

### Hecho
- Se diagnostico y corrigio el congelamiento de imagen en camara local.
- El backend real de la camara local es **MSMF** (Microsoft Media Foundation), no DirectShow.
- Con el codigo anterior, el hilo de fondo de `CamaraStream` iniciaba y comenzaba a leer; luego `cap.set(FRAME_WIDTH/HEIGHT/FPS)` se llamaba desde el hilo principal. MSMF reinicia el stream internamente al cambiar la resolucion mientras otro hilo esta leyendo → imagen congelada.
- La camara IP (DroidCam) no tenia ese problema porque FFMPEG maneja los `cap.set()` de forma diferente.
- Se reescribio `src/camara_stream.py` con dos modos distintos:
  - **Camara local (int):** sin hilo de fondo, sin `CAP_PROP_BUFFERSIZE`. `read()` llama `cap.read()` directamente (bloqueante hasta nuevo frame). Resultado: 30/30 frames unicos, 0 fallos.
  - **Camara IP (str URL):** hilo de fondo + `CAP_PROP_BUFFERSIZE=1`, igual que antes. Sin cambios en el comportamiento.

### Decisiones
- Para camaras locales no se necesita hilo de fondo; `cap.read()` con MSMF bloquea naturalmente hasta el siguiente frame.
- `cap.set()` para resolucion/FPS debe aplicarse antes del primer `read()`, no despues de iniciar un hilo lector.
- La clase `CamaraStream` mantiene la misma interfaz publica (`read`, `set`, `isOpened`, `release`) — ningun archivo que la use necesito cambios.

- Se redujo `min_frames_manos` de `saludos` en `src/config.py` de 14 a 6 (de 70% a 30% de la ventana de 20 frames). El requisito de 2 manos visibles se mantiene intacto. Resultado: la seña se confirma en ~200ms en lugar de ~467ms.
- Se creo la estructura de carpetas para imagenes de la seccion Aprender LSC:
  - `static/images/abecedario/` → `a.jpg` … `z.jpg` (26 letras)
  - `static/images/numeros/`    → `0.jpg` … `9.jpg` (10 numeros)
  - `static/images/saludos/`   → `hola.jpg`, `gracias.jpg`, `bien.jpg`, `mal.jpg`, `ayuda.jpg`, `sordo.jpg`, `yo.jpg`, `tu.jpg`
  - `static/images/frases/`    → imagenes opcionales de frases basicas
  - Cada carpeta tiene un `README.md` con la tabla de nombres exactos y reglas (minuscula, .jpg/.png, min 300x300px).
- El usuario descargara las imagenes LSC de internet y las colocara con los nombres indicados.
- Siguiente paso pendiente: cuando las imagenes esten listas, rediseñar `templates/aprender.html` con cards profesionales (imagen real + modal de detalle + busqueda + marcado aprendida).

- Se ajusto la camara 3D del avatar para mostrar torso hacia arriba (de cintura para arriba con cara visible):
  - FOV: 38 → 34, posicion: (0,1.35,2.1) → (0,1.50,1.65), lookAt: (0,1.0,0) → (0,1.25,0).
- Se corrigieron los marcadores de referencia del avatar (esferas de colores) que aparecian en la zona del cuello/barriga:
  - Causa: el hueso `head` en Mixamo esta en la base del craneo (nivel de menton), no en la cara. `spine1` es la zona lumbar, no el pecho.
  - Nariz: `head.y + 0.09`, Boca: `head.y + 0.05`, Orejas: `head.y + 0.09`, Pecho: usa `spine2.y` (toracico alto) en vez de `spine1.y`.
- Se identifico y corrigio la causa raiz del problema de dedos sin movimiento:
  - `a_puntos()` en `src/services/landmarks_avatar.py` descartaba el Z de MediaPipe (step=3 solo tomaba x,y saltando z).
  - Se corrigio para devolver `[x, y, z]` por landmark — el Z de MediaPipe codifica la profundidad de cada dedo (curvado vs extendido).
  - Se actualizo `_cam3D()` en `avatar3d.js` para usar `pt2D[2]` como offset Z: `zOffset = -pt2D[2] * scale`.
- Se reescribio `_poseFingers()` en `avatar3d.js`:
  - Estima orientacion de palma desde landmarks 2D (spread de nudillos).
  - Rota la muneca (`rHand`/`lHand`) para alinear con la direccion general de la mano.
  - Calcula direccion 3D real de cada segmento de dedo usando los Z del dataset.
- Se agrego `_computeFingerLengths()` que calcula la longitud real de cada hueso de dedo desde el modelo FBX al cargar.
- Diagnostico con logs de consola confirmo que el flujo de datos ES correcto: 42 huesos detectados, rotaciones de 11°-92° calculadas correctamente para los dedos.
- **Problema descubierto:** el modelo Avatar.fbx (futbolista de Mixamo) tiene manos simplificadas sin geometria individual de dedos — los huesos existen pero el mesh no tiene vertices asignados a ellos (skinning weights = 0 en dedos). Por eso las rotaciones calculadas no se ven visualmente.
- **Solucion decidida:** descargar un nuevo modelo de Mixamo con manos detalladas (Y Bot, X Bot, o personaje humano). Pasos: mixamo.com → Characters → seleccionar personaje con manos → Download FBX T-pose → renombrar `Avatar.fbx` → reemplazar `static/models/Avatar.fbx`.

### Pendiente
- **INMEDIATO:** Descargar modelo Mixamo con manos detalladas (Y Bot recomendado) y reemplazar `static/models/Avatar.fbx`. El codigo no cambia, solo el modelo.
- Remover logs de debug temporales en `avatar3d.js` (funciones `_poseFingers` y `_setBoneWorldDir`) una vez confirmado que los dedos se mueven con el nuevo modelo.
- Imagenes de la seccion Aprender LSC: el usuario descarga imagenes LSC y las coloca en `static/images/abecedario/`, `numeros/`, `saludos/`. Luego redisenar `templates/aprender.html` con cards profesionales.
- Reforzar `tu`, `yo`, `sordo` y reentrenar (prioridad alta, pendiente desde sesiones anteriores).
- Fase 2: Migrar BD a MariaDB con SQLAlchemy.
- Fases 3-5: servidor central, auto-update, PyInstaller.

### Problemas conocidos
- Web Speech API no funciona en Brave (usar Chrome).
- DroidCam gratuito: solo 1 hora/dia de HD.
- Modelo Avatar.fbx actual (futbolista Mixamo) no tiene geometria de dedos — reemplazar por Y Bot u otro con manos detalladas.

## Sesion 2026-05-26 (continuacion — Dataset avatar y plan de dedos)

### Contexto
Se discutio el problema principal con la traduccion voz → LSC: el avatar no mueve los dedos correctamente y no ubica bien la postura de la mano para cada seña.

### Decisiones

#### Dataset especializado para avatar (texto/voz → LSC)
- Se decidio crear un dataset separado exclusivamente para la animacion del avatar, distinto al dataset de reconocimiento (`data/senas.csv`).
- **Razon:** el dataset de reconocimiento necesita variacion (angulos, personas, velocidades) para que el modelo sea robusto. El dataset del avatar necesita la forma canonica perfecta de cada seña, capturada una sola vez por un experto firmante.
- El nuevo dataset guarda la secuencia temporal completa (todos los frames), NO el promedio. El `landmarks_avatar.py` actual promedia y eso genera una pose estatica sin movimiento real de dedos.
- Cada seña se guarda como `data/avatar_movimientos/<sena>.json` con el siguiente formato:
```json
{
  "sena": "hola",
  "categoria": "cortesia",
  "manos": "1",
  "duracion": "corta",
  "frames": [
    {
      "frame": 0,
      "mano_der": [[x,y,z], ...],
      "mano_izq": [[x,y,z], ...],
      "ref": { "nariz": [x,y,z], "pecho": [x,y,z] }
    }
  ]
}
```
- Las coordenadas se normalizan relativo a nariz/pecho en el momento de guardar (no en el avatar), para que el avatar reciba datos listos.
- El Z de MediaPipe es critico para los dedos: codifica profundidad relativa a la muneca — diferencia dedo extendido de dedo doblado.

#### Categorias de señas
- Se agregan categorias para organizacion, captura ordenada y seccion Aprender LSC. NO es para mejorar velocidad de busqueda (el lookup por nombre de archivo ya es O(1) y es instantaneo).
- Categorias sugeridas: `cortesia`, `emociones`, `personas`, `familia`, `numeros`, `abecedario`, `frases`.
- La categoria viaja como metadato en el JSON. El lookup siempre es por nombre de seña directo.

#### Prioridad: modelo Avatar.fbx
- **Bloqueante principal:** el Avatar.fbx actual (futbolista Mixamo) no tiene geometria de dedos en el mesh. Las rotaciones se calculan correctamente pero no se ven porque el mesh no tiene vertices asignados a los huesos de dedos.
- Sin cambiar el modelo, ningun avance en el dataset o en avatar3d.js va a mostrar movimiento de dedos.
- **Solucion:** descargar Y Bot de Mixamo (tiene manos completas con dedos detallados).
  - Ir a mixamo.com → Characters → Y Bot → Download → FBX for Unity → T-pose
  - Renombrar a `Avatar.fbx` → reemplazar `static/models/Avatar.fbx`
  - El codigo no cambia, solo el modelo.

### Plan de construccion (en orden)

```
PASO 1 — INMEDIATO (sin codigo):
  Descargar Y Bot de Mixamo → reemplazar static/models/Avatar.fbx
  → desbloquea ver los dedos moverse con el codigo actual

PASO 2 — capturar_avatar.py:
  Nuevo script de captura especializado para el avatar
  - igual a capturar_dataset.py en estructura (cuenta regresiva, calidad de mano, 1 o 2 manos)
  - guarda secuencia temporal completa con [x,y,z] por landmark
  - normaliza coordenadas relativo a nariz/pecho al guardar
  - clasifica: corta (≤15 frames), media (16-30), larga (>30)
  - guarda en data/avatar_movimientos/<sena>.json con categoria

PASO 3 — nuevo endpoint Flask:
  GET /api/animacion/<sena>
  → devuelve todos los frames (no el promedio de landmarks_avatar.py)
  → el avatar los reproduce uno a uno

PASO 4 — avatar3d.js modo animacion:
  - reproduce frames en secuencia con requestAnimationFrame
  - SLERP entre frames para suavidad
  - transicion SLERP entre señas consecutivas en una oracion
```

### Pendiente
- **INMEDIATO:** Descargar Y Bot de Mixamo y reemplazar `static/models/Avatar.fbx`.
- Crear `capturar_avatar.py` con el nuevo formato de dataset.
- Crear endpoint `GET /api/animacion/<sena>`.
- Actualizar `avatar3d.js` para modo de reproduccion de secuencia temporal.
- Imagenes seccion Aprender LSC: colocar en `static/images/abecedario/`, `numeros/`, `saludos/`.
- Reforzar `tu`, `yo`, `sordo` y reentrenar (prioridad alta, pendiente desde sesiones anteriores).
- Fase 2: Migrar BD a MariaDB con SQLAlchemy.
- Fases 3-5: servidor central, auto-update, PyInstaller.

### Problemas conocidos
- Web Speech API no funciona en Brave (usar Chrome).
- DroidCam gratuito: solo 1 hora/dia de HD.
- Modelo Avatar.fbx actual (futbolista Mixamo) no tiene geometria de dedos — REEMPLAZAR POR Y BOT antes de continuar con avatar.

## Sesion 2026-05-26 (continuacion 3 — Pipeline avatar normalizado + fix de brazo)

### Hecho
- Se creo `src/capturar_avatar.py`: herramienta de captura especializada para el dataset del avatar. Guarda la secuencia temporal completa (todos los frames) en `data/avatar_movimientos/<sena>.json` con coordenadas normalizadas relativas a nariz/pecho. Categorias: cortesia, emociones, personas, familia, numeros, abecedario, frases, otra. Duraciones: corta (15f), media (25f), larga (40f). Incluye ventana de revision visual con replay frame a frame.
- Se agrego el endpoint `GET /api/animacion/<sena>` en `run_flask.py`. Devuelve el JSON completo de frames normalizados desde `data/avatar_movimientos/<sena>.json`.
- Se actualizo `avatar3d.js` con funciones de reproduccion de animaciones del nuevo dataset:
  - `startAnimation(framesData, onDone)`: reproduce a 20fps con `setInterval`.
  - `stopAnimation()`: para el intervalo y llama el callback `onDone`.
  - `_normToWorld(normPt)`: convierte coordenadas normalizadas al espacio mundo de Three.js.
  - `_armIKNorm(side, wristNorm)`: IK de brazo desde coordenadas normalizadas.
  - `_poseFingersNorm(ptsNorm, side)`: dedos desde coordenadas normalizadas.
  - `_setPoseFromFrame(frame)`: aplica un frame del dataset al avatar con SLERP rapido (80ms).
- Se actualizo `comunicar.html`:
  - Import actualizado para incluir `startAnimation` y `stopAnimation`.
  - `procesarCola()` primero intenta `/api/animacion/<sena>`, si no existe cae al estatico `setPose`.
  - `limpiarTodo()` llama `stopAnimation()`.
  - Cache de animaciones en `cacheAnimaciones`.
- El usuario capturo las señas `hola` y `bien` con el nuevo dataset.
- Se diagnostico y corrigio el bug principal: **el brazo iba al lado incorrecto**.
  - **Causa raiz**: MediaPipe Holistic usa convenio person-centric. `right_hand_landmarks` = mano DERECHA del firmante (aparece a la izquierda del frame → `norm_x` negativo). En `capturar_avatar.py` estaba invertido (asignaba `right_hand_landmarks` a `mano_izq_lm`).
  - **Fix en `avatar3d.js` (`_setPoseFromFrame`)**: se cambio la asignacion de brazo de etiqueta (`der`/`izq`) a **posicion del muñeca**: `norm_x ≤ 0` → brazo derecho del avatar; `norm_x > 0` → brazo izquierdo. Esto es robusto ante capturas pasadas y futuras.
  - **Fix en `capturar_avatar.py`**: se corrigio la asignacion de MediaPipe: `mano_der_lm = res.right_hand_landmarks`, `mano_izq_lm = res.left_hand_landmarks`.
- El usuario confirmo: el brazo ahora va al lado correcto.

### Estado del sistema al cerrar sesion
- `hola.json` y `bien.json` existen en `data/avatar_movimientos/` con el convenio anterior (data en `izq` con `norm_x` negativo). El fix de posicion los maneja correctamente — **no es necesario recapturarlos**.
- `_neutralArms()` sigue deshabilitado (comentado). Los brazos parten desde T-pose. Funciona para verificar señas. Reactivar cuando se verifique completamente.
- Avatar renderiza con modelo Y Bot (Mixamo, dedos funcionales, 42 huesos detectados).
- El SLERP de animacion es 0.08s por frame (20fps) para seguimiento fluido.

### Convenio de coordenadas normalizadas (definitivo)
```
norm_x = (lm.x - nose_x) * escala
  norm_x < 0 → izquierda del frame → mano DERECHA del firmante → brazo DERECHO del avatar
  norm_x > 0 → derecha del frame  → mano IZQUIERDA del firmante → brazo IZQUIERDO del avatar

norm_y = -(lm.y - nose_y) * escala   (Y invertida: positivo = arriba)
norm_z = -lm.z * escala               (Z invertido: positivo = hacia camara)
Origen: nariz del firmante. Escala: 1 unidad = distancia nariz-pecho.
```

### Estructura del JSON por seña
```json
{
  "sena": "hola", "categoria": "cortesia", "manos": "1",
  "duracion": "media", "total_frames": 25, "calidad_pct": 88.0,
  "frames": [
    { "f": 0, "der": [[x,y,z]×21] o null, "izq": [[x,y,z]×21] o null }
  ]
}
```

### Pendiente inmediato
1. **Verificar postura de dedos "bien"** (pulgar arriba): con el brazo ya en el lado correcto, confirmar que `_poseFingersNorm` genera la postura de pulgar hacia arriba. Si no, ajustar la heuristica de orientacion de palma en `_poseFingersNorm`.
2. **Capturar mas señas** con `capturar_avatar.py` (ahora con convenio correcto): minimo `yo`, `tu`, `ayuda`, `sordo`, `mal`.
3. **Agregar panel dev** para lanzar `capturar_avatar.py` desde la interfaz Flask (similar a `dev/capturar.html`).
4. **Re-habilitar `_neutralArms()`** una vez que `setPose` y la animacion esten verificados completamente.
5. Imagenes seccion Aprender LSC: colocar en `static/images/abecedario/`, `numeros/`, `saludos/`.
6. Reforzar `tu`, `yo`, `sordo` y reentrenar modelo de reconocimiento (prioridad alta).
7. Fase 2: Migrar BD a MariaDB con SQLAlchemy.
8. Fases 3-5: servidor central, auto-update, PyInstaller.

### Archivos clave modificados en esta sesion
| Archivo | Estado |
|---------|--------|
| `src/capturar_avatar.py` | NUEVO — captura dataset normalizado para avatar |
| `static/js/avatar3d.js` | Actualizado — animacion + fix asignacion brazo por posicion |
| `templates/comunicar.html` | Actualizado — usa `startAnimation`, cache animaciones, version `?v=20260527a` |
| `run_flask.py` | Actualizado — endpoint `GET /api/animacion/<sena>` |
| `data/avatar_movimientos/hola.json` | Capturado por el usuario |
| `data/avatar_movimientos/bien.json` | Capturado por el usuario |

### Comando para iniciar
```powershell
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"
```

## Sesion 2026-05-27 / 2026-05-28

### Hecho

#### Pantalla Predecir Seña (OpenCV HUD)
- Se agrandó el texto del párrafo acumulado: escala `0.45 → 0.75`, color amarillo claro `(255,255,150)`, grosor 2.
- La predicción principal se dejó igual (escala 0.8, verde).
- La barra superior se amplió de 56px a 82px para dar espacio al párrafo.
- Se agregó línea separadora sutil entre predicción y párrafo.

#### Avatar 3D — puntos de referencia
- Se agregaron **hombros, orejas, boca y codos** como puntos de referencia en `capturar_avatar.py`.
- Cada frame del JSON ahora incluye `ref: { boca, hombro_der, hombro_izq, oreja_der, oreja_izq, codo_der, codo_izq }`.
- Todos normalizados con el mismo sistema que las manos (origen=nariz, escala=1/dist(nariz-pecho)).
- MediaPipe indices usados: 0=nariz, 7=oreja_izq, 8=oreja_der, 9-10=boca, 11-12=hombros, 13=codo_izq, 14=codo_der.
- Vista previa de captura: puntos de colores sobre el frame (nariz=rojo, boca=naranja, pecho=verde, hombros=naranja oscuro, orejas=cyan, codos=magenta).
- Canvas de revisión: muestra todos los puntos de referencia con leyenda de colores.

#### Colores unificados captura ↔ avatar
| Punto | OpenCV BGR | Three.js | Color |
|-------|-----------|----------|-------|
| Nariz | `(0,0,255)` | `0xff0000` | 🔴 Rojo |
| Boca | `(0,170,255)` | `0xffaa00` | 🟠 Naranja |
| Pecho | `(136,255,68)` | `0x44ff88` | 🟢 Verde |
| Hombros | `(0,119,255)` | `0xff7700` | 🟠 Naranja oscuro |
| Orejas | `(255,208,0)` | `0x00d0ff` | 🩵 Cyan |
| Codos | `(255,0,255)` | — | 🟣 Magenta |

#### Avatar 3D — correcciones de posición
- `_neutralArms()` re-habilitado: brazos parten en posición natural de señas (no T-pose).
- Logs de debug de `_setBoneWorldDir` eliminados de la consola.
- Marcadores de hombros corregidos: antes usaban `rShoulder`/`lShoulder` (clavícula, cerca del cuello). Ahora usan `rArm`/`lArm` (articulación real donde nace el brazo).
- `_computeRefs()` también actualizado para leer hombros desde `rArm`/`lArm`.
- `_normToWorld()`: eliminado el offset Z fijo `+0.15`. Las manos usan Z exactamente del dataset.

#### IK de brazos — IK directo por codo capturado
- Nueva función `_armIKDirect(side, elbowNorm, wristNorm)` en `avatar3d.js`.
- En vez de adivinar la posición del codo con un hint genérico, usa la posición **real** del codo capturado por MediaPipe pose.
- En `_setPoseFromFrame`: si el frame tiene `ref.codo_der`/`ref.codo_izq` → usa `_armIKDirect`. Si no (capturas antiguas) → cae al hint genérico `_armIKNorm`.
- Se descubrió que el hint Z fijo `-0.5` causaba que el codo fuera demasiado hacia atrás para señas bajas (`bien`) y que el brazo rodeara la cabeza para señas altas (`hola`).

#### Hint adaptativo (fallback para capturas sin codo)
- El hint Z del IK es ahora adaptativo: `+0.3` cuando el objetivo está sobre el hombro, `-0.15` cuando está debajo.

### Decisiones
- Los codos de MediaPipe Holistic pose dan la posición exacta del doblado del brazo → IK directo es más preciso que cualquier hint.
- El formato JSON de `data/avatar_movimientos/` es compatible hacia atrás: capturas sin `ref.codo_*` usan hint, capturas nuevas usan IK directo.
- Se borró `hola.json` y `bien.json` capturados sin codos. Hay que recapturar ambos con el nuevo script.

### Pendiente INMEDIATO
1. **Recapturar señas** con el nuevo `capturar_avatar.py` que incluye codos:
   - `hola`, `bien` (las antiguas fueron borradas)
   - Mínimo también: `yo`, `tu`, `ayuda`, `sordo`, `mal`
2. Probar que el IK directo (`_armIKDirect`) produce la postura correcta del brazo para cada seña.
3. Verificar dedos — `_poseFingersNorm` implementado pero no verificado visualmente después de todos los cambios.

### Pendiente general
- Reforzar `tu`, `yo`, `sordo` y reentrenar modelo de reconocimiento (prioridad alta, pendiente desde semanas).
- Imágenes sección Aprender LSC en `static/images/abecedario/`, `numeros/`, `saludos/`.
- Fase 2: Migrar BD a MariaDB con SQLAlchemy.
- Fases 3-5: servidor central, auto-update, PyInstaller.

### Archivos clave modificados
| Archivo | Cambio |
|---------|--------|
| `src/predecir_sena.py` | Párrafo más grande en HUD |
| `src/capturar_avatar.py` | Agrega boca, hombros, orejas, codos al ref de cada frame |
| `static/js/avatar3d.js` | `_neutralArms` habilitado, hombros desde rArm, `_armIKDirect`, hint adaptativo, cache `?v=20260528d` |
| `templates/comunicar.html` | Cache bumpeado a `?v=20260528d` |
| `data/avatar_movimientos/` | Vacío — hola.json y bien.json borrados, pendiente recapturar |

### Versión del script JS
`comunicar.html` importa: `/static/js/avatar3d.js?v=20260528d`
Para forzar recarga: Ctrl+Shift+R en Chrome.

### Comandos para retomar
```powershell
# Iniciar servidor Flask
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"

# Capturar señas para el avatar (con todos los puntos de referencia)
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\src\capturar_avatar.py"
```

---

## Sesion 2026-06-07

### Hecho
- Se discutio y planeo la mejora completa del avatar: expresiones faciales (gramatica LSC), dedos precisos y colocacion de mano.
- Se decidio migrar el avatar de **Mixamo FBX a formato VRM** porque VRM tiene morph targets faciales estandar y geometria de dedos garantizada.
- Se reescribio `static/js/avatar3d.js` completamente para VRM:
  - Carga via `GLTFLoader` + `VRMLoaderPlugin` de `@pixiv/three-vrm@2.1.2`.
  - Bones accedidos via `vrm.humanoid.getRawBoneNode(vrmName)` (huesos reales del grafo de escena).
  - Mapeo `VRM_BONE_MAP`: claves internas → nombres estandar VRM 1.0 humanoid (rightUpperArm, rightIndexProximal, etc.).
  - IK de brazos preservado: `_armIKDirect` (con codo capturado), `_armIKNorm` (fallback), `_armIKWorld` (base).
  - Postura de dedos preservada: `_poseFingersNorm` y `_poseFingers` (dataset antiguo).
  - `VRMUtils.rotateVRM0(vrm)` para que el avatar mire hacia la camara (+Z).
  - Se agrego `setExpression(name, intensity, durationSecs)`: activa expresion facial con SLERP suave.
  - Se agrego `clearExpression(durationSecs)`: vuelve a neutral suavemente.
  - Parpadeo automatico cada 3-6 segundos (`_updateBlink`) para que el avatar se sienta vivo.
  - En el render loop: NO se llama `vrm.humanoid.update()` (sobreescribiria los huesos), solo `vrm.expressionManager.update(dt)`.
- Se actualizo `templates/comunicar.html`:
  - Importmap ampliado con `@pixiv/three-vrm`.
  - Importa `setExpression` y `clearExpression` de `avatar3d.js`.
  - `EXPRESION_SENA`: diccionario de expresiones lexicas por seña (bien→happy, mal→sad, hola→happy, ayuda→surprised, etc.).
  - `detectarExpresionGramatical(texto)`: analiza puntuacion: `?`→surprised (cejas arriba), `!`→happy, `no/nunca`→angry (ceno).
  - Expresion gramatical persiste durante toda la frase; expresion lexica tiene prioridad sobre la gramatical.
  - `clearExpression` solo se llama cuando se vacia la cola (no entre señas de la misma frase).
  - Version cache bumpeada a `?v=20260607a`.
- El usuario descargo un avatar de VRoid Hub/Studio exportado como `.vrm`.
  - Archivo colocado en `static/models/Avatar_LSC.vrm`.
  - Ruta actualizada en `avatar3d.js`.

### Decisiones
- **Formato definitivo del avatar: VRM** (descarta Mixamo FBX para siempre).
  - VRM tiene blend shapes faciales estandar (happy, sad, angry, surprised, relaxed, blink, aa/ih/ou/ee/oh).
  - VRM tiene rig de dedos completo garantizado (a diferencia del Y Bot que no tenia geometria de dedos).
  - `@pixiv/three-vrm@2` via CDN jsDelivr, compatible con Three.js r160.
- Las expresiones faciales se manejan por codigo (NO por captura con camara), porque:
  - Las expresiones gramaticales dependen de la oración, no de la seña.
  - Las expresiones lexicas son un mapeo fijo y predecible.
  - Capturar face mesh durante la seña es complejo y poco reproducible.
- `vrm.humanoid.update()` NO se llama en el render loop para que no sobreescriba las rotaciones de huesos calculadas por el IK.

### Pendiente INMEDIATO
1. **Probar el avatar en Chrome**: iniciar servidor, abrir `/comunicar`, verificar en DevTools (F12 → Console):
   - Mensaje `[avatar3d] huesos: X / 44` (deberian ser ~44 huesos).
   - Sin errores en rojo.
2. **Verificar orientacion**: si el avatar aparece de espaldas, cambiar `VRMUtils.rotateVRM0(vrm)` por `vrm.scene.rotation.y = 0` en `avatar3d.js` linea ~155.
3. **Probar señas**: escribir "bien" en el campo manual → verificar que el brazo se mueve y la expresion happy aparece.
4. **Recapturar señas** con `capturar_avatar.py`: hola, bien, yo, tu, ayuda, sordo, mal (los JSONs anteriores fueron borrados en sesion 2026-05-28).

### Pendiente general
- Reforzar muestras `tu`, `yo`, `sordo` y reentrenar modelo de reconocimiento (prioridad alta desde semanas).
- Imagenes seccion Aprender LSC en `static/images/abecedario/`, `numeros/`, `saludos/`.
- Fase 2: Migrar BD a MariaDB con SQLAlchemy.
- Fases 3-5: servidor central, auto-update, PyInstaller.

### Expresiones implementadas (referencia rapida)
| Seña / Situacion | Expresion | Intensidad |
|---|---|---|
| `bien` | happy | 70% |
| `hola`, `saludos` | happy | 45% |
| `mal` | sad | 60% |
| `ayuda` | surprised | 50% |
| `sordo`, `yo`, `tu` | relaxed | 20-30% |
| Frase con `?` o `¿` | surprised | 55% |
| Frase con `!` o `¡` | happy | 65% |
| Frase con "no/nunca/jamas" | angry | 30% |

### Archivos clave modificados
| Archivo | Cambio |
|---------|--------|
| `static/js/avatar3d.js` | Reescrito para VRM: carga GLTFLoader+VRMLoaderPlugin, expresiones faciales, parpadeo, misma IK/dedos |
| `templates/comunicar.html` | Importmap VRM, setExpression/clearExpression, EXPRESION_SENA, deteccion gramatical |
| `static/models/Avatar_LSC.vrm` | Nuevo modelo VRM (reemplaza Avatar.fbx) |

### Comando para iniciar
```powershell
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"
```

---

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
