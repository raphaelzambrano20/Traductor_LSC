import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

// ─── Estado ───────────────────────────────────────────────────────────────────
const S = {
  scene: null, camera: null, renderer: null,
  vrm: null, model: null,
  bones: {},
  restQ: {}, fromQ: {}, targetQ: {}, currentQ: {},
  slerpAlpha: 1, _slerpDur: null,
  pendingPose: null,
  armLens: {}, fingerLens: {},
  // Expresiones faciales
  exprTarget: {}, exprFrom: {}, exprAlpha: 1, _exprDur: 0.35,
  // Parpadeo automático
  _blinkT: 0, _blinkInterval: 4.0, _blinkPhase: 0,
};

let _prevT = 0;
const SLERP_DUR = 0.45;
let _animTimer = null;
let _onAnimDone = null;

// ─── Mapeo de huesos VRM 1.0 humanoid ────────────────────────────────────────
// Clave interna → nombre estándar VRM 1.0
// three-vrm v2 normaliza VRM 0.x a estos mismos nombres
const VRM_BONE_MAP = {
  head:     'head',       neck:     'neck',
  spine2:   'upperChest', spine1:   'chest',
  rArm:     'rightUpperArm',  rForeArm: 'rightLowerArm',  rHand: 'rightHand',
  lArm:     'leftUpperArm',   lForeArm: 'leftLowerArm',   lHand: 'leftHand',

  rThumb1:  'rightThumbMetacarpal',   rThumb2: 'rightThumbProximal',    rThumb3: 'rightThumbDistal',
  rIndex1:  'rightIndexProximal',     rIndex2: 'rightIndexIntermediate', rIndex3: 'rightIndexDistal',
  rMiddle1: 'rightMiddleProximal',    rMiddle2:'rightMiddleIntermediate',rMiddle3:'rightMiddleDistal',
  rRing1:   'rightRingProximal',      rRing2:  'rightRingIntermediate',  rRing3:  'rightRingDistal',
  rPinky1:  'rightLittleProximal',    rPinky2: 'rightLittleIntermediate',rPinky3: 'rightLittleDistal',

  lThumb1:  'leftThumbMetacarpal',    lThumb2: 'leftThumbProximal',     lThumb3: 'leftThumbDistal',
  lIndex1:  'leftIndexProximal',      lIndex2: 'leftIndexIntermediate',  lIndex3: 'leftIndexDistal',
  lMiddle1: 'leftMiddleProximal',     lMiddle2:'leftMiddleIntermediate', lMiddle3:'leftMiddleDistal',
  lRing1:   'leftRingProximal',       lRing2:  'leftRingIntermediate',   lRing3:  'leftRingDistal',
  lPinky1:  'leftLittleProximal',     lPinky2: 'leftLittleIntermediate', lPinky3: 'leftLittleDistal',
};

// Hijo canónico por hueso (evita huesos twist/roll en _boneWorldDir)
const BONE_CHILD_KEY = {
  rArm:'rForeArm', rForeArm:'rHand',
  lArm:'lForeArm', lForeArm:'lHand',
  rThumb1:'rThumb2', rThumb2:'rThumb3',
  rIndex1:'rIndex2', rIndex2:'rIndex3',
  rMiddle1:'rMiddle2', rMiddle2:'rMiddle3',
  rRing1:'rRing2', rRing2:'rRing3',
  rPinky1:'rPinky2', rPinky2:'rPinky3',
  lThumb1:'lThumb2', lThumb2:'lThumb3',
  lIndex1:'lIndex2', lIndex2:'lIndex3',
  lMiddle1:'lMiddle2', lMiddle2:'lMiddle3',
  lRing1:'lRing2', lRing2:'lRing3',
  lPinky1:'lPinky2', lPinky2:'lPinky3',
};

// Segmentos de dedo: [sufijo, landmark_desde, landmark_hasta]
const FINGER_DEFS = [
  ['Thumb1',  1,2], ['Thumb2',  2,3], ['Thumb3',  3,4],
  ['Index1',  5,6], ['Index2',  6,7], ['Index3',  7,8],
  ['Middle1', 9,10],['Middle2',10,11],['Middle3',11,12],
  ['Ring1',  13,14],['Ring2',  14,15],['Ring3',  15,16],
  ['Pinky1', 17,18],['Pinky2', 18,19],['Pinky3', 19,20],
];

