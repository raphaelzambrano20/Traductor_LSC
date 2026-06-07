import * as THREE from 'three';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';

// ─── State ────────────────────────────────────────────────────────────────────
const S = {
  scene: null, camera: null, renderer: null, model: null,
  bones: {},
  restQ: {},        // bone quaternion saved after neutral arm pose
  restWorldDir: {}, // world direction bone→child, saved after neutral arm pose
  fromQ: {},
  targetQ: {},
  currentQ: {},
  pendingPose: null,
  slerpAlpha: 1,
  armLens: {},
  fingerLens: {},   // longitud real de cada hueso de dedo (calculada desde el modelo)
};
let _prevT = 0;
const SLERP_DUR = 0.45;

// ─── Bone patterns ────────────────────────────────────────────────────────────
const BONE_PATTERNS = [
  ['head',      /Head$/i],
  ['neck',      /Neck$/i],
  ['spine2',    /Spine2$/i],
  ['spine1',    /Spine1$/i],
  ['rShoulder', /RightShoulder$/i],
  ['rArm',      /RightArm$/i],
  ['rForeArm',  /RightForeArm$/i],
  ['rHand',     /RightHand$/i],
  ['lShoulder', /LeftShoulder$/i],
  ['lArm',      /LeftArm$/i],
  ['lForeArm',  /LeftForeArm$/i],
  ['lHand',     /LeftHand$/i],
  ['rThumb1',   /RightHandThumb1$/i],  ['rThumb2',  /RightHandThumb2$/i],
  ['rThumb3',   /RightHandThumb3$/i],
  ['rIndex1',   /RightHandIndex1$/i],  ['rIndex2',  /RightHandIndex2$/i],
  ['rIndex3',   /RightHandIndex3$/i],
  ['rMiddle1',  /RightHandMiddle1$/i], ['rMiddle2', /RightHandMiddle2$/i],
  ['rMiddle3',  /RightHandMiddle3$/i],
  ['rRing1',    /RightHandRing1$/i],   ['rRing2',   /RightHandRing2$/i],
  ['rRing3',    /RightHandRing3$/i],
  ['rPinky1',   /RightHandPinky1$/i],  ['rPinky2',  /RightHandPinky2$/i],
  ['rPinky3',   /RightHandPinky3$/i],
  ['lThumb1',   /LeftHandThumb1$/i],   ['lThumb2',  /LeftHandThumb2$/i],
  ['lThumb3',   /LeftHandThumb3$/i],
  ['lIndex1',   /LeftHandIndex1$/i],   ['lIndex2',  /LeftHandIndex2$/i],
  ['lIndex3',   /LeftHandIndex3$/i],
  ['lMiddle1',  /LeftHandMiddle1$/i],  ['lMiddle2', /LeftHandMiddle2$/i],
  ['lMiddle3',  /LeftHandMiddle3$/i],
  ['lRing1',    /LeftHandRing1$/i],    ['lRing2',   /LeftHandRing2$/i],
  ['lRing3',    /LeftHandRing3$/i],
  ['lPinky1',   /LeftHandPinky1$/i],   ['lPinky2',  /LeftHandPinky2$/i],
  ['lPinky3',   /LeftHandPinky3$/i],
];

// Known child bone key for each bone — avoids picking twist/roll bones by accident
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

// Each finger bone direction = direction from landmark[i] to landmark[j]
const FINGER_DEFS = [
  ['Thumb1',  1,2], ['Thumb2',  2,3], ['Thumb3',  3,4],
  ['Index1',  5,6], ['Index2',  6,7], ['Index3',  7,8],
  ['Middle1', 9,10],['Middle2',10,11],['Middle3',11,12],
  ['Ring1',  13,14],['Ring2',  14,15],['Ring3',  15,16],
  ['Pinky1', 17,18],['Pinky2', 18,19],['Pinky3', 19,20],
];

