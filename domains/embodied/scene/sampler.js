// The Reader's first pass: every surface in the scene sampled evenly by area (density points per
// square metre), each point with its place, the way its surface faces, its colour (read from the
// surface's own texture: albedo, not lit), and the gerund region it lies in. Which object it came
// from is kept too, as the answer key the mind never sees. Coordinates stay on this side of the line:
// the octree is built from them, the mind reads what the octree makes of them.
import * as THREE from 'three';
import { MeshSurfaceSampler } from 'three/addons/math/MeshSurfaceSampler.js';

const pixelCache = new Map();
function pixels(tex) {   // a canvas texture's pixels, read once
  if (!pixelCache.has(tex)) {
    const c = tex.image;
    pixelCache.set(tex, { w: c.width, h: c.height, d: c.getContext('2d').getImageData(0, 0, c.width, c.height).data });
  }
  return pixelCache.get(tex);
}

function texel(tex, u, v) {
  const p = pixels(tex);
  const wrap = (x, mode) => (mode === THREE.RepeatWrapping ? x - Math.floor(x) : Math.min(1, Math.max(0, x)));
  const uu = wrap(u, tex.wrapS), vv = wrap(v, tex.wrapT);
  const x = Math.min(p.w - 1, Math.floor(uu * p.w));
  const y = Math.min(p.h - 1, Math.floor((tex.flipY ? 1 - vv : vv) * p.h));
  const i = (y * p.w + x) * 4;
  return [p.d[i], p.d[i + 1], p.d[i + 2]];
}

// the part of a geometry one material covers (a book's cover, spine, page edges)
function part(geo, group) {
  const g = geo.clone();
  if (group) {
    const idx = geo.index.array.slice(group.start, group.start + group.count);
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.clearGroups();
  }
  return g;
}

function worldArea(geo, matrix) {
  const pos = geo.attributes.position, idx = geo.index;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  const tri = new THREE.Triangle();
  let area = 0;
  const n = idx ? idx.count : pos.count;
  for (let i = 0; i < n; i += 3) {
    const [i0, i1, i2] = idx ? [idx.getX(i), idx.getX(i + 1), idx.getX(i + 2)] : [i, i + 1, i + 2];
    a.fromBufferAttribute(pos, i0).applyMatrix4(matrix);
    b.fromBufferAttribute(pos, i1).applyMatrix4(matrix);
    c.fromBufferAttribute(pos, i2).applyMatrix4(matrix);
    tri.set(a, b, c);
    area += tri.getArea();
  }
  return area;
}

export function sampleWorld(world, { density = 1e6, seed = 1 } = {}) {
  const { scene } = world;
  scene.updateMatrixWorld(true);
  const things = world.objects.filter((o) => !o.group.userData.part);   // the stack's books, not the stack
  const owner = new Map(things.map((o, k) => [o.group, k]));
  const gerunds = [];
  const gid = (g) => (gerunds.includes(g) ? gerunds.indexOf(g) : gerunds.push(g) - 1);

  // a seeded random for the sampler (three's sampler draws from Math.random unless given one)
  let s = seed >>> 0;
  const rnd = () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

  // the gerund field's nodes: each doing is a region (the table supporting, a book resting on it, the oil
  // pooling in its glass). Object boundaries are force boundaries. Node ids are shuffled, so they say which
  // surfaces belong to one doing and nothing about which object it is.
  const nodeKeys = [];
  const nodeOf = (key) => (nodeKeys.includes(key) ? nodeKeys.indexOf(key) : nodeKeys.push(key) - 1);
  const chunks = [];
  let total = 0;
  const perPart = [];
  scene.traverse((mesh) => {
    if (!mesh.isMesh) return;
    let up = mesh, obj = null, gerund = mesh.userData.gerund;
    while (up && obj === null) {
      if (owner.has(up)) obj = owner.get(up);
      if (!gerund && up.userData.gerund) gerund = up.userData.gerund;
      up = up.parent;
    }
    if (obj === null) return;
    const node = nodeOf(mesh.userData.gerund ? `${obj}:${mesh.uuid}` : `${obj}`);
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const groups = Array.isArray(mesh.material) ? mesh.geometry.groups : [null];
    const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
    groups.forEach((group, gi) => {
      const mat = mats[group ? group.materialIndex : 0];
      const geo = part(mesh.geometry, group);
      const area = worldArea(geo, mesh.matrixWorld);
      const want = Math.round(area * density);
      if (!want) return;
      const sampler = new MeshSurfaceSampler(new THREE.Mesh(geo)).setRandomGenerator(rnd).build();
      const P = new THREE.Vector3(), N = new THREE.Vector3(), UV = new THREE.Vector2();
      const base = mat.color.clone().convertLinearToSRGB();
      const pos = new Float32Array(want * 3), nrm = new Int8Array(want * 3), col = new Uint8Array(want * 3);
      let k = 0;
      for (let i = 0; i < want; i++) {
        sampler.sample(P, N, null, UV);
        if (mat.alphaMap && texel(mat.alphaMap, UV.x, UV.y)[0] < 128) continue;   // torn away: no surface
        P.applyMatrix4(mesh.matrixWorld);
        N.applyMatrix3(normalMatrix).normalize();
        const t = mat.map ? texel(mat.map, UV.x, UV.y) : [255, 255, 255];
        pos.set([P.x, P.y, P.z], k * 3);
        nrm.set([Math.round(N.x * 127), Math.round(N.y * 127), Math.round(N.z * 127)], k * 3);
        col.set([t[0] * base.r, t[1] * base.g, t[2] * base.b], k * 3);
        k++;
      }
      chunks.push({ pos: pos.subarray(0, k * 3), nrm: nrm.subarray(0, k * 3), col: col.subarray(0, k * 3), n: k,
        obj, node, gerund: gid(gerund ?? 'resting') });
      perPart.push({ object: things[obj].name, mesh: mesh.uuid.slice(0, 8), part: gi, area, points: k });
      total += k;
    });
  });

  // pack: positions f32 x3 | normals i8 x3 | colours u8 x3 | gerund u8 | node u8 | object u8 (the answer key)
  const pos = new Float32Array(total * 3), nrm = new Int8Array(total * 3), col = new Uint8Array(total * 3);
  const ger = new Uint8Array(total), nod = new Uint8Array(total), obj = new Uint8Array(total);
  const shuffle = [...nodeKeys.keys()];
  for (let i = shuffle.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [shuffle[i], shuffle[j]] = [shuffle[j], shuffle[i]]; }
  let o = 0;
  for (const c of chunks) {
    pos.set(c.pos, o * 3); nrm.set(c.nrm, o * 3); col.set(c.col, o * 3);
    ger.fill(c.gerund, o, o + c.n); nod.fill(shuffle[c.node], o, o + c.n); obj.fill(c.obj, o, o + c.n);
    o += c.n;
  }
  const manifest = {
    seed: world.seed, density, points: total,
    layout: ['pos f32 x3', 'normal i8 x3 (x/127)', 'colour u8 x3 (sRGB albedo)', 'gerund u8', 'node u8 (shuffled)',
      'object u8 (answer key)'],
    nodes: nodeKeys.length,
    gerunds,
    answer_key: things.map((t) => ({ name: t.name, gerund: t.gerund, truth: t.truth,
      matrix: t.group.matrixWorld.elements.slice() })),   // where the designer put it (column-major 4x4)
    parts: perPart,
  };
  const blob = new Blob([pos, nrm, col, ger, nod, obj]);
  return { manifest, blob };
}