// Posiciones de referencia corporal (se calculan desde los huesos reales al cargar)
const REF = {
  noseX:0, noseY:1.55, noseZ:0.10,
  chestY:1.22,
  rShoulderX:-0.18, lShoulderX:0.18, shoulderY:1.40,
  earOffX:0.09, earY:1.53, mouthY:1.46, mouthZ:0.08,
};

// Expresiones disponibles para SLERP (VRM 1.0 preset names)
const EXPR_NAMES = ['happy', 'sad', 'angry', 'surprised', 'relaxed'];

// ─── API Pública ──────────────────────────────────────────────────────────────

export function initAvatar(canvasId, onReady) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const W = canvas.width || 400, H = canvas.height || 420;

  S.scene = new THREE.Scene();
  S.scene.background = new THREE.Color(0xf5f5f7);

  S.camera = new THREE.PerspectiveCamera(34, W / H, 0.01, 50);
  S.camera.position.set(0, 1.50, 1.65);
  S.camera.lookAt(0, 1.25, 0);

  S.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  S.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  S.renderer.setSize(W, H, false);
  S.renderer.outputColorSpace = THREE.SRGBColorSpace;

  S.scene.add(new THREE.AmbientLight(0xffffff, 0.9));
  const key = new THREE.DirectionalLight(0xfff5e8, 1.3);
  key.position.set(1.5, 4, 3); S.scene.add(key);
  const fill = new THREE.DirectionalLight(0xdfe3ea, 0.5);
  fill.position.set(-2, 1, 1); S.scene.add(fill);

  const loader = new GLTFLoader();
  loader.register(parser => new VRMLoaderPlugin(parser));
  loader.load(
    '/static/models/Avatar_LSC.vrm',
    gltf => _onLoaded(gltf, onReady),
    xhr => { if (xhr.total > 0) _setMsg(`Cargando... ${((xhr.loaded / xhr.total) * 100) | 0}%`); },
    err => { console.error('[avatar3d]', err); _setMsg('⚠️ Error al cargar el avatar'); }
  );
  requestAnimationFrame(_loop);
}

export function setPose(poseData) {
  if (!S.model) { S.pendingPose = poseData || null; return; }
  for (const key of Object.keys(S.bones)) {
    S.fromQ[key]   = S.currentQ[key].clone();
    S.targetQ[key] = S.restQ[key].clone();
  }
  if (poseData) {
    if (poseData.mano_der) _armIK('r', poseData.mano_der[0], poseData.nariz, poseData.pecho);
    if (poseData.mano_izq) _armIK('l', poseData.mano_izq[0], poseData.nariz, poseData.pecho);
    _applyNow(['rArm','rForeArm','lArm','lForeArm']);
    if (poseData.mano_der) _poseFingers(poseData.mano_der, 'r', poseData.nariz, poseData.pecho);
    if (poseData.mano_izq) _poseFingers(poseData.mano_izq, 'l', poseData.nariz, poseData.pecho);
    for (const [k, bone] of Object.entries(S.bones)) bone.quaternion.copy(S.currentQ[k]);
    S.model.updateMatrixWorld(false);
  }
  S.slerpAlpha = 0;
}

export function clearPose() { setPose(null); }

export function startAnimation(framesData, onDone) {
  stopAnimation();
  if (!framesData || framesData.length === 0) { if (onDone) onDone(); return; }
  _onAnimDone = onDone || null;
  let idx = 0;
  _animTimer = setInterval(() => {
    if (!S.model) { stopAnimation(); return; }
    _setPoseFromFrame(framesData[idx++]);
    if (idx >= framesData.length) stopAnimation();
  }, 50); // 20 fps
}

export function stopAnimation() {
  if (_animTimer !== null) { clearInterval(_animTimer); _animTimer = null; }
  const cb = _onAnimDone; _onAnimDone = null;
  if (cb) cb();
}

/**
 * Aplica rotaciones de huesos inmediatamente (sin SLERP) para seguimiento en vivo.
 * Usado por la página de captura con Kalidokit.
 * @param {Object} bonesMap  { vrmBoneName: {x,y,z,w} }
 */