// Reference body positions — updated from real bone positions after loading
const REF = {
  noseX: 0, noseY: 1.55, noseZ: 0.10,
  chestY: 1.22,
  rShoulderX: -0.18, lShoulderX: 0.18, shoulderY: 1.40,
  earOffX: 0.09, earY: 1.53,
  mouthY: 1.46, mouthZ: 0.08,
};
const HAND_Z = 0.15;

// Animation state
let _animTimer  = null;
let _onAnimDone = null;

// ─── Public API ───────────────────────────────────────────────────────────────

export function initAvatar(canvasId, onReady) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const W = canvas.width || 400, H = canvas.height || 420;

  S.scene = new THREE.Scene();
  S.scene.background = new THREE.Color(0xdde6f0);

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
  const fill = new THREE.DirectionalLight(0xb8d0ff, 0.45);
  fill.position.set(-2, 1, 1); S.scene.add(fill);

  new FBXLoader().load('/static/models/Avatar.fbx',
    fbx => _onLoaded(fbx, onReady),
    xhr => { if (xhr.total > 0) _setMsg(`Cargando... ${((xhr.loaded/xhr.total)*100)|0}%`); },
    err  => { console.error('[avatar3d]', err); _setMsg('⚠️ Error'); }
  );
  requestAnimationFrame(_loop);
}

export function setPose(poseData) {
  if (!S.model) {
    S.pendingPose = poseData || null;
    return;
  }

  // Snapshot current bone state as SLERP start; default target = rest
  for (const key of Object.keys(S.bones)) {
    S.fromQ[key]   = S.currentQ[key].clone();
    S.targetQ[key] = S.restQ[key].clone();
  }

  if (poseData) {
    // Phase 1: Arm IK — temporarily apply so finger world matrices are correct
    if (poseData.mano_der) _armIK('r', poseData.mano_der[0], poseData.nariz, poseData.pecho);
    if (poseData.mano_izq) _armIK('l', poseData.mano_izq[0], poseData.nariz, poseData.pecho);
    _applyNow(['rArm','rForeArm','lArm','lForeArm']);

    // Phase 2: Finger posing — parent matrices now reflect arm IK position
    if (poseData.mano_der) _poseFingers(poseData.mano_der, 'r', poseData.nariz, poseData.pecho);
    if (poseData.mano_izq) _poseFingers(poseData.mano_izq, 'l', poseData.nariz, poseData.pecho);

    // Restore bones to current state so SLERP starts from there
    for (const [k, bone] of Object.entries(S.bones)) bone.quaternion.copy(S.currentQ[k]);
    S.model.updateMatrixWorld(false);
  }

  S.slerpAlpha = 0;
}

export function clearPose() { setPose(null); }

// ─── Animation playback (normalized dataset) ──────────────────────────────────

/**
 * Reproduce la secuencia completa de frames del nuevo dataset normalizado.
 * onDone() se llama cuando termina la animación (para encolar la siguiente seña).
 */
export function startAnimation(framesData, onDone) {
  stopAnimation();
  if (!framesData || framesData.length === 0) { if (onDone) onDone(); return; }
  _onAnimDone = onDone || null;
  let idx = 0;
  const MS = 50;   // 20 fps de reproducción — equilibrio suavidad/velocidad
  _animTimer = setInterval(() => {
    if (!S.model) { stopAnimation(); return; }
    _setPoseFromFrame(framesData[idx]);
    idx++;
    if (idx >= framesData.length) stopAnimation();
  }, MS);
}

export function stopAnimation() {
  if (_animTimer !== null) { clearInterval(_animTimer); _animTimer = null; }
  const cb = _onAnimDone; _onAnimDone = null;
  if (cb) cb();
}

// ─── Loading ──────────────────────────────────────────────────────────────────

