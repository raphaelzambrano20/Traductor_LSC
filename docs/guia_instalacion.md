# Guía de instalación para colaboradores

Pasos para ejecutar el Traductor LSC en un computador con Windows y empezar a trabajar en el
código. Las reglas de trabajo en equipo están en [CONTRIBUTING.md](../CONTRIBUTING.md).

## 1. Qué instalar

| Programa | Para qué | Dónde |
|---|---|---|
| **Git** | Bajar y subir el código | https://git-scm.com/download/win |
| **Python 3.10** | Ejecutar la app. Marcar *Add python.exe to PATH* al instalar. No usar 3.12 o superior | https://www.python.org/downloads/release/python-31011/ |
| **Google Chrome** | La Web Speech API (voz) solo funciona ahí | https://www.google.com/chrome |
| **VS Code** (opcional) | Editor | https://code.visualstudio.com |

Para las señas con cámara se necesita una webcam, o DroidCam en el celular.

## 2. Acceso al repositorio

Quien administra el repositorio invita a la persona como colaborador (Settings → Collaborators).
Hay que aceptar la invitación que llega al correo de GitHub. Sin eso se puede clonar, pero no
subir cambios.

## 3. Clonar e instalar

En PowerShell:

```powershell
git config --global user.name "Su nombre"
git config --global user.email "su-correo@ejemplo.com"

git clone https://github.com/raphaelzambrano20/Traductor_LSC.git
cd Traductor_LSC

py -3.10 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

La instalación tarda unos minutos porque descarga MediaPipe, OpenCV y scikit-learn.
`requirements.txt` ya incluye `pytest`.

## 4. Configurar las credenciales

Las claves no están en el código. Se crea el archivo `.env` propio:

```powershell
copy .env.example .env
notepad .env
```

Valores a completar:

- `LSC_DEV_PASSWORD`: clave del modo desarrollador (`/dev`). Se pide por mensaje privado a
  quien ya tiene el proyecto; nunca se publica en el repositorio.
- `LSC_SECRET_KEY`: llave de sesiones de Flask, propia de cada computador. Se genera con:

```powershell
venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

El archivo `.env` es local: git lo ignora y nunca se sube.

## 5. Ejecutar la app

```powershell
venv\Scripts\python.exe run_flask.py
```

Se abre el navegador en http://127.0.0.1:5000. Usar **Chrome** y dar permiso al micrófono cuando
lo pida.

## 6. Archivos que no vienen en el repositorio

La app arranca sin ellos, pero con funciones limitadas. Se piden a quien ya tiene el proyecto
(Drive o USB) y se copian en estas carpetas:

| Archivo | Carpeta | Qué habilita |
|---|---|---|
| `senas.csv` | `data\` | El dataset de señas (necesario para reentrenar). |
| `modelo_lsc.pkl` | `models\` | El reconocimiento de **seña → voz**. Sin él esa parte no funciona. |
| `vosk-model-small-es-0.42` | `models\` | Respaldo de voz sin internet. Opcional; se descarga de https://alphacephei.com/vosk/models. |

El dataset y el modelo no están en git. Si dos personas capturan señas por separado, quedan
desincronizados: hay que acordar quién es dueño de esos archivos y pasarse la versión nueva cada
vez.

## 7. Flujo de trabajo

Nunca se trabaja directo en `main` ni en `Staging`:

```powershell
git switch Staging
git pull
git switch -c feat/nombre-del-cambio

# ...cambios...
git add archivo1 archivo2
git commit -m "feat: descripción corta en español"
git push -u origin feat/nombre-del-cambio
```

La primera vez que se sube, se abre el navegador para iniciar sesión en GitHub.

Después se abre un PR de la rama hacia **Staging**, y otra persona lo revisa y lo une. Luego un
PR de `Staging` a **main** (producción).

Antes de abrir el PR se corren las pruebas:

```powershell
venv\Scripts\python.exe -m pytest
```

Los commits y PR no llevan marcas de IA. El detalle completo está en
[CONTRIBUTING.md](../CONTRIBUTING.md).

## 8. Problemas frecuentes

- **`pip install` falla con mediapipe:** instalar el
  [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) y repetir.
- **`py -3.10` no se reconoce:** reinstalar Python marcando *Add python.exe to PATH*, o usar
  `python` si `python --version` indica 3.10.
- **El modo `/dev` dice "no configurado":** falta `LSC_DEV_PASSWORD` en el `.env`.
- **No reconoce la voz:** se está usando Brave u otro navegador; usar Chrome.