export function applyLiveRotations(bonesMap) {
  if (!S.model) return;
  for (const [key, vrmName] of Object.entries(VRM_BONE_MAP)) {
    const rot = bonesMap[vrmName];
    if (!rot || !S.bones[key]) continue;
    S.bones[key].quaternion.set(rot.x, rot.y, rot.z, rot.w);
    S.currentQ[key] = S.bones[key].quaternion.clone();
    S.targetQ[key]  = S.bones[key].quaternion.clone();
    S.fromQ[key]    = S.bones[key].quaternion.clone();
  }
  S.slerpAlpha = 1; // sin SLERP pendiente
}

/**
 * Devuelve una copia del estado actual de todos los huesos como [qx, qy, qz, qw].
 * Usado por la página de captura para guardar un frame en formato rotaciones_v2.
 * @returns {Object} { vrmBoneName: [qx, qy, qz, qw] }
 */
export function snapshotRotations() {
  const snap = {};
  for (const [key, vrmName] of Object.entries(VRM_BONE_MAP)) {
    const q = S.currentQ[key];
    if (q) snap[vrmName] = [q.x, q.y, q.z, q.w];
  }
  return snap;
}

/**
 * Activa una expresión facial con transición suave.
 * @param {string}  name        Nombre VRM 1.0: 'happy','sad','angry','surprised','relaxed'
 * @param {number}  intensity   0.0 – 1.0
 * @param {number}  durationSecs  Duración de la transición en segundos (default 0.35)
 */
export function setExpression(name, intensity = 1.0, durationSecs = 0.35) {
  if (!S.vrm?.expressionManager) return;
  for (const n of EXPR_NAMES) {
    S.exprFrom[n]   = S.vrm.expressionManager.getValue(n) ?? 0;
    S.exprTarget[n] = (n === name) ? Math.max(0, Math.min(1, intensity)) : 0;
  }
  S.exprAlpha = 0;
  S._exprDur  = Math.max(0.05, durationSecs);
}

/**
 * Vuelve a expresión neutral con transición suave.
 */
export function clearExpression(durationSecs = 0.5) {
  if (!S.vrm?.expressionManager) return;
  for (const n of EXPR_NAMES) {
    S.exprFrom[n]   = S.vrm.expressionManager.getValue(n) ?? 0;
    S.exprTarget[n] = 0;
  }
  S.exprAlpha = 0;
  S._exprDur  = Math.max(0.05, durationSecs);
}

// ─── Carga del modelo ─────────────────────────────────────────────────────────

function _onLoaded(gltf, onReady) {
  const vrm = gltf.userData.vrm;
  if (!vrm) { _setMsg('⚠️ Archivo no reconocido como VRM'); return; }

  S.vrm   = vrm;
  S.model = vrm.scene;

  // VRMUtils.rotateVRM0 rota el modelo 180° en Y para que quede mirando +Z
  // (la cámara está en +Z viendo hacia -Z, así se ve el frente del avatar)
  // Aplica tanto a VRM 0.x como VRM 1.x con esta cámara
  VRMUtils.rotateVRM0(vrm);

  S.scene.add(vrm.scene);

  // Poblar S.bones usando la API humanoid de VRM (huesos reales del grafo de escena)
  for (const [key, vrmName] of Object.entries(VRM_BONE_MAP)) {
    const bone = vrm.humanoid.getRawBoneNode(vrmName);
    if (bone) S.bones[key] = bone;
    else console.warn(`[avatar3d] hueso no encontrado: ${key} → ${vrmName}`);
  }
  console.log(`[avatar3d] huesos: ${Object.keys(S.bones).length} / ${Object.keys(VRM_BONE_MAP).length}`);

  vrm.scene.updateMatrixWorld(true);
  _commitRest();
  _computeRefs();
  _computeArmLengths();
  _computeFingerLengths();
  _neutralArms();
  _commitRest();
  _addRefMarkers();

  document.getElementById('avatar-loading')?.style.setProperty('display', 'none');
  if (onReady) onReady();
  if (S.pendingPose) { const p = S.pendingPose; S.pendingPose = null; setPose(p); }
}