function _onLoaded(fbx, onReady) {
  fbx.scale.setScalar(0.01);
  const box = new THREE.Box3().setFromObject(fbx);
  fbx.position.y -= box.min.y;
  const c = box.getCenter(new THREE.Vector3());
  fbx.position.x -= c.x; fbx.position.z -= c.z;
  fbx.animations = [];
  S.scene.add(fbx); S.model = fbx;

  fbx.traverse(obj => {
    if (!obj.isBone) return;
    for (const [key, pat] of BONE_PATTERNS)
      if (pat.test(obj.name) && !S.bones[key]) { S.bones[key] = obj; break; }
  });
  console.log('[avatar3d] bones:', Object.keys(S.bones).join(', ') || 'NINGUNO — verifica el FBX');

  console.log('[avatar3d] rig listo:', {
    total: Object.keys(S.bones).length,
    rightArm: !!S.bones.rArm,
    rightForeArm: !!S.bones.rForeArm,
    rightHand: !!S.bones.rHand,
    leftArm: !!S.bones.lArm,
    leftForeArm: !!S.bones.lForeArm,
    leftHand: !!S.bones.lHand,
  });

  fbx.updateMatrixWorld(true);
  _commitRest();           // save T-pose as initial rest
  _computeRefs();          // compute nose/ear/chest from real bone positions
  _computeArmLengths();
  _computeFingerLengths(); // compute real bone length for each finger segment
  _neutralArms();          // bajar brazos a posicion natural de senas
  _commitRest();           // guardar posicion neutra como reposo base
  _addRefMarkers();        // show colored spheres at reference points

  document.getElementById('avatar-loading')?.style.setProperty('display', 'none');
  if (onReady) onReady();
  if (S.pendingPose) {
    const pose = S.pendingPose;
    S.pendingPose = null;
    setPose(pose);
  }
}

// Save all bone quaternions + world directions as "rest"
function _commitRest() {
  S.model.updateMatrixWorld(true);
  for (const [key, bone] of Object.entries(S.bones)) {
    S.restQ[key]    = bone.quaternion.clone();
    S.currentQ[key] = bone.quaternion.clone();
    S.targetQ[key]  = bone.quaternion.clone();
    S.fromQ[key]    = bone.quaternion.clone();
    S.restWorldDir[key] = _boneWorldDir(bone, key);
  }
}

// Compute real body reference positions from skeleton bones
function _computeRefs() {
  S.model.updateMatrixWorld(true);
  const wp = key => { const v = new THREE.Vector3(); S.bones[key]?.getWorldPosition(v); return v; };

  const head   = wp('head');
  const spine1 = wp('spine1');
  const spine2 = wp('spine2');

  if (head.y > 0.5) {
    // Head bone in Mixamo = base of skull (atlas/C1 level ≈ chin height).
    // Face features sit well above that bone:
    REF.noseX   = head.x;           // centro horizontal del modelo
    REF.noseY   = head.y + 0.09;   // nose ≈ mid-face
    REF.noseZ   = head.z + 0.11;
    REF.earY    = head.y + 0.09;   // ears
    REF.earOffX = 0.09;
    REF.mouthY  = head.y + 0.05;   // mouth
    REF.mouthZ  = head.z + 0.11;
  }
  // spine1 = lumbar/mid-back, spine2 = upper thoracic ≈ real chest level
  if (spine2.y > 0.3) {
    REF.chestY = spine2.y;
  } else if (spine1.y > 0.3) {
    REF.chestY = spine1.y + 0.18;
  }

  // Hombros — usar rArm/lArm (articulacion real del brazo, no la clavicula rShoulder)
  const rArm = new THREE.Vector3(); S.bones['rArm']?.getWorldPosition(rArm);
  const lArm = new THREE.Vector3(); S.bones['lArm']?.getWorldPosition(lArm);
  if (rArm.y > 0.3 && lArm.y > 0.3) {
    REF.rShoulderX = rArm.x;
    REF.lShoulderX = lArm.x;
    REF.shoulderY  = (rArm.y + lArm.y) / 2;
  }

  console.log('[avatar3d] refs — narizY:', REF.noseY.toFixed(3),
              'pechoY:', REF.chestY.toFixed(3),
              'hombrosY:', REF.shoulderY.toFixed(3),
              'rShoulderX:', REF.rShoulderX.toFixed(3));
}

