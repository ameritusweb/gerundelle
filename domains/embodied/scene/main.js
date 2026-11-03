import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildWorld } from './world.js';

const seed = Number(new URLSearchParams(location.search).get('seed') ?? 7);
const layout = Number(new URLSearchParams(location.search).get('layout') ?? 0);
const dataName = layout ? `seed${seed}_layout${layout}` : `seed${seed}`;   // the data files of this view
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const world = buildWorld(seed, layout);
const { scene } = world;
scene.background = new THREE.Color('#d9d4cb');
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.55;

const sun = new THREE.DirectionalLight('#fff3e2', 2.4);   // light from a window to the left
sun.position.set(-0.9, 1.3, 0.4);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -0.8, right: 0.8, top: 0.8, bottom: -0.8, near: 0.1, far: 4 });
sun.shadow.bias = -0.0004;
sun.shadow.radius = 4;
scene.add(sun, new THREE.HemisphereLight('#f4efe6', '#6b5a48', 0.35));

const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.01, 20);
camera.position.set(0.05, 0.5, 0.78);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(-0.04, 0.04, 0.0);
controls.enableDamping = true;
controls.update();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});

window.WORLD = world;   // for the voxelizer and for inspection
console.log('[embodied] scene built', world.objects.map((o) => o.name).join(', '));

const params = new URLSearchParams(location.search);

// ?cam=x,y,z,tx,ty,tz: where to look from and at
if (params.has('cam')) {
  const v = params.get('cam').split(',').map(Number);
  camera.position.set(v[0], v[1], v[2]);
  controls.target.set(v[3], v[4], v[5]);
  controls.update();
}

// ?hand=<pose>[&hp=x,y,z][&hr=rx,ry,rz]: the hand, in a pose (open, hook, pinch, wrap), at a place and turn.
// Default: above the near right of the table, back of the hand up, fingers pointing into the scene.
if (params.has('hand')) {
  const { buildHand, setPose } = await import('./hand.js');
  const hand = buildHand();
  setPose(hand, params.get('hand') || 'open');
  const hp = (params.get('hp') ?? '0.32,0.09,0.42').split(',').map(Number);
  const hr = (params.get('hr') ?? `${-Math.PI / 2},0,0`).split(',').map(Number);
  hand.position.set(hp[0], hp[1], hp[2]);
  hand.rotation.set(hr[0], hr[1], hr[2], 'YXZ');
  scene.add(hand);
  window.HAND = hand;
}

// ?replay=<name>[&frame=k]: an attempt the body made (data/<name>.json, written by body/grasp.py), shown at one of
// its frames (default: the last): the hand where it was, oriented to what it was doing, and what happened.
if (params.has('replay')) {
  const { buildHand, setPose } = await import('./hand.js');
  const path = await fetch(`/data/${params.get('replay')}.json`).then((r) => r.json());
  const k = Math.min(path.length - 1, Number(params.get('frame') ?? path.length - 1));
  const fr = path[k];
  const hand = buildHand();
  setPose(hand, fr.pose);
  const V = (a) => new THREE.Vector3(...a);
  const up = new THREE.Vector3(0, 1, 0);
  let F, B;   // the fingers' direction, and the back of the hand's
  if (fr.face) {
    const face = new THREE.Vector3(fr.face[0], 0, fr.face[1]).normalize();
    if (fr.part === 'rim') { F = new THREE.Vector3(0, -1, 0); B = face.clone().negate(); }   // from above, palm to the mug
    else { F = new THREE.Vector3().crossVectors(up, face).normalize(); B = face.clone().negate(); }   // across, palm to it
  } else {   // on the way: fingers along the way it is going, palm down
    const next = path[Math.min(k + 1, path.length - 1)].at, prev = path[Math.max(k - 1, 0)].at;
    F = V(next).sub(V(prev)).setY(0);
    if (F.lengthSq() < 1e-9) F.set(0, 0, -1);
    F.normalize();
    B = up.clone();
  }
  const X = new THREE.Vector3().crossVectors(F, B).normalize();
  B = new THREE.Vector3().crossVectors(X, F).normalize();
  hand.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, F, B));
  hand.position.copy(V(fr.at)).addScaledVector(F, -0.12).addScaledVector(B, 0.015);
  scene.add(hand);
  const target = world.objects.find((o) => o.name === 'mug_b').group;
  if (fr.lift) target.position.y += fr.lift;
  const ev = path.slice(0, k + 1).map((p) => p.event).filter(Boolean).pop();
  if (ev && ev.includes('knocked')) {   // the thing knocked tips away from the hand
    const name = ev.split(' ')[0];
    const g = world.objects.find((o) => o.name === name)?.group;
    if (g) { const away = g.position.clone().sub(V(fr.at)).setY(0).normalize(); g.rotateOnWorldAxis(new THREE.Vector3(away.z, 0, -away.x), 0.35); }
  }
  const label = document.createElement('div');
  label.style.cssText = 'position:fixed;left:24px;top:18px;font:600 26px Helvetica,Arial,sans-serif;color:#2b2b2b;' +
    'background:rgba(255,255,255,0.78);padding:8px 14px;border-radius:6px';
  label.textContent = `${params.get('label') ?? ''} ${fr.side ?? ''} ${fr.part ?? ''} ${fr.pose ?? ''}: ${ev ?? fr.gerund}`;
  document.body.appendChild(label);
}