function _commitRest() {
  S.model.updateMatrixWorld(true);
  for (const [key, bone] of Object.entries(S.bones)) {
    S.restQ[key]    = bone.quaternion.clone();
    S.currentQ[key] = bone.quaternion.clone();
    S.targetQ[key]  = bone.quaternion.clone();
    S.fromQ[key]    = bone.quaternion.clone();
  }
}

function _computeRefs() {
  S.model.updateMatrixWorld(true);
  const wp = key => { const v = new THREE.Vector3(); S.bones[key]?.getWorldPosition(v); return v; };

  const head   = wp('head');
  const spine2 = wp('spine2');
  const spine1 = wp('spine1');
  const rArm   = new THREE.Vector3(); S.bones['rArm']?.getWorldPosition(rArm);
  const lArm   = new THREE.Vector3(); S.bones['lArm']?.getWorldPosition(lArm);

  // Para VRM: el hueso head está aproximadamente al nivel de la mandíbula/base del cráneo
  if (head.y > 0.3) {
    REF.noseX   = head.x;
    REF.noseY   = head.y + 0.09;  // nariz ≈ 9cm sobre el hueso head
    REF.noseZ   = head.z + 0.11;
    REF.mouthY  = head.y + 0.04;
    REF.mouthZ  = head.z + 0.11;
    REF.earY    = head.y + 0.08;
    REF.earOffX = 0.09;
  }
  if (spine2.y > 0.3) {
    REF.chestY = spine2.y;
  } else if (spine1.y > 0.3) {
    REF.chestY = spine1.y + 0.18;
  }
  if (rArm.y > 0.3 && lArm.y > 0.3) {
    REF.rShoulderX = rArm.x;
    REF.lShoulderX = lArm.x;
    REF.shoulderY  = (rArm.y + lArm.y) / 2;
  }
  console.log('[avatar3d] refs — nariz:', REF.noseY.toFixed(3),
              'pecho:', REF.chestY.toFixed(3), 'hombroY:', REF.shoulderY.toFixed(3));
}

function _computeArmLengths() {
  S.model.updateMatrixWorld(true);
  const wp = k => { const v = new THREE.Vector3(); S.bones[k]?.getWorldPosition(v); return v; };
  if (S.bones.rArm && S.bones.rForeArm && S.bones.rHand) {
    S.armLens.rU = wp('rArm').distanceTo(wp('rForeArm'));
    S.armLens.rF = wp('rForeArm').distanceTo(wp('rHand'));
  }
  if (S.bones.lArm && S.bones.lForeArm && S.bones.lHand) {
    S.armLens.lU = wp('lArm').distanceTo(wp('lForeArm'));
    S.armLens.lF = wp('lForeArm').distanceTo(wp('lHand'));
  }
}

function _computeFingerLengths() {
  S.model.updateMatrixWorld(true);
  const wp = k => { const v = new THREE.Vector3(); S.bones[k]?.getWorldPosition(v); return v; };
  for (const [suffix] of FINGER_DEFS) {
    for (const side of ['r', 'l']) {
      const key   = side + suffix;
      const child = BONE_CHILD_KEY[key];
      const bone  = S.bones[key];
      const cbone = child ? S.bones[child] : Array.from(bone?.children ?? []).find(c => c.isBone);
      if (!bone || !cbone) continue;
      const len = wp(key).distanceTo(new THREE.Vector3().copy(wp(child || '')));
      if (len > 1e-4) S.fingerLens[key] = len;
    }
  }
}

// Baja los brazos desde la T-pose a una posición natural para señas
function _neutralArms() {
  // El modelo mira en +Z (después de rotateVRM0).
  // Su lado derecho apunta en -X mundo. Los vectores son independientes del eje local.
  _setBoneWorldDir('rArm',    new THREE.Vector3(-0.35, -0.80,  0.35).normalize());
  _applyNow(['rArm']); S.model.updateMatrixWorld(true);
  _setBoneWorldDir('rForeArm', new THREE.Vector3(-0.10, -0.72,  0.52).normalize());
  _applyNow(['rForeArm']); S.model.updateMatrixWorld(true);
  _setBoneWorldDir('lArm',    new THREE.Vector3( 0.35, -0.80,  0.35).normalize());
  _applyNow(['lArm']); S.model.updateMatrixWorld(true);
  _setBoneWorldDir('lForeArm', new THREE.Vector3( 0.10, -0.72,  0.52).normalize());
  _applyNow(['lForeArm']); S.model.updateMatrixWorld(true);
}