// Add visible colored spheres at key body reference points
function _addRefMarkers() {
  const geo = new THREE.SphereGeometry(0.018, 8, 8);
  const add = (x, y, z, color, label) => {
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, depthTest: false }));
    m.position.set(x, y, z);
    m.renderOrder = 999;
    m.name = 'ref_' + label;
    S.scene.add(m);
  };
  const h = S.bones.head ? (() => { const v = new THREE.Vector3(); S.bones.head.getWorldPosition(v); return v; })() : new THREE.Vector3(0, REF.noseY, 0);

  add(h.x,               REF.noseY,    REF.noseZ,   0xff0000, 'nariz');   // rojo   = nariz  → BGR(0,0,255)
  add(h.x,               REF.mouthY,   REF.mouthZ,  0xffaa00, 'boca');    // naranja= boca   → BGR(0,170,255)
  add(h.x + REF.earOffX, REF.earY,     h.z,         0x00d0ff, 'oreja_l');// cyan   = oreja  → BGR(255,208,0)
  add(h.x - REF.earOffX, REF.earY,     h.z,         0x00d0ff, 'oreja_r');// cyan   = oreja  → BGR(255,208,0)
  add(h.x,               REF.chestY,   h.z + 0.05,  0x44ff88, 'pecho');  // verde  = pecho  → BGR(136,255,68)
  // Hombros — usar rArm/lArm (articulacion real del brazo, no la clavicula)
  const rArmWP = new THREE.Vector3(); S.bones['rArm']?.getWorldPosition(rArmWP);
  const lArmWP = new THREE.Vector3(); S.bones['lArm']?.getWorldPosition(lArmWP);
  if (rArmWP.y > 0.1) {
    add(rArmWP.x, rArmWP.y, rArmWP.z + 0.04, 0xff7700, 'hombro_r');
    add(lArmWP.x, lArmWP.y, lArmWP.z + 0.04, 0xff7700, 'hombro_l');
  }
}

function _computeArmLengths() {
  S.model.updateMatrixWorld(true);
  const wp = k => { const v = new THREE.Vector3(); S.bones[k]?.getWorldPosition(v); return v; };
  if (S.bones['rArm'] && S.bones['rForeArm'] && S.bones['rHand']) {
    S.armLens.rU = wp('rArm').distanceTo(wp('rForeArm'));
    S.armLens.rF = wp('rForeArm').distanceTo(wp('rHand'));
  }
  if (S.bones['lArm'] && S.bones['lForeArm'] && S.bones['lHand']) {
    S.armLens.lU = wp('lArm').distanceTo(wp('lForeArm'));
    S.armLens.lF = wp('lForeArm').distanceTo(wp('lHand'));
  }
}

// Compute the world-space length of every finger bone segment from the loaded model.
// Used later in _poseFingers to estimate the Z depth via Pythagorean theorem.
function _computeFingerLengths() {
  S.model.updateMatrixWorld(true);
  const wp = k => { const v = new THREE.Vector3(); S.bones[k]?.getWorldPosition(v); return v; };

  for (const [suffix] of FINGER_DEFS) {
    for (const side of ['r', 'l']) {
      const boneKey  = side + suffix;
      const childKey = BONE_CHILD_KEY[boneKey];
      const bone     = S.bones[boneKey];
      const child    = childKey
        ? S.bones[childKey]
        : Array.from(bone?.children ?? []).find(c => c.isBone);
      if (!bone || !child) continue;
      const a = wp(boneKey);
      const b = new THREE.Vector3(); child.getWorldPosition(b);
      const len = a.distanceTo(b);
      if (len > 1e-4) S.fingerLens[boneKey] = len;
    }
  }
  console.log('[avatar3d] fingerLens rIndex1:', S.fingerLens['rIndex1']?.toFixed(4),
                                  'rThumb1:', S.fingerLens['rThumb1']?.toFixed(4));
}

