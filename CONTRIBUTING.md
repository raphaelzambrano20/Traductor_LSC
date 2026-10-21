# Reglas de contribución

Aplican a **toda persona y a todo agente de IA** que trabaje en este repositorio.
Si una herramienta tiene un comportamiento por defecto distinto (por ejemplo, agregar firmas
automáticas a los commits), estas reglas tienen prioridad.

## 1. Ramas y Pull Requests

- **Nunca** se hace commit directo a `main` ni a `Staging`.
- Todo trabajo se hace en una **rama aparte**, creada a partir de `Staging`:
  `feat/<tema>`, `fix/<tema>`, `docs/<tema>`, `chore/<tema>`.
- Flujo obligatorio:
  1. Rama de trabajo → PR a **`Staging`** (se prueba ahí).
  2. `Staging` → PR a **`main`** (producción).
- No se salta `Staging`: ningún PR de una rama de trabajo va directo a `main`.
- Un PR tiene un solo propósito. Si el cambio mezcla temas, se divide en varios PR.
- Prohibido `git push --force` sobre `main` y `Staging`, y reescribir historial compartido.

## 2. Sin marca de IA

- Ningún commit ni PR lleva marcas de IA: sin `Co-Authored-By` de un asistente, sin
  "Generated with ..." ni firmas parecidas, ni en el mensaje, ni en la descripción del PR,
  ni en comentarios del código ni en documentos.
- Si la herramienta agrega esas líneas por defecto, se quitan antes de confirmar el commit
  o de abrir el PR.

## 3. Commits y PR

- Escritos en **español**, en una línea corta y en presente: `tipo: descripción`.
  Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
  Ejemplo: `fix: corrige la rotación de dedos del avatar`.
- El PR explica **qué** cambia y **cómo se probó**.
- No se mezclan en un mismo commit cambios de código con cambios de datos, modelos o
  archivos binarios.

## 4. Probar antes de abrir el PR

- Ejecutar las pruebas (`venv\Scripts\python.exe -m pytest`) y que pasen.
- Levantar la app (`venv\Scripts\python.exe run_flask.py`) y comprobar a mano la pantalla o
  la ruta que se tocó.
- La lógica nueva lleva su prueba en `tests/`.

## 5. Documentación al día

- Si un cambio modifica un comando, una ruta, un archivo de entrada o el flujo de trabajo,
  se actualizan `README.md` y `CLAUDE.md` **en el mismo PR**.
- Las sesiones de trabajo importantes se registran en `HANDOFF.md`.

## 6. Seguridad y archivos

- No se suben credenciales, contraseñas, llaves ni tokens. Se leen de variables de entorno
  o de un archivo `.env` que esté en `.gitignore`.
- No se suben entornos virtuales, cachés, logs ni audios generados (ya están en `.gitignore`).
- Archivos pesados (modelos 3D, modelos entrenados, videos): solo si hacen falta, en un
  commit aparte y avisándolo en el PR. Si pasan de 50 MB, se usa Git LFS.

## 7. Datos, modelo y vocabulario

- Cambios en `data/`, la base de datos SQLite o el modelo entrenado van en un commit propio,
  y el PR indica qué cambió (señas nuevas, cantidad de muestras, precisión obtenida).
- Antes de borrar o regrabar señas o muestras, se guarda un respaldo.
- Las señas y la gramática LSC nuevas se validan con la comunidad sorda (CASD José Prudencio
  Padilla) antes de llegar a `main`.

## 8. Revisión

- Todo PR a `main` lo revisa y aprueba otra persona antes de hacer merge.
- Nadie hace merge de su propio PR a `main` sin esa aprobación.