function _addRefMarkers() {
  const geo = new THREE.SphereGeometry(0.016, 8, 8);
  const add = (x, y, z, color, label) => {
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, depthTest: false }));
    m.position.set(x, y, z);
    m.renderOrder = 999;
    m.name = 'ref_' + label;
    S.scene.add(m);
  };
  const hx = REF.noseX;
  add(hx,               REF.noseY,   REF.noseZ,  0xff0000, 'nariz');
  add(hx,               REF.mouthY,  REF.mouthZ, 0xffaa00, 'boca');
  add(hx + REF.earOffX, REF.earY,    REF.noseZ,  0x00d0ff, 'oreja_l');
  add(hx - REF.earOffX, REF.earY,    REF.noseZ,  0x00d0ff, 'oreja_r');
  add(hx,               REF.chestY,  REF.noseZ + 0.05, 0x44ff88, 'pecho');
  const rArmWP = new THREE.Vector3(); S.bones['rArm']?.getWorldPosition(rArmWP);
  const lArmWP = new THREE.Vector3(); S.bones['lArm']?.getWorldPosition(lArmWP);
  if (rArmWP.y > 0.1) {
    add(rArmWP.x, rArmWP.y, rArmWP.z + 0.04, 0xff7700, 'hombro_r');
    add(lArmWP.x, lArmWP.y, lArmWP.z + 0.04, 0xff7700, 'hombro_l');
  }
}

// ─── Rotación de huesos: independiente de ejes, usa posición mundo actual ─────

function _setBoneWorldDir(boneKey, targetWorldDir) {
  const bone = S.bones[boneKey];
  if (!bone) return;
  const currentDir = _boneWorldDir(bone, boneKey);
  if (!currentDir) return;
  const targetDir = targetWorldDir.clone().normalize();
  if (currentDir.dot(targetDir) > 0.9999) { S.targetQ[boneKey] = bone.quaternion.clone(); return; }

  const worldDelta = new THREE.Quaternion().setFromUnitVectors(currentDir, targetDir);
  const parentWorldQ = new THREE.Quaternion();
  if (bone.parent) bone.parent.getWorldQuaternion(parentWorldQ);
  const localDelta = parentWorldQ.clone().invert().multiply(worldDelta).multiply(parentWorldQ);

  const origQ = bone.quaternion.clone();
  bone.quaternion.multiplyQuaternions(localDelta, bone.quaternion);
  S.targetQ[boneKey] = bone.quaternion.clone();
  bone.quaternion.copy(origQ);
  S.model.updateMatrixWorld(true);
}

function _boneWorldDir(bone, boneKey) {
  const childKey = boneKey ? BONE_CHILD_KEY[boneKey] : null;
  const child = (childKey && S.bones[childKey])
    ? S.bones[childKey]
    : Array.from(bone.children).find(c => c.isBone);
  if (!child) return null;
  const a = new THREE.Vector3(), b = new THREE.Vector3();
  bone.getWorldPosition(a); child.getWorldPosition(b);
  const d = b.sub(a);
  return d.length() > 1e-5 ? d.normalize() : null;
}

function _applyNow(keys) {
  for (const k of keys) { if (S.bones[k] && S.targetQ[k]) S.bones[k].quaternion.copy(S.targetQ[k]); }
  S.model.updateMatrixWorld(true);
}

// ─── Conversión coordenadas normalizadas → mundo 3D ──────────────────────────
// Los JSONs de data/avatar_movimientos/ tienen coords normalizadas:
//   origen = nariz, escala = 1 unidad = dist(nariz-pecho), Y+ = arriba

function _normToWorld(pt) {
  const scale = REF.noseY - REF.chestY;
  return new THREE.Vector3(
    REF.noseX + pt[0] * scale,
    REF.noseY + pt[1] * scale,
    REF.noseZ + (pt[2] || 0) * scale
  );
}

// ─── IK de brazos (dos huesos) ────────────────────────────────────────────────

