import json


def _pasos_para_avatar(pasos):
    datos = []
    for paso in pasos or []:
        datos.append(
            {
                "texto": str(paso.get("texto", "")).strip(),
                "categoria": str(paso.get("categoria", "")).strip(),
                "tipo": str(paso.get("tipo", "")).strip(),
                "recursoTipo": paso.get("recurso_tipo"),
                "recursoData": paso.get("recurso_data"),
            }
        )
    return datos


def html_avatar_animado(pasos=None, en_vivo=False, reproducir_auto=False, recursos=None):
    secuencia = json.dumps(_pasos_para_avatar(pasos), ensure_ascii=False).replace("</", "<\\/")
    modo_vivo = "true" if en_vivo else "false"
    auto = "true" if reproducir_auto else "false"
    recursos_json = json.dumps(recursos or {}, ensure_ascii=False).replace("</", "<\\/")

    return (
        AVATAR_TEMPLATE.replace("__SECUENCIA__", secuencia).replace("__EN_VIVO__", modo_vivo)
        .replace("__REPRODUCIR_AUTO__", auto)
        .replace("__RECURSOS__", recursos_json)
    )


AVATAR_TEMPLATE = r"""
<div class="lsc-avatar-shell">
  <div class="lsc-avatar-toolbar">
    <button id="playSequence" type="button">Reproducir secuencia</button>
    <button id="startLive" type="button">Iniciar voz en vivo</button>
    <button id="stopLive" type="button">Detener</button>
    <span id="avatarStatus">Avatar listo</span>
  </div>
  <div class="lsc-avatar-stage">
    <canvas id="avatarCanvas" width="860" height="470"></canvas>
    <video id="signVideo" playsinline muted></video>
    <img id="signImage" alt="" />
  </div>
  <div class="lsc-avatar-text">
    <strong id="currentSign">Reposo</strong>
    <span id="liveText"></span>
  </div>
</div>

<style>
  .lsc-avatar-shell {
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    overflow: hidden;
    background: #f8fafc;
    color: #111827;
    font-family: Arial, sans-serif;
  }
  .lsc-avatar-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    background: #ffffff;
    flex-wrap: wrap;
  }
  .lsc-avatar-toolbar button {
    border: 1px solid #cbd5e1;
    background: #ffffff;
    color: #111827;
    border-radius: 6px;
    padding: 7px 10px;
    cursor: pointer;
    font-size: 14px;
  }
  .lsc-avatar-toolbar button:hover {
    background: #eef2ff;
  }
  .lsc-avatar-toolbar button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
  #avatarStatus {
    margin-left: auto;
    color: #475569;
    font-size: 13px;
  }
  #avatarCanvas {
    display: block;
    width: 100%;
    height: 430px;
    background: #f8fafc;
  }
  .lsc-avatar-stage {
    position: relative;
    background: #f8fafc;
  }
  #signVideo,
  #signImage {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 430px;
    object-fit: contain;
    background: #f8fafc;
    display: none;
  }
  .lsc-avatar-text {
    min-height: 48px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 14px;
    border-top: 1px solid #e5e7eb;
    background: #ffffff;
  }
  #currentSign {
    font-size: 18px;
  }
  #liveText {
    color: #64748b;
    font-size: 13px;
  }
</style>

<script>
(() => {
  const sequence = __SECUENCIA__;
  const liveMode = __EN_VIVO__;
  const autoPlay = __REPRODUCIR_AUTO__;
  const resourceMap = __RECURSOS__;
  const canvas = document.getElementById("avatarCanvas");
  const ctx = canvas.getContext("2d");
  const signVideo = document.getElementById("signVideo");
  const signImage = document.getElementById("signImage");
  const playButton = document.getElementById("playSequence");
  const startLiveButton = document.getElementById("startLive");
  const stopLiveButton = document.getElementById("stopLive");
  const statusEl = document.getElementById("avatarStatus");
  const currentSignEl = document.getElementById("currentSign");
  const liveTextEl = document.getElementById("liveText");

  const aliases = {
    "saludo": "saludos",
    "buen": "bien",
    "bueno": "bien",
    "buena": "bien",
    "malo": "mal",
    "mala": "mal",
    "ayudar": "ayuda",
    "ayudame": "ayuda",
    "usted": "tu"
  };

  const basePose = {
    left: [0.33, 0.76],
    right: [0.67, 0.76],
    leftShape: "open",
    rightShape: "open",
    expression: "neutral",
    marker: ""
  };

  const signs = {
    "reposo": {
      label: "Reposo",
      duration: 900,
      frames: [
        { p: 0, left: [0.33, 0.76], right: [0.67, 0.76] },
        { p: 1, left: [0.33, 0.76], right: [0.67, 0.76] }
      ]
    },
    "sin_sena": {
      label: "Sin sena",
      duration: 900,
      frames: [
        { p: 0, left: [0.33, 0.76], right: [0.67, 0.76] },
        { p: 1, left: [0.33, 0.76], right: [0.67, 0.76] }
      ]
    },
    "ninguna": {
      label: "Ninguna",
      duration: 900,
      frames: [
        { p: 0, left: [0.33, 0.76], right: [0.67, 0.76] },
        { p: 1, left: [0.33, 0.76], right: [0.67, 0.76] }
      ]
    },
    "hola": {
      label: "Hola",
      duration: 1450,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "open" },
        { p: 0.16, right: [0.70, 0.34], rightShape: "open" },
        { p: 0.34, right: [0.78, 0.29], rightShape: "open", expression: "smile" },
        { p: 0.52, right: [0.66, 0.28], rightShape: "open", expression: "smile" },
        { p: 0.70, right: [0.78, 0.29], rightShape: "open", expression: "smile" },
        { p: 0.88, right: [0.70, 0.34], rightShape: "open", expression: "smile" },
        { p: 1, right: [0.67, 0.76], rightShape: "open" }
      ]
    },
    "saludos": {
      label: "Saludos",
      duration: 1550,
      frames: [
        { p: 0, left: [0.33, 0.76], right: [0.67, 0.76], leftShape: "open", rightShape: "open" },
        { p: 0.18, left: [0.32, 0.34], right: [0.68, 0.34], leftShape: "open", rightShape: "open" },
        { p: 0.38, left: [0.25, 0.29], right: [0.75, 0.29], leftShape: "open", rightShape: "open", expression: "smile" },
        { p: 0.58, left: [0.36, 0.31], right: [0.64, 0.31], leftShape: "open", rightShape: "open", expression: "smile" },
        { p: 0.78, left: [0.25, 0.29], right: [0.75, 0.29], leftShape: "open", rightShape: "open", expression: "smile" },
        { p: 1, left: [0.33, 0.76], right: [0.67, 0.76], leftShape: "open", rightShape: "open" }
      ]
    },
    "yo": {
      label: "Yo",
      duration: 1200,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "point" },
        { p: 0.30, right: [0.52, 0.58], rightShape: "point", marker: "chest" },
        { p: 0.72, right: [0.50, 0.58], rightShape: "point", marker: "chest" },
        { p: 1, right: [0.67, 0.76], rightShape: "point" }
      ]
    },
    "tu": {
      label: "Tu",
      duration: 1200,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "point" },
        { p: 0.28, right: [0.55, 0.50], rightShape: "point", marker: "forward" },
        { p: 0.72, right: [0.62, 0.43], rightShape: "point", marker: "forward" },
        { p: 1, right: [0.67, 0.76], rightShape: "point" }
      ]
    },
    "ayuda": {
      label: "Ayuda",
      duration: 1450,
      frames: [
        { p: 0, left: [0.33, 0.76], right: [0.67, 0.76], leftShape: "palm", rightShape: "fist" },
        { p: 0.25, left: [0.48, 0.64], right: [0.54, 0.66], leftShape: "palm", rightShape: "fist" },
        { p: 0.58, left: [0.47, 0.53], right: [0.54, 0.54], leftShape: "palm", rightShape: "fist", expression: "focus" },
        { p: 0.82, left: [0.47, 0.50], right: [0.54, 0.50], leftShape: "palm", rightShape: "fist", expression: "focus" },
        { p: 1, left: [0.33, 0.76], right: [0.67, 0.76], leftShape: "palm", rightShape: "fist" }
      ]
    },
    "sordo": {
      label: "Sordo",
      duration: 1450,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "point" },
        { p: 0.25, right: [0.66, 0.30], rightShape: "point", marker: "ear", expression: "focus" },
        { p: 0.52, right: [0.66, 0.30], rightShape: "point", marker: "ear", expression: "focus" },
        { p: 0.78, right: [0.58, 0.39], rightShape: "point", marker: "mouth", expression: "focus" },
        { p: 1, right: [0.67, 0.76], rightShape: "point" }
      ]
    },
    "bien": {
      label: "Bien",
      duration: 1150,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "thumbUp" },
        { p: 0.30, right: [0.61, 0.51], rightShape: "thumbUp", expression: "smile" },
        { p: 0.72, right: [0.61, 0.47], rightShape: "thumbUp", expression: "smile" },
        { p: 1, right: [0.67, 0.76], rightShape: "thumbUp" }
      ]
    },
    "mal": {
      label: "Mal",
      duration: 1150,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "thumbDown" },
        { p: 0.28, right: [0.61, 0.51], rightShape: "thumbDown", expression: "sad" },
        { p: 0.72, right: [0.61, 0.61], rightShape: "thumbDown", expression: "sad" },
        { p: 1, right: [0.67, 0.76], rightShape: "thumbDown" }
      ]
    }
  };

  let queue = [];
  let activeSign = null;
  let activeStarted = 0;
  let lastPose = { ...basePose };
  let recognition = null;

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\u00f1/g, "n")
      .trim();
  }

  function tokenize(value) {
    return normalizeText(value).split(/[^a-z0-9]+/).filter(Boolean);
  }

  function title(value) {
    const text = String(value || "").trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Reposo";
  }

  function signNameFor(value) {
    const key = normalizeText(value).replace(/\s+/g, "_");
    if (signs[key]) return key;
    if (aliases[key] && signs[aliases[key]]) return aliases[key];
    return key;
  }

  function letterSign(letter) {
    return {
      label: letter.toUpperCase(),
      duration: 720,
      frames: [
        { p: 0, right: [0.67, 0.76], rightShape: "letter" },
        { p: 0.25, right: [0.56, 0.52], rightShape: "letter", letter: letter.toUpperCase() },
        { p: 0.75, right: [0.56, 0.52], rightShape: "letter", letter: letter.toUpperCase() },
        { p: 1, right: [0.67, 0.76], rightShape: "letter" }
      ]
    };
  }

  function signFor(value) {
    const key = signNameFor(value);
    if (signs[key]) return signs[key];
    if (/^[a-z0-9]$/.test(key)) return letterSign(key);
    return null;
  }

  function resourceFor(value) {
    const key = signNameFor(value);
    return resourceMap[key] || resourceMap[normalizeText(value).replace(/\s+/g, "_")] || null;
  }

  function resourceSign(value, resource) {
    return {
      label: title(value),
      duration: resource.tipo === "imagen" ? 1500 : 1800,
      resourceTipo: resource.tipo,
      resourceData: resource.data,
      frames: signs.reposo.frames
    };
  }

  function enqueueSign(value) {
    const normalized = normalizeText(value);
    if (!normalized) return;

    const resource = resourceFor(normalized);
    if (resource && resource.data) {
      queue.push(resourceSign(resource.texto || normalized, resource));
      if (!activeSign) startNextSign();
      return;
    }

    const sign = signFor(normalized);
    if (sign) {
      queue.push(sign);
      if (!activeSign) startNextSign();
      return;
    }

    for (const char of normalized.replace(/[^a-z0-9]/g, "")) {
      queue.push(letterSign(char));
    }
    if (!activeSign) startNextSign();
  }

  function enqueueText(value) {
    const words = tokenize(value);
    for (const word of words) enqueueSign(word);
  }

  function enqueueStep(step) {
    if (step.recursoData) {
      queue.push(resourceSign(step.texto, { tipo: step.recursoTipo, data: step.recursoData }));
      if (!activeSign) startNextSign();
      return;
    }

    enqueueText(step.texto);
  }

  function playSequence() {
    queue = [];
    hideResource();
    for (const step of sequence) enqueueStep(step);
    if (!sequence.length) {
      statusEl.textContent = "No hay secuencia para reproducir";
    }
  }

  function startNextSign() {
    hideResource();
    activeSign = queue.shift() || null;
    activeStarted = performance.now();
    if (activeSign) {
      currentSignEl.textContent = activeSign.label;
      statusEl.textContent = queue.length ? "Reproduciendo" : "Reproduciendo ultima sena";
      if (activeSign.resourceData) {
        playResource(activeSign);
      }
    } else {
      currentSignEl.textContent = "Reposo";
      statusEl.textContent = "Avatar listo";
    }
  }

  function hideResource() {
    signVideo.pause();
    signVideo.removeAttribute("src");
    signVideo.load();
    signVideo.style.display = "none";
    signImage.removeAttribute("src");
    signImage.style.display = "none";
    canvas.style.visibility = "visible";
  }

  function playResource(sign) {
    canvas.style.visibility = "hidden";
    if (sign.resourceTipo === "video") {
      signVideo.src = sign.resourceData;
      signVideo.currentTime = 0;
      signVideo.style.display = "block";
      signVideo.onended = () => {
        activeSign = null;
        startNextSign();
      };
      signVideo.play().catch(() => {
        statusEl.textContent = "Pulse Reproducir secuencia para ver el video";
      });
    } else if (sign.resourceTipo === "imagen") {
      signImage.src = sign.resourceData;
      signImage.style.display = "block";
    }
  }

  function mix(a, b, t) {
    return a + (b - a) * t;
  }

  function mergeFrame(frame) {
    return {
      ...basePose,
      ...frame,
      left: frame.left || basePose.left,
      right: frame.right || basePose.right,
      leftShape: frame.leftShape || basePose.leftShape,
      rightShape: frame.rightShape || basePose.rightShape,
      expression: frame.expression || basePose.expression,
      marker: frame.marker || ""
    };
  }

  function poseAt(sign, progress) {
    const frames = sign.frames || signs.reposo.frames;
    let prev = mergeFrame(frames[0]);
    let next = mergeFrame(frames[frames.length - 1]);

    for (let i = 1; i < frames.length; i++) {
      if (progress <= frames[i].p) {
        prev = mergeFrame(frames[i - 1]);
        next = mergeFrame(frames[i]);
        break;
      }
    }

    const span = Math.max(0.001, next.p - prev.p);
    const local = Math.max(0, Math.min(1, (progress - prev.p) / span));
    return {
      left: [mix(prev.left[0], next.left[0], local), mix(prev.left[1], next.left[1], local)],
      right: [mix(prev.right[0], next.right[0], local), mix(prev.right[1], next.right[1], local)],
      leftShape: local < 0.5 ? prev.leftShape : next.leftShape,
      rightShape: local < 0.5 ? prev.rightShape : next.rightShape,
      expression: local < 0.5 ? prev.expression : next.expression,
      marker: local < 0.5 ? prev.marker : next.marker,
      letter: next.letter || prev.letter || ""
    };
  }

  function point(pair) {
    return [pair[0] * canvas.width, pair[1] * canvas.height];
  }

  function drawArm(shoulder, hand, side) {
    const sx = shoulder[0];
    const sy = shoulder[1];
    const hx = hand[0];
    const hy = hand[1];
    const bend = side === "left" ? -34 : 34;
    const elbow = [(sx + hx) / 2 + bend, (sy + hy) / 2 + 18];

    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.quadraticCurveTo(elbow[0], elbow[1], hx, hy);
    ctx.stroke();
  }

  function drawHand(center, shape, letter) {
    const x = center[0];
    const y = center[1];
    ctx.fillStyle = "#f3d2b8";
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";

    if (shape === "open" || shape === "palm") {
      for (let i = -2; i <= 2; i++) {
        ctx.beginPath();
        ctx.moveTo(x + i * 5, y - 10);
        ctx.lineTo(x + i * 8, y - 30);
        ctx.stroke();
      }
    } else if (shape === "point") {
      ctx.beginPath();
      ctx.moveTo(x, y - 8);
      ctx.lineTo(x, y - 38);
      ctx.stroke();
    } else if (shape === "thumbUp") {
      ctx.beginPath();
      ctx.moveTo(x - 6, y - 4);
      ctx.lineTo(x - 16, y - 28);
      ctx.stroke();
    } else if (shape === "thumbDown") {
      ctx.beginPath();
      ctx.moveTo(x - 6, y + 4);
      ctx.lineTo(x - 16, y + 30);
      ctx.stroke();
    } else if (shape === "letter") {
      ctx.fillStyle = "#111827";
      ctx.font = "bold 18px Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(letter || "", x, y);
    }
  }

  function drawMarker(marker) {
    if (!marker) return;
    ctx.save();
    ctx.strokeStyle = "#ef4444";
    ctx.fillStyle = "rgba(239, 68, 68, 0.12)";
    ctx.lineWidth = 3;
    if (marker === "chest") {
      ctx.beginPath();
      ctx.arc(canvas.width * 0.50, canvas.height * 0.58, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (marker === "ear") {
      ctx.beginPath();
      ctx.arc(canvas.width * 0.61, canvas.height * 0.25, 18, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (marker === "mouth") {
      ctx.beginPath();
      ctx.arc(canvas.width * 0.54, canvas.height * 0.32, 16, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (marker === "forward") {
      const x = canvas.width * 0.62;
      const y = canvas.height * 0.43;
      ctx.strokeStyle = "#ef4444";
      ctx.beginPath();
      ctx.moveTo(x - 46, y + 18);
      ctx.lineTo(x + 46, y - 18);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x + 46, y - 18);
      ctx.lineTo(x + 27, y - 21);
      ctx.moveTo(x + 46, y - 18);
      ctx.lineTo(x + 34, y - 3);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawFace(expression) {
    const cx = canvas.width * 0.5;
    const cy = canvas.height * 0.23;
    const r = canvas.height * 0.105;

    ctx.strokeStyle = "#111827";
    ctx.fillStyle = "#f8fafc";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#111827";
    ctx.beginPath();
    ctx.arc(cx - r * 0.32, cy - r * 0.10, 4, 0, Math.PI * 2);
    ctx.arc(cx + r * 0.32, cy - r * 0.10, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 3;
    ctx.beginPath();
    if (expression === "smile") {
      ctx.arc(cx, cy + r * 0.12, r * 0.35, 0.12 * Math.PI, 0.88 * Math.PI);
    } else if (expression === "sad") {
      ctx.arc(cx, cy + r * 0.48, r * 0.35, 1.12 * Math.PI, 1.88 * Math.PI);
    } else if (expression === "focus") {
      ctx.moveTo(cx - r * 0.30, cy + r * 0.32);
      ctx.lineTo(cx + r * 0.30, cy + r * 0.32);
    } else {
      ctx.moveTo(cx - r * 0.25, cy + r * 0.28);
      ctx.lineTo(cx + r * 0.25, cy + r * 0.28);
    }
    ctx.stroke();
  }

  function drawAvatar(pose) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const shoulderLeft = [canvas.width * 0.42, canvas.height * 0.45];
    const shoulderRight = [canvas.width * 0.58, canvas.height * 0.45];
    const handLeft = point(pose.left);
    const handRight = point(pose.right);

    drawMarker(pose.marker);
    drawArm(shoulderLeft, handLeft, "left");
    drawArm(shoulderRight, handRight, "right");

    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(canvas.width * 0.40, canvas.height * 0.78);
    ctx.quadraticCurveTo(canvas.width * 0.40, canvas.height * 0.48, canvas.width * 0.50, canvas.height * 0.48);
    ctx.quadraticCurveTo(canvas.width * 0.60, canvas.height * 0.48, canvas.width * 0.60, canvas.height * 0.78);
    ctx.stroke();

    drawFace(pose.expression);
    drawHand(handLeft, pose.leftShape, pose.letter);
    drawHand(handRight, pose.rightShape, pose.letter);
  }

  function tick(now) {
    if (activeSign) {
      const elapsed = now - activeStarted;
      if (activeSign.resourceData) {
        if (activeSign.resourceTipo === "imagen" && elapsed >= activeSign.duration) {
          activeSign = null;
          startNextSign();
        }
        requestAnimationFrame(tick);
        return;
      }

      const progress = Math.min(1, elapsed / activeSign.duration);
      lastPose = poseAt(activeSign, progress);
      drawAvatar(lastPose);
      if (progress >= 1) {
        activeSign = null;
        startNextSign();
      }
    } else {
      const breath = Math.sin(now / 900) * 0.008;
      const idlePose = {
        ...basePose,
        left: [basePose.left[0], basePose.left[1] + breath],
        right: [basePose.right[0], basePose.right[1] + breath]
      };
      lastPose = idlePose;
      drawAvatar(idlePose);
    }
    requestAnimationFrame(tick);
  }

  function configureLiveRecognition() {
    if (!liveMode) {
      startLiveButton.style.display = "none";
      stopLiveButton.style.display = "none";
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      startLiveButton.disabled = true;
      stopLiveButton.disabled = true;
      statusEl.textContent = "Reconocimiento en vivo no disponible en este navegador";
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "es-CO";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      statusEl.textContent = "Escuchando voz en vivo";
      startLiveButton.disabled = true;
      stopLiveButton.disabled = false;
    };

    recognition.onend = () => {
      startLiveButton.disabled = false;
      stopLiveButton.disabled = true;
      if (!activeSign && !queue.length) statusEl.textContent = "Avatar listo";
    };

    recognition.onerror = (event) => {
      statusEl.textContent = "No se pudo escuchar: " + (event.error || "error");
    };

    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += " " + transcript;
        else interim += " " + transcript;
      }

      liveTextEl.textContent = (finalText || interim).trim();
      if (finalText.trim()) enqueueText(finalText);
    };

    stopLiveButton.disabled = true;
  }

  playButton.disabled = !sequence.length;
  playButton.addEventListener("click", playSequence);
  startLiveButton.addEventListener("click", () => recognition && recognition.start());
  stopLiveButton.addEventListener("click", () => recognition && recognition.stop());
  configureLiveRecognition();
  drawAvatar(basePose);
  if (autoPlay && sequence.length) {
    setTimeout(playSequence, 250);
  }
  requestAnimationFrame(tick);
})();
</script>
"""
