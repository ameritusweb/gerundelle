// The hand: a right hand and forearm, articulated (palm, four fingers of three segments, a thumb of three),
// with the grips a mug invites. Poses are joint angles; the world sets them, the mind only reads what the
// hand is doing (its gerund: empty, extending, gripping, releasing) and what it touches.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const skin = new THREE.MeshPhysicalMaterial({ color: '#d9a88a', roughness: 0.55, sheen: 0.4, sheenColor: '#ffd9c4',
  clearcoat: 0.05 });

function capsule(r, len) {
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 6, 14), skin);
  m.position.y = len / 2;   // grows from its joint along +y
  m.castShadow = m.receiveShadow = true;
  return m;
}

// a chain of segments: each joint a group rotating about its local x axis (curl), the first also about z (spread)
function chain(lengths, radii) {
  const joints = [];
  let parent = null, root = null;
  lengths.forEach((len, i) => {
    const j = new THREE.Group();
    j.add(capsule(radii[i], len));
    if (parent) { j.position.y = lengths[i - 1]; parent.add(j); } else root = j;
    joints.push(j);
    parent = j;
  });
  return { root, joints };
}

// Proportions of an adult hand (metres): palm 0.09 long, 0.08 wide at the knuckles, narrower at the wrist.
const FINGERS = [   // name, base across the palm (x), base height (the knuckles lie on an arc), segments, radius
  ['index', 0.027, 0.088, [0.042, 0.026, 0.021], 0.0088],
  ['middle', 0.0085, 0.092, [0.047, 0.029, 0.022], 0.0091],
  ['ring', -0.0105, 0.089, [0.044, 0.027, 0.021], 0.0086],
  ['little', -0.0275, 0.081, [0.034, 0.021, 0.019], 0.0075],
];

export function buildHand() {
  const hand = new THREE.Group();   // the wrist: palm along +y, back of the hand toward +z, thumb toward +x
  hand.name = 'hand';
  // the palm: a rounded slab, wider at the knuckles than at the wrist, fuller on the thumb side (the
  // thenar pad), thinner at the edges (first a box: a mannequin's block)
  const geo = new RoundedBoxGeometry(0.078, 0.092, 0.028, 4, 0.011);
  geo.translate(0, 0.046, 0);
  const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const t = y / 0.092;                           // 0 at the wrist, 1 at the knuckles
    x *= 0.8 + 0.2 * t;                            // narrower toward the wrist
    if (z < 0 && x > 0.005 && t < 0.6) z -= 0.006 * Math.sin(Math.PI * t / 0.6) * (x / 0.039);   // the thenar pad
    z *= 1 - 0.3 * (x / 0.039) ** 4;               // thinner at the edges
    p.setXYZ(i, x, y, z);
  }
  geo.computeVertexNormals();
  const palm = new THREE.Mesh(geo, skin);
  palm.castShadow = palm.receiveShadow = true;
  hand.add(palm);
  const forearm = new THREE.Mesh(new THREE.CylinderGeometry(0.029, 0.037, 0.22, 24), skin);
  forearm.scale.z = 0.72;   // a forearm is flatter than it is wide
  forearm.position.y = -0.11;
  forearm.castShadow = true;
  hand.add(forearm);

  const fingers = {};
  for (const [name, x, y, lens, r] of FINGERS) {
    const c = chain(lens, [r, r * 0.9, r * 0.82]);
    c.root.position.set(x, y - 0.006, 0.001);
    hand.add(c.root);
    fingers[name] = c.joints;
  }
  const thumb = chain([0.032, 0.030, 0.024], [0.011, 0.0098, 0.009]);
  const thumbBase = new THREE.Group();   // the thumb leaves the palm low on its side, angled out and forward
  thumbBase.position.set(0.034, 0.018, 0.004);
  thumbBase.add(thumb.root);
  hand.add(thumbBase);
  fingers.thumb = thumb.joints;
  hand.userData = { fingers, thumbBase, gerund: 'empty' };
  setPose(hand, 'open');
  return hand;
}

// Joint angles (radians) per pose: [knuckle curl, middle curl, tip curl] per finger; spread at the knuckle;
// the thumb's base: its swing across the palm (z), its turn toward the fingers (y), then its curls.
const POSES = {
  open: { curl: [0.12, 0.1, 0.05], spread: 0.09, thumb: { swing: -0.75, turn: 0.4, curl: [0.15, 0.1, 0.05] } },
  // fingers hooked through a handle: knuckles straight-ish, middle and tip joints curled round it
  hook: { curl: [0.5, 1.45, 1.0], spread: 0.0, thumb: { swing: -0.35, turn: 0.9, curl: [0.25, 0.5, 0.4] } },
  // thumb and index pinched together, the rest folded away
  pinch: { curl: [0.75, 0.55, 0.35], spread: 0.02, index: [0.85, 0.5, 0.3],
    thumb: { swing: -1.15, turn: 1.05, curl: [0.35, 0.35, 0.25] } },
  // fingers and thumb wrapped round a body
  wrap: { curl: [0.85, 0.8, 0.5], spread: 0.03, thumb: { swing: -1.05, turn: 0.75, curl: [0.3, 0.45, 0.3] } },
};

export function setPose(hand, pose, t = 1) {
  const P = POSES[pose] ?? POSES.open, O = POSES.open;
  const lerp = (a, b) => a + (b - a) * t;
  const { fingers, thumbBase } = hand.userData;
  ['index', 'middle', 'ring', 'little'].forEach((name, k) => {
    const curl = P[name] ?? P.curl, oc = O[name] ?? O.curl;
    fingers[name].forEach((j, i) => { j.rotation.x = -lerp(oc[i], curl[i]); });   // curl toward the palm (-z side)
    fingers[name][0].rotation.z = lerp(O.spread, P.spread) * (1.5 - k);
  });
  thumbBase.rotation.set(0, lerp(O.thumb.turn, P.thumb.turn), lerp(O.thumb.swing, P.thumb.swing));
  fingers.thumb.forEach((j, i) => { j.rotation.x = -lerp(O.thumb.curl[i], P.thumb.curl[i]); });
  hand.userData.pose = pose;
}