function _armIKWorld(side, wrist3D) {
  const armKey = side + 'Arm', foreKey = side + 'ForeArm';
  const armBone = S.bones[armKey], foreBone = S.bones[foreKey];
  if (!armBone || !foreBone) return;

  armBone.parent.updateWorldMatrix(true, false);
  const shoulder = new THREE.Vector3(); armBone.parent.getWorldPosition(shoulder);

  const L1 = (side === 'r' ? S.armLens.rU : S.armLens.lU) || 0.28;
  const L2 = (side === 'r' ? S.armLens.rF : S.armLens.lF) || 0.24;

  const toWrist = wrist3D.clone().sub(shoulder);
  const d = Math.min(toWrist.length(), L1 + L2 - 0.001);
  const dir = toWrist.clone().normalize();

  const cosA = THREE.MathUtils.clamp((d*d + L1*L1 - L2*L2) / (2*d*L1), -1, 1);
  const A = Math.acos(cosA);

  // Hint adaptativo: codo adelante para señas sobre el hombro, levemente atrás para señas bajas
  const aboveShoulder = wrist3D.y > shoulder.y + 0.05;
  const sideX = side === 'r' ? 0.6 : -0.6;
  const hint = new THREE.Vector3(sideX, -0.4, aboveShoulder ? 0.3 : -0.15).normalize();
  const perp = dir.clone().cross(hint).cross(dir).normalize();

  const elbowPos = shoulder.clone()
    .addScaledVector(dir, L1 * Math.cos(A))
    .addScaledVector(perp, L1 * Math.sin(A));

  _setBoneWorldDir(armKey, elbowPos.clone().sub(shoulder).normalize());
  _applyNow([armKey]);

  const elbowWorld = new THREE.Vector3(); foreBone.getWorldPosition(elbowWorld);
  _setBoneWorldDir(foreKey, wrist3D.clone().sub(elbowWorld).normalize());
}

// IK desde dataset antiguo (2D + nariz/pecho en imagen)
function _armIK(side, wrist2D, nariz, pecho) {
  _armIKWorld(side, _cam3D(wrist2D, nariz, pecho));
}

// IK desde dataset normalizado — solo muñeca, codo por hint adaptativo
function _armIKNorm(side, wristNorm) {
  _armIKWorld(side, _normToWorld(wristNorm));
}

// IK directo usando la posición REAL del codo capturado por MediaPipe pose
function _armIKDirect(side, elbowNorm, wristNorm) {
  const armKey = side + 'Arm', foreKey = side + 'ForeArm';
  const armBone = S.bones[armKey], foreBone = S.bones[foreKey];
  if (!armBone || !foreBone) { _armIKNorm(side, wristNorm); return; }

  armBone.parent.updateWorldMatrix(true, false);
  const shoulder = new THREE.Vector3(); armBone.parent.getWorldPosition(shoulder);

  const elbowWorld = _normToWorld(elbowNorm);
  const wristWorld = _normToWorld(wristNorm);

  _setBoneWorldDir(armKey, elbowWorld.clone().sub(shoulder).normalize());
  _applyNow([armKey]);
  S.model.updateMatrixWorld(true);

  const elbowBonePos = new THREE.Vector3(); foreBone.getWorldPosition(elbowBonePos);
  _setBoneWorldDir(foreKey, wristWorld.clone().sub(elbowBonePos).normalize());
}

// ─── Postura de dedos desde coordenadas normalizadas ─────────────────────────

function _poseFingersNorm(ptsNorm, side) {
  if (!ptsNorm || ptsNorm.length < 21) return;

  const pts3D = ptsNorm.map(p => p ? _normToWorld(p) : null);

  // 1. Orientar la muñeca según la dirección general de la mano
  const wristKey = side + 'Hand';
  if (S.bones[wristKey] && pts3D[0] && pts3D[9]) {
    const handDir = pts3D[9].clone().sub(pts3D[0]);
    // Detectar si la palma mira hacia la cámara o hacia atrás
    const p5 = ptsNorm[5], p17 = ptsNorm[17];
    if (p5 && p17) {
      const spread = (side === 'r') ? (p17[0] - p5[0]) : (p5[0] - p17[0]);
      const palmZ = spread >= 0 ? 1.0 : -1.0;
      handDir.z += palmZ * Math.hypot(handDir.x, handDir.y) * 0.25;
    }
    if (handDir.length() > 1e-4) {
      _setBoneWorldDir(wristKey, handDir.normalize());
      _applyNow([wristKey]);
      S.model.updateMatrixWorld(true);
    }
  }

  // 2. Cada segmento de dedo apunta de landmark[i] a landmark[j]
  //    El Z de MediaPipe codifica profundidad: dedo curvado vs extendido
  for (const [suffix, i, j] of FINGER_DEFS) {
    const boneKey = side + suffix;
    if (!S.bones[boneKey]) continue;
    const a = pts3D[i], b = pts3D[j];
    if (!a || !b) continue;
    const dir = b.clone().sub(a);
    if (dir.length() < 1e-4) continue;
    _setBoneWorldDir(boneKey, dir.normalize());
    _applyNow([boneKey]);
    S.model.updateMatrixWorld(true);
  }
}