// Lower arms from T-pose to natural signing position using world-space directions.
// This method works for any Mixamo model regardless of bone local axis orientation.
function _neutralArms() {
  // Model faces +Z (camera). Right arm T-pose = -X direction, left = +X.
  // Neutral signing: each arm goes slightly outward, down and forward.
  _setBoneWorldDir('rArm',    new THREE.Vector3(-0.35, -0.80, 0.35).normalize());
  _applyNow(['rArm']); S.model.updateMatrixWorld(true);

  _setBoneWorldDir('rForeArm', new THREE.Vector3(-0.10, -0.72, 0.52).normalize());
  _applyNow(['rForeArm']); S.model.updateMatrixWorld(true);

  _setBoneWorldDir('lArm',    new THREE.Vector3( 0.35, -0.80, 0.35).normalize());
  _applyNow(['lArm']); S.model.updateMatrixWorld(true);

  _setBoneWorldDir('lForeArm', new THREE.Vector3( 0.10, -0.72, 0.52).normalize());
  _applyNow(['lForeArm']); S.model.updateMatrixWorld(true);
}

// ─── Core bone rotation: axis-independent, uses CURRENT world state ───────────
// Rotates boneKey so it points in targetWorldDir.
// Uses actual current world direction (not cached rest dir) so it works correctly
// even when parent bones have moved.

function _setBoneWorldDir(boneKey, targetWorldDir) {
  const bone = S.bones[boneKey];
  if (!bone) return;

  const currentDir = _boneWorldDir(bone, boneKey);
  if (!currentDir) return;

  const targetDir = targetWorldDir.clone().normalize();
  const dot = THREE.MathUtils.clamp(currentDir.dot(targetDir), -1, 1);
  if (dot > 0.9999) {
    S.targetQ[boneKey] = bone.quaternion.clone();
    return;
  }

  // World-space delta: rotation that takes currentDir → targetDir
  const worldDelta = new THREE.Quaternion().setFromUnitVectors(currentDir, targetDir);

  // Convert to parent-local space: localDelta = parentWorldQ⁻¹ · worldDelta · parentWorldQ
  const parentWorldQ = new THREE.Quaternion();
  if (bone.parent) bone.parent.getWorldQuaternion(parentWorldQ);
  const localDelta = parentWorldQ.clone().invert()
    .multiply(worldDelta)
    .multiply(parentWorldQ);

  // Apply to bone's current local quaternion, save target, then restore
  const originalQ = bone.quaternion.clone();
  bone.quaternion.multiplyQuaternions(localDelta, bone.quaternion);
  S.targetQ[boneKey] = bone.quaternion.clone();
  bone.quaternion.copy(originalQ);
  S.model.updateMatrixWorld(true);
}

// World-space direction from bone to its known child (or first bone child as fallback)
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
  for (const k of keys) {
    const bone = S.bones[k];
    if (bone && S.targetQ[k]) bone.quaternion.copy(S.targetQ[k]);
  }
  S.model.updateMatrixWorld(true);
}

// ─── Conversión coordenadas normalizadas → mundo 3D ──────────────────────────
// Los datos del nuevo dataset (capturar_avatar.py) están normalizados:
//   origen = nariz, escala = 1 unidad = dist(nariz-pecho), Y positivo = arriba
// Esta función los convierte al espacio mundo del modelo Three.js.

function _normToWorld(normPt) {
  const bodyScale = REF.noseY - REF.chestY;
  return new THREE.Vector3(
    REF.noseX + normPt[0] * bodyScale,
    REF.noseY + normPt[1] * bodyScale,
    REF.noseZ + (normPt[2] || 0) * bodyScale
  );
}

// ─── Two-bone arm IK (base) ───────────────────────────────────────────────────

