// The first scene: a kitchen table with what collects on one. Five mugs (three of one diner model,
// a handmade one, a coloured one), a stack of books, a bottle of oil. Built from one seed.
import * as THREE from 'three';
import { makeRand, makeNoise } from './rng.js';
import { mug, book, bottle, table } from './objects.js';

// layout: 0 is the scene as first set. Any other number rearranges it with its own randomness, after every
// object has been made, so the objects are the same individuals: the mugs swap places and turn, the stack of
// books turns. For recognition: the same things, seen again somewhere else.
export function buildWorld(seed = 7, layout = 0) {
  const rand = makeRand(seed);
  const noise = makeNoise(rand);
  const scene = new THREE.Scene();
  const objects = [];

  // gerund: what the object is doing under forces, the region of the gerund field it makes. It is
  // perceived (the field is what the mind sees); which object is which is not (truth: the answer key)
  const place = (name, g, x, z, turn = 0, gerund = 'resting') => {
    g.position.set(x, 0, z);
    g.rotation.y = turn;
    g.name = name;
    g.userData.gerund = gerund;
    scene.add(g);
    objects.push({ name, group: g, truth: g.userData.truth, gerund });
    return g;
  };

  place('table', table(rand, noise, { age: 14 }), 0, 0, 0, 'supporting');

  // three of the same diner mug: the differences between them are the years and what they held
  place('mug_a', mug(rand, noise, { model: 'diner', age: 0.4 }), -0.32, 0.12, rand.range(0, 6.28));
  place('mug_b', mug(rand, noise, { model: 'diner', age: 17, stain: 0.95, chip: true }), -0.16, 0.2, rand.range(0, 6.28));
  place('mug_c', mug(rand, noise, { model: 'diner', age: 6, stain: 0.35,
    print: { text: 'Lakeside Diner', family: 'Georgia, serif', font: 'italic bold', color: '#8c2b20', size: 0.015 } }),
  -0.05, 0.05, Math.PI / 2 + 0.35);   // its print toward the viewer
  place('mug_d', mug(rand, noise, { model: 'stoneware', age: 3, stain: 0.5 }), 0.1, 0.18, rand.range(0, 6.28));
  place('mug_e', mug(rand, noise, { model: 'colored', age: 8, stain: 0.6,
    print: { text: 'coffee first.', family: 'Helvetica, Arial, sans-serif', font: 'bold', color: '#f3f1ec', size: 0.013 } }),
  0.26, 0.08, Math.PI / 2 - 0.5);

  const stack = new THREE.Group();
  const b1 = book(rand, noise, { w: 0.16, h: 0.235, d: 0.042, cover: '#2f4a3a', binding: 'cloth',
    title: 'A Natural History\nof Salt', author: 'Margaret Ellison', age: 38, sun: 0.85, foil: '#cdb46a' });
  const b2 = book(rand, noise, { w: 0.14, h: 0.21, d: 0.026, cover: '#d4a536', binding: 'paper', titleColor: '#1f2a44',
    title: 'The Quiet Year', author: 'Daniel Oyelaran', age: 5, ring: [0.62, 0.4], titleFamily: 'Helvetica, Arial, sans-serif' });
  const b3 = book(rand, noise, { w: 0.13, h: 0.195, d: 0.03, cover: '#6b2430', binding: 'cloth',
    title: 'Field Notes\non Small Birds', author: 'H. W. Barrow', age: 55, sun: 0.4, damp: true, foil: '#d9c48a', titleSize: 34 });
  b2.position.set(0.01, 0.042, -0.005); b2.rotation.y = 0.12;
  b3.position.set(-0.008, 0.068, 0.01); b3.rotation.y = -0.07;
  stack.add(b1, b2, b3);
  stack.userData.truth = { kind: 'stack', of: [b1.userData.truth, b2.userData.truth, b3.userData.truth] };
  place('books', stack, -0.36, -0.2, Math.PI / 2 - 0.25);   // spines toward the viewer
  stack.userData.part = true;   // the stack is not a thing of its own: its books are
  b1.userData.gerund = 'supporting'; b2.userData.gerund = 'supporting'; b3.userData.gerund = 'resting';
  objects.push({ name: 'book_salt', group: b1, truth: b1.userData.truth, gerund: 'supporting' },
    { name: 'book_quiet', group: b2, truth: b2.userData.truth, gerund: 'supporting' },
    { name: 'book_birds', group: b3, truth: b3.userData.truth, gerund: 'resting' });

  place('bottle', bottle(rand, noise, { glass: '#4e6b34', liquid: '#a8922e', fill: 0.55, cap: '#2b2b2b', age: 2,
    drip: true, torn: true,
    label: { brand: 'Casa Moretti', product: 'OLIVE OIL', note: 'Extra virgin  ·  cold pressed  ·  500 ml',
      color: '#efe4c8', ink: '#2c3d24' } }), 0.15, -0.16, -0.25, 'containing');

  if (layout >= 200 && layout < 300) {   // grasp tasks: the oil bottle stands right beside the wanted mug, on the
    // side away from its handle (3 cm between them), so something is in the way on that side.
    // 200: the chipped mug as it stands. 201: the same mug turned (its handle and chip another way).
    // 202: the "Lakeside Diner" mug (no chip), as it stands. 203: the new diner mug, 204: the stoneware mug, 205:
    // the blue mug, each turned its own way (mugs no method has learned on).
    const want = { 202: 'mug_c', 203: 'mug_a', 204: 'mug_d', 205: 'mug_e' }[layout] ?? 'mug_b';
    const mb = objects.find((o) => o.name === want).group, bt = objects.find((o) => o.name === 'bottle').group;
    if (layout === 201) mb.rotation.y += 2.6;
    // the new mugs' handles set to face three different ways (the handle is local +x, so it faces
    // (cos t, -sin t) in x, z): toward the near side, the far side, the right (first turned by offsets, and all
    // three happened to face left, the bottle on the right: one arrangement, not a test of others)
    const face = { 203: -Math.PI / 2 + 0.3, 204: Math.PI / 2 - 0.3, 205: 0.35 }[layout];
    if (face !== undefined) mb.rotation.y = face;
    const th = mb.rotation.y;
    const away = new THREE.Vector3(-Math.cos(th), 0, Math.sin(th));   // opposite the handle (local +x)
    bt.position.copy(mb.position).addScaledVector(away, 0.0415 + 0.034 + 0.03);
  } else if (layout) {   // 1..99: the mugs swap places and turn; 100 on: each turns where it stands (watched turning:
    const lr = makeRand(layout * 7919 + 13);   // which is which carries over by place, for learning)
    const mugs = objects.filter((o) => o.name.startsWith('mug_'));
    const spots = mugs.map((o) => o.group.position.clone());
    if (layout < 100) {
      for (let i = spots.length - 1; i > 0; i--) {
        const j = Math.floor(lr() * (i + 1));
        [spots[i], spots[j]] = [spots[j], spots[i]];
      }
    }
    mugs.forEach((o, i) => { o.group.position.copy(spots[i]); o.group.rotation.y = lr.range(0, Math.PI * 2); });
    stack.rotation.y += lr.range(-0.6, 0.6);
  }

  return { scene, objects, seed, layout };
}