// Postura de dedos desde dataset antiguo (2D)
function _poseFingers(pts2D, side, nariz, pecho) {
  if (!pts2D || pts2D.length < 21) return;
  const pts3D = pts2D.map(p => p ? _cam3D(p, nariz, pecho) : null);

  const wristKey = side + 'Hand';
  if (S.bones[wristKey] && pts3D[0] && pts3D[9]) {
    const handDir = pts3D[9].clone().sub(pts3D[0]);
    const p5 = pts2D[5], p17 = pts2D[17];
    if (p5 && p17) {
      const spread = (side === 'r') ? (p17[0] - p5[0]) : (p5[0] - p17[0]);
      handDir.z += (spread >= 0 ? 1.0 : -1.0) * Math.hypot(handDir.x, handDir.y) * 0.25;
    }
    if (handDir.length() > 1e-4) {
      _setBoneWorldDir(wristKey, handDir.normalize());
      _applyNow([wristKey]);
      S.model.updateMatrixWorld(true);
    }
  }
  for (const [suffix, i, j] of FINGER_DEFS) {
    const boneKey = side + suffix;
    if (!S.bones[boneKey]) continue;
    const a = pts3D[i], b = pts3D[j];
    if (!a || !b) continue;
    const dir = b.clone().sub(a);
    if (dir.length() < 1e-4) continue;
    _setBoneWorldDir(boneKey, dir.normalize());
    _applyNow([boneKey]);
    S.model.updateMatrixWorld(true);
  }
}

// ─── Aplicar un frame del dataset al avatar ───────────────────────────────────

function _setPoseFromFrame(frame) {
  if (!S.model) return;
  for (const key of Object.keys(S.bones)) {
    S.fromQ[key]   = S.currentQ[key].clone();
    S.targetQ[key] = S.restQ[key].clone();
  }

  if (frame.bones) {
    // Formato v2 (rotaciones_v2): aplica bone.quaternion directamente — sin IK
    for (const [key, vrmName] of Object.entries(VRM_BONE_MAP)) {
      const q = frame.bones[vrmName];
      if (q && S.bones[key])
        S.targetQ[key] = new THREE.Quaternion(q[0], q[1], q[2], q[3]);
    }
  } else {
    // Formato v1 (landmarks): fallback al IK de runtime mientras se recapturan los JSONs
    _setPoseFromFrameV1(frame);
  }

  for (const [k, bone] of Object.entries(S.bones)) bone.quaternion.copy(S.currentQ[k]);
  S.model.updateMatrixWorld(false);
  S._slerpDur = 0.08;
  S.slerpAlpha = 0;
}

// Fallback para JSONs v1 (landmarks + IK) — se elimina cuando todos los JSONs sean v2
function _setPoseFromFrameV1(frame) {
  const pts_a = frame.der && frame.der.length >= 21 ? frame.der : null;
  const pts_b = frame.izq && frame.izq.length >= 21 ? frame.izq : null;
  let ptsR = null, ptsL = null;
  for (const pts of [pts_a, pts_b].filter(Boolean)) {
    if (pts[0][0] <= 0) ptsR = pts;
    else                ptsL = pts;
  }
  const ref = frame.ref || {};
  if (ptsR) {
    if (ref.codo_der) {
      const wristIK = ref.muneca_der || [ptsR[0][0], ptsR[0][1], ref.codo_der[2]];
      _armIKDirect('r', ref.codo_der, wristIK);
    } else { _armIKNorm('r', ptsR[0]); }
  }
  if (ptsL) {
    if (ref.codo_izq) {
      const wristIK = ref.muneca_izq || [ptsL[0][0], ptsL[0][1], ref.codo_izq[2]];
      _armIKDirect('l', ref.codo_izq, wristIK);
    } else { _armIKNorm('l', ptsL[0]); }
  }
  _applyNow(['rArm','rForeArm','lArm','lForeArm']);
  if (ptsR) _poseFingersNorm(ptsR, 'r');
  if (ptsL) _poseFingersNorm(ptsL, 'l');
}