function _armIKWorld(side, wrist3D) {
  const armKey = side + 'Arm', foreKey = side + 'ForeArm';
  const armBone = S.bones[armKey], foreBone = S.bones[foreKey];
  if (!armBone || !foreBone) return;

  armBone.parent.updateWorldMatrix(true, false);
  const shoulder = new THREE.Vector3();
  armBone.parent.getWorldPosition(shoulder);

  const L1 = (side === 'r' ? S.armLens.rU : S.armLens.lU) || 0.28;
  const L2 = (side === 'r' ? S.armLens.rF : S.armLens.lF) || 0.24;

  const toWrist = wrist3D.clone().sub(shoulder);
  const d = Math.min(toWrist.length(), L1 + L2 - 0.001);
  const dir = toWrist.clone().normalize();

  const cosA = Math.max(-1, Math.min(1, (d*d + L1*L1 - L2*L2) / (2*d*L1)));
  const A = Math.acos(cosA);

  // Hint adaptativo según altura del objetivo:
  //   encima del hombro (hola, señas altas) → codo adelante (+Z)
  //   debajo del hombro (bien, señas normales) → codo apenas atrás (-0.15)
  // Evita que el brazo rodee el cuerpo en cualquier caso.
  const sideX = side === 'r' ? 0.6 : -0.6;
  const aboveShoulder = wrist3D.y > shoulder.y + 0.05;
  const hintZ = aboveShoulder ? 0.3 : -0.15;
  const hint = new THREE.Vector3(sideX, -0.4, hintZ).normalize();
  const perp = dir.clone().cross(hint).cross(dir).normalize();

  const elbowPos = shoulder.clone()
    .addScaledVector(dir, L1 * Math.cos(A))
    .addScaledVector(perp, L1 * Math.sin(A));

  _setBoneWorldDir(armKey, elbowPos.clone().sub(shoulder).normalize());
  _applyNow([armKey]);

  const elbowWorld = new THREE.Vector3();
  foreBone.getWorldPosition(elbowWorld);
  _setBoneWorldDir(foreKey, wrist3D.clone().sub(elbowWorld).normalize());
}

// IK desde dataset viejo (2D + nariz/pecho)
function _armIK(side, wrist2D, nariz, pecho) {
  _armIKWorld(side, _cam3D(wrist2D, nariz, pecho));
}

// IK desde dataset nuevo (coordenadas normalizadas) — solo muñeca, codo por hint
function _armIKNorm(side, wristNorm) {
  _armIKWorld(side, _normToWorld(wristNorm));
}

// IK directo usando posición EXACTA del codo capturado.
// Elimina el hint genérico: el brazo se dobla exactamente como en la captura.
function _armIKDirect(side, elbowNorm, wristNorm) {
  const armKey = side + 'Arm', foreKey = side + 'ForeArm';
  const armBone = S.bones[armKey], foreBone = S.bones[foreKey];
  if (!armBone || !foreBone) { _armIKNorm(side, wristNorm); return; }

  armBone.parent.updateWorldMatrix(true, false);
  const shoulder = new THREE.Vector3();
  armBone.parent.getWorldPosition(shoulder);

  const elbowWorld = _normToWorld(elbowNorm);
  const wristWorld = _normToWorld(wristNorm);

  // Brazo superior: shoulder → codo (dirección real capturada)
  _setBoneWorldDir(armKey, elbowWorld.clone().sub(shoulder).normalize());
  _applyNow([armKey]);
  S.model.updateMatrixWorld(true);

  // Antebrazo: posición real del hueso codo → muñeca capturada
  const elbowBonePos = new THREE.Vector3();
  foreBone.getWorldPosition(elbowBonePos);
  _setBoneWorldDir(foreKey, wristWorld.clone().sub(elbowBonePos).normalize());
  // foreKey se aplica con _applyNow global en _setPoseFromFrame
}

// ─── Finger posing desde coordenadas normalizadas ─────────────────────────────

