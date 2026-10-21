# traductor_lsc_ia — Traductor bidireccional de LSC (LSCNOVA)

> Tesis. Ingeniería Informática, UNIPAZ. Semillero SISINFO. Trabaja y responde en español.
> App de escritorio en Flask + HTML/CSS/JS. Entrada: `run_flask.py` → http://127.0.0.1:5000
> Historial detallado de cada sesión: ver `HANDOFF.md` (este archivo es el resumen vivo; el HANDOFF es la bitácora).

## Qué es

Traductor LSC bidireccional en tiempo real para aula, con dos flujos:

- **Pipeline 1 (Seña → Voz):** cámara + MediaPipe + clasificador ExtraTrees (`data/senas.csv`, 212 features, ventana de 20 frames). Predicción en `src/predecir_sena.py` (ventana OpenCV). ~99,55 %.
- **Pipeline 2 (Voz → Seña):** Web Speech API (en Chrome) o Vosk → texto → traducción → el avatar VRM ejecuta la seña. UI en `templates/comunicar.html`.

## Componentes reales (estado actual)

- **Avatar:** VRM en `static/models/Avatar_LSC.vrm`, lógica en `static/js/avatar3d.js` con `@pixiv/three-vrm@2` + Three.js r160.
- **Captura de señas para el avatar:** `src/capturar_avatar.py` → guarda en `data/avatar_movimientos/<sena>.json` (hoy: secuencia temporal de landmarks normalizados a nariz/pecho, con refs de boca/orejas/hombros/codos).
- **Reproducción:** endpoint `GET /api/animacion/<sena>`; `avatar3d.js` reproduce los frames.
- **Traducción de texto:** `src/services/traductor_texto.py` (busca frases → palabras → deletreo). Vocabulario, categorías y sinónimos en SQLite (`data/traductor_lsc.db`).
- **Expresiones faciales:** blendshapes VRM por código (`setExpression`/`clearExpression`), mapa léxico `EXPRESION_SENA` + detección gramatical por puntuación. NO se capturan con cámara (decisión deliberada).

## Problema actual del avatar (a resolver — Cambio 1)

La reproducción de las señas sale mal: los dedos apuntan en dirección equivocada y los huesos se ven rotos. **Causa raíz:** el dataset guarda *landmarks* y `avatar3d.js` RECONSTRUYE las rotaciones de huesos en tiempo de reproducción con IK y heurísticas propias (frágiles, mal condicionadas). Cada modelo nuevo vuelve a romperlas.

## Cambio 1 (FOCO ACTUAL): grabación en tiempo real + guardar ROTACIONES

Principio: resolver las rotaciones UNA vez al capturar (viéndolas correctas en el avatar) y guardar esas rotaciones, no los puntos. La reproducción solo interpola rotaciones guardadas. Lo que se ve al grabar es lo que se reproduce → elimina los bugs de dedos/huesos.

- Captura: webcam → MediaPipe → **Kalidokit** (solver) → aplicar rotaciones de huesos + (opcional) al VRM **en vivo**, viéndome reflejado mientras hago la seña.
- Grabar: guardar por frame las **rotaciones de huesos** (brazos, manos, dedos). Cambia el formato de `data/avatar_movimientos/<sena>.json` (de landmarks a rotaciones).
- Reproducción: cargar frames y SLERP de las rotaciones sobre los huesos. **Eliminar** el IK de runtime (`_armIKDirect`, `_poseFingersNorm`, etc.).
- Revisar y regrabar tomas hasta que se vean bien.
- Las expresiones faciales siguen por código (no se capturan).
- Recapturar las señas con el nuevo formato (`hola`, `bien`, `yo`, `tu`, `ayuda`, `sordo`, `mal` y las que sigan).

Nota: Kalidokit es un solver probado para VRM, pero es algo antiguo (usa MediaPipe Holistic); puede necesitar adaptación menor para `@pixiv/three-vrm@2` y Three.js r160. El seguimiento de dedos de MediaPipe tiene límites por oclusión: algunas señas requerirán regrabarse o retoque manual.

## Cambio 2: gramática a glosa en ambos sentidos

Glosa = representación intermedia escrita que respeta la gramática de la LSC (no es español palabra por palabra). Enfoque por reglas + diccionario (no NMT: no hay corpus suficiente). Acotar a un dominio limitado (presentación personal / aula).

- **Pipeline 2 (Español → Glosa):** módulo nuevo que reordena, omite (artículos, ser/estar) y marca (pregunta, negación) ANTES del lookup de clips. Los marcadores también alimentan las expresiones.
- **Pipeline 1 (Glosa → Español):** módulo nuevo que convierte la secuencia de señas reconocidas en español natural ANTES de la voz (formaliza y reemplaza las reglas ad-hoc de repetición/sinónimos).

## Orden de trabajo

1. **Cambio 1 (avatar):** grabación en tiempo real + rotaciones. Bloqueante y visible.
2. **Cambio 2 (glosa):** primero Pipeline 2 (voz → seña), luego Pipeline 1 (seña → voz).

## Convenciones de trabajo

- Responder y comentar el código en español.
- Alcance mínimo y enfocado; no agregar cosas no pedidas.
- Al modificar un archivo, entregar el archivo completo y corregido (no diffs parciales).
- Avanzar por pasos y probar antes de seguir.
- Ante una decisión de diseño con varias opciones, preguntar antes de asumir.
- Web Speech API solo funciona en Chrome (Brave la bloquea).
- La gramática y las señas en LSC se validan con la comunidad sorda (CASD José Prudencio Padilla).

## Comandos

```powershell
# Iniciar servidor
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\run_flask.py"

# Capturar señas para el avatar
& "c:\Users\LEANDRO\traductor_lsc_ia - copia\venv\Scripts\python.exe" "c:\Users\LEANDRO\traductor_lsc_ia - copia\src\capturar_avatar.py"
```