// Convierte landmark 2D del dataset antiguo a 3D en espacio mundo
function _cam3D(pt2D, nariz, pecho) {
  const camDY = (nariz && pecho) ? Math.abs(pecho[1] - nariz[1]) : 0.12;
  const scale = (REF.noseY - REF.chestY) / Math.max(camDY, 0.04);
  const cx = nariz ? nariz[0] : 0.5;
  const cy = nariz ? nariz[1] : 0.35;
  const zBase  = REF.noseZ + 0.22;
  const zOffset = (pt2D.length >= 3) ? (-pt2D[2] * scale) : 0;
  return new THREE.Vector3(
    (pt2D[0] - cx) * scale,
    REF.noseY - (pt2D[1] - cy) * scale * 0.5,
    zBase + zOffset
  );
}

// ─── Parpadeo automático ──────────────────────────────────────────────────────

function _updateBlink(dt) {
  if (!S.vrm?.expressionManager) return;
  S._blinkT += dt;
  if (S._blinkPhase === 0 && S._blinkT >= S._blinkInterval) {
    S._blinkPhase = 1; S._blinkT = 0;
  } else if (S._blinkPhase === 1) {
    const v = Math.min(1, S._blinkT / 0.06); // 60 ms cerrando
    S.vrm.expressionManager.setValue('blink', v);
    if (v >= 1) { S._blinkPhase = 2; S._blinkT = 0; }
  } else if (S._blinkPhase === 2) {
    const v = 1 - Math.min(1, S._blinkT / 0.10); // 100 ms abriendo
    S.vrm.expressionManager.setValue('blink', v);
    if (v <= 0) {
      S.vrm.expressionManager.setValue('blink', 0);
      S._blinkPhase = 0; S._blinkT = 0;
      S._blinkInterval = 3 + Math.random() * 3; // 3–6 segundos hasta el próximo parpadeo
    }
  }
}

// ─── Render loop ──────────────────────────────────────────────────────────────

function _loop(t) {
  requestAnimationFrame(_loop);
  const dt = Math.min((t - _prevT) / 1000, 0.05);
  _prevT = t;

  // SLERP de huesos
  if (S.model && S.slerpAlpha < 1) {
    const dur = S._slerpDur || SLERP_DUR;
    S.slerpAlpha = Math.min(1, S.slerpAlpha + dt / dur);
    if (S.slerpAlpha >= 1) S._slerpDur = null;
    const e = _ease(S.slerpAlpha);
    for (const [key, bone] of Object.entries(S.bones)) {
      if (!S.fromQ[key] || !S.targetQ[key]) continue;
      S.currentQ[key] = S.fromQ[key].clone().slerp(S.targetQ[key], e);
      bone.quaternion.copy(S.currentQ[key]);
    }
    S.model.updateMatrixWorld(false);
  }

  // SLERP de expresiones faciales
  if (S.vrm?.expressionManager) {
    if (S.exprAlpha < 1) {
      S.exprAlpha = Math.min(1, S.exprAlpha + dt / S._exprDur);
      const e = _ease(S.exprAlpha);
      for (const name of EXPR_NAMES) {
        const from = S.exprFrom[name] ?? 0;
        const to   = S.exprTarget[name] ?? 0;
        S.vrm.expressionManager.setValue(name, from + (to - from) * e);
      }
    }
    _updateBlink(dt);
    // Aplica blend shapes al mesh (NO llama humanoid.update — eso sobreescribiría los huesos)
    S.vrm.expressionManager.update(dt);
  }

  S.renderer?.render(S.scene, S.camera);
}

function _ease(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function _setMsg(txt) {
  const el = document.getElementById('avatar-loading');
  if (el) el.textContent = txt;
}