function _poseFingersNorm(ptsNorm, side) {
  if (!ptsNorm || ptsNorm.length < 21) return;

  const pts3D = ptsNorm.map(p => p ? _normToWorld(p) : null);

  // Orientar muñeca según dirección general de la mano
  const wristKey = side + 'Hand';
  if (S.bones[wristKey] && pts3D[0] && pts3D[9]) {
    const handDir = pts3D[9].clone().sub(pts3D[0]);
    const xyLen = Math.hypot(handDir.x, handDir.y);
    // Detectar si la palma mira hacia la cámara o hacia atrás
    const p5 = ptsNorm[5], p17 = ptsNorm[17];
    let palmZ = 1.0;
    if (p5 && p17) {
      const spread = (side === 'r') ? (p17[0] - p5[0]) : (p5[0] - p17[0]);
      palmZ = spread >= 0 ? 1.0 : -1.0;
    }
    handDir.z += palmZ * xyLen * 0.25;
    if (handDir.length() > 1e-4) {
      _setBoneWorldDir(wristKey, handDir.normalize());
      _applyNow([wristKey]);
      S.model.updateMatrixWorld(true);
    }
  }

  // Huesos de cada dedo
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

// ─── Aplicar un frame del nuevo dataset al avatar ────────────────────────────

function _setPoseFromFrame(frame) {
  if (!S.model) return;

  // Snapshot: SLERP parte desde la pose actual, objetivo = reposo
  for (const key of Object.keys(S.bones)) {
    S.fromQ[key]   = S.currentQ[key].clone();
    S.targetQ[key] = S.restQ[key].clone();
  }

  // ── Asignación de brazo por POSICIÓN del muñeca ──────────────────────────
  // En coordenadas normalizadas del dataset:
  //   norm_x < 0 → muñeca a la IZQUIERDA del frame → lado DERECHO del avatar (-X mundo)
  //   norm_x > 0 → muñeca a la DERECHA del frame  → lado IZQUIERDO del avatar (+X mundo)
  // Esto es robusto ante cualquier variación en las etiquetas der/izq del JSON.
  const pts_a = frame.der && frame.der.length >= 21 ? frame.der : null;
  const pts_b = frame.izq && frame.izq.length >= 21 ? frame.izq : null;
  let ptsR = null, ptsL = null;

  for (const pts of [pts_a, pts_b].filter(Boolean)) {
    if (pts[0][0] <= 0) ptsR = pts;  // norm_x ≤ 0 → brazo derecho del avatar
    else                ptsL = pts;  // norm_x > 0 → brazo izquierdo del avatar
  }

  // Fase 1: IK de brazos
  // codo_der/izq → IK directo con posición real del codo.
  // El landmark z=0 de la mano (sistema relativo a muñeca) NO es comparable
  // al z del codo (sistema de cuerpo/pose). Se usa:
  //   - ref.muneca_der/izq si existe (pose wrist, z correcto)
  //   - si no, se toma el z del codo como estimado de profundidad de muñeca
  const ref = frame.ref || {};
  if (ptsR) {
    if (ref.codo_der) {
      const wristIK = ref.muneca_der
        ? ref.muneca_der
        : [ptsR[0][0], ptsR[0][1], ref.codo_der[2]];
      _armIKDirect('r', ref.codo_der, wristIK);
    } else {
      _armIKNorm('r', ptsR[0]);
    }
  }
  if (ptsL) {
    if (ref.codo_izq) {
      const wristIK = ref.muneca_izq
        ? ref.muneca_izq
        : [ptsL[0][0], ptsL[0][1], ref.codo_izq[2]];
      _armIKDirect('l', ref.codo_izq, wristIK);
    } else {
      _armIKNorm('l', ptsL[0]);
    }
  }
  _applyNow(['rArm','rForeArm','lArm','lForeArm']);

  // Fase 2: dedos (matrices de brazo ya actualizadas)
  if (ptsR) _poseFingersNorm(ptsR, 'r');
  if (ptsL) _poseFingersNorm(ptsL, 'l');

  // Restaurar y lanzar SLERP corto (80ms) para animación fluida
  for (const [k, bone] of Object.entries(S.bones)) bone.quaternion.copy(S.currentQ[k]);
  S.model.updateMatrixWorld(false);
  S._slerpDur = 0.08;   // SLERP rápido para seguir la animación de cerca
  S.slerpAlpha = 0;
}

function _cam3D(pt2D, nariz, pecho) {
  const camDY = (nariz && pecho) ? Math.abs(pecho[1] - nariz[1]) : 0.12;
  const scale  = (REF.noseY - REF.chestY) / Math.max(camDY, 0.04);
  const cx = nariz ? nariz[0] : 0.5;
  const cy = nariz ? nariz[1] : 0.35;

  // Z base: manos claramente delante del cuerpo
  const zBase = REF.noseZ + 0.22;

  // Si el landmark incluye Z de MediaPipe (pt2D[2]):
  // MediaPipe Z < 0 → dedo hacia la cámara (+Z mundo)
  // MediaPipe Z > 0 → dedo hacia atrás (−Z mundo)
  // Se escala igual que X/Y para mantener proporciones reales del dedo.
  const zOffset = (pt2D.length >= 3) ? (-pt2D[2] * scale) : 0;

  return new THREE.Vector3(
    (pt2D[0] - cx) * scale,
    REF.noseY - (pt2D[1] - cy) * scale * 0.5,
    zBase + zOffset
  );
}

// ─── Finger posing ────────────────────────────────────────────────────────────

function _poseFingers(pts2D, side, nariz, pecho) {
  if (!pts2D || pts2D.length < 21) return;

  // Convert all 21 landmarks to 3D (initially all share the same Z plane)
  const pts3D = pts2D.map(p => p ? _cam3D(p, nariz, pecho) : null);

  // ── Step 1: Estimate palm-facing direction ──────────────────────────────────
  // When signer's RIGHT hand faces camera (non-mirrored coords):
  //   index base (5) is to the LEFT of pinky base (17) → p5[0] < p17[0]
  // When signer's LEFT hand faces camera: opposite.
  // palmZ = +1 → palm toward camera (fingers extend +Z)
  // palmZ = -1 → back of hand toward camera (fingers extend -Z)
  let palmZ = 1.0;
  const p5 = pts2D[5], p17 = pts2D[17];
  if (p5 && p17) {
    const spread = (side === 'r') ? (p17[0] - p5[0]) : (p5[0] - p17[0]);
    palmZ = spread >= 0 ? 1.0 : -1.0;
  }

  // ── Step 2: Orient wrist bone to match overall hand direction ───────────────
  // This aligns the "root" of all fingers before posing each one.
  const wristKey = side + 'Hand';
  if (S.bones[wristKey] && pts3D[0] && pts3D[9]) {
    const handDir = pts3D[9].clone().sub(pts3D[0]); // wrist → middle MCP
    const xyLen = Math.hypot(handDir.x, handDir.y);
    handDir.z += palmZ * xyLen * 0.25; // tilt wrist toward/away camera
    if (handDir.length() > 1e-4) {
      _setBoneWorldDir(wristKey, handDir.normalize());
      _applyNow([wristKey]);
      S.model.updateMatrixWorld(true);
    }
  }

  // ── Step 3: Pose each finger bone ───────────────────────────────────────────
  // pts3D ya incluye el Z real de MediaPipe (profundidad por dedo).
  // La dirección 3D del segmento captura curvaturas y extensiones correctamente.
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

// ─── Render loop ──────────────────────────────────────────────────────────────

function _loop(t) {
  requestAnimationFrame(_loop);
  const dt = Math.min((t - _prevT) / 1000, 0.05);
  _prevT = t;

  if (S.model && S.slerpAlpha < 1) {
    const dur = S._slerpDur || SLERP_DUR;
    S.slerpAlpha = Math.min(1, S.slerpAlpha + dt / dur);
    if (S.slerpAlpha >= 1) S._slerpDur = null;  // reset a duración normal
    const e = S.slerpAlpha < 0.5
      ? 2 * S.slerpAlpha * S.slerpAlpha
      : -1 + (4 - 2 * S.slerpAlpha) * S.slerpAlpha;

    for (const [key, bone] of Object.entries(S.bones)) {
      if (!S.fromQ[key] || !S.targetQ[key]) continue;
      S.currentQ[key] = S.fromQ[key].clone().slerp(S.targetQ[key], e);
      bone.quaternion.copy(S.currentQ[key]);
    }
    S.model.updateMatrixWorld(false);
  }

  S.renderer?.render(S.scene, S.camera);
}

function _setMsg(txt) {
  const el = document.getElementById('avatar-loading');
  if (el) el.textContent = txt;
}