// ?cells[=size]: the scene as the octree left it. Each cell a square of its mean colour (or, with
// =size, coloured by its size: fine red to coarse blue), at its samples' mean position, facing their
// mean normal, as wide as the cell. The objects themselves are hidden.
if (params.has('cells')) {
  const buf = await fetch(`/data/cells_${dataName}.bin`).then((r) => r.arrayBuffer());
  const f = new Float32Array(buf);
  const n = f.length / 10;
  for (const o of world.objects) o.group.visible = false;
  const mesh = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }), n);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), z = new THREE.Vector3(0, 0, 1);
  const col = new THREE.Color();
  const bySize = params.get('cells') === 'size';
  // =distinct: the cells distinctive in their family in their own colour, the rest dimmed to grey
  const distinct = params.get('cells') === 'distinct'
    ? new Float32Array(await fetch(`/data/distinct_${dataName}.bin`).then((r) => r.arrayBuffer())) : null;
  for (let i = 0; i < n; i++) {
    const o = i * 10;
    const nrm = new THREE.Vector3(f[o + 3], f[o + 4], f[o + 5]);
    q.setFromUnitVectors(z, nrm.lengthSq() > 0.01 ? nrm.normalize() : new THREE.Vector3(0, 1, 0));
    const s = f[o + 6] * 0.92;   // a little smaller than the cell, so cells show as cells
    m.compose(new THREE.Vector3(f[o], f[o + 1], f[o + 2]), q, new THREE.Vector3(s, s, s));
    mesh.setMatrixAt(i, m);
    if (bySize) {   // log scale: 1 mm red .. 160 mm blue
      const t = Math.min(1, Math.max(0, Math.log2(f[o + 6] * 1000) / Math.log2(160)));
      col.setHSL(t * 0.66, 0.85, 0.5);
    } else if (distinct && !(distinct[i] > 30)) {
      const g = 0.82 + 0.1 * (f[o + 7] + f[o + 8] + f[o + 9]) / 3;
      col.setRGB(g, g, g, THREE.SRGBColorSpace);
    } else col.setRGB(f[o + 7], f[o + 8], f[o + 9], THREE.SRGBColorSpace);
    mesh.setColorAt(i, col);
  }
  scene.add(mesh);
  console.log(`[embodied] ${n} cells`);
}

// ?sample[=density]: the Reader samples every surface and sends the samples to the server
if (params.has('sample')) {
  const { sampleWorld } = await import('./sampler.js');
  const density = Number(params.get('sample')) || 1e6;
  const t0 = performance.now();
  const { manifest, blob } = sampleWorld(world, { density, seed: 1 + layout });   // its own sampling and node shuffle
  const name = `samples_${dataName}`;
  const post = (file, body) => fetch(`/api/save/${file}`, { method: 'POST', body }).then((r) => r.text());
  console.log('[embodied]', await post(`${name}.json`, JSON.stringify(manifest, null, 1)));
  console.log('[embodied]', await post(`${name}.bin`, blob));
  console.log(`[embodied] sampled ${manifest.points} points in ${((performance.now() - t0) / 1000).toFixed(1)}s`);
  document.title = 'sampled';
}
