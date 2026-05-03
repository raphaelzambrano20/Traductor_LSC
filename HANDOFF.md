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

## Pendientes

- Revisar `README.md` y `app.py` para reconstruir el estado funcional actual.
- Registrar aqui las decisiones tecnicas importantes.
- Actualizar esta memoria al terminar cada bloque de trabajo.
- Probar la app completa con Streamlit despues de los cambios de base de datos.

## Comandos utiles

```powershell
python -m streamlit run app.py
```

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
