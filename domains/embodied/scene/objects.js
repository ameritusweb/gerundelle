// Objects as individuals of a kind: each is generated from its family's model with the variation
// real ones have (manufacture, handwork), then aged (use, light, washing, knocks). Nothing is a
// "marker": what makes one distinctive is how it differs from the others it is seen among.
// Every object keeps what was put into it in userData.truth: the designer's answer key, never
// shown to the mind.
import * as THREE from 'three';
import { canvas, texture, paint, adjust, crazing, print, patch, ring, scratches, wood, cloth, paper,
  clamp, mix, hex, rgb } from './textures.js';

const TAU = Math.PI * 2;

// ---- profiles ------------------------------------------------------------------------------------

// Resample a polyline profile [(r, y)] to n points evenly spaced by arc length, so a lathe's v
// coordinate is proportional to distance along the profile (letters and stains keep their size).
function resample(pts, n) {
  const seg = [0];
  for (let i = 1; i < pts.length; i++) {
    seg.push(seg[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  }
  const L = seg[seg.length - 1];
  const out = [];
  let k = 0;
  for (let i = 0; i < n; i++) {
    const s = (L * i) / (n - 1);
    while (k < seg.length - 2 && seg[k + 1] < s) k++;
    const t = (s - seg[k]) / Math.max(seg[k + 1] - seg[k], 1e-9);
    out.push([pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t, s / L]);
  }
  return { pts: out, L };
}

// v at which the profile first reaches a condition (searching from an end).
function vWhere(prof, pred, fromEnd = false) {
  const idx = fromEnd ? [...prof.pts.keys()].reverse() : [...prof.pts.keys()];
  for (const i of idx) if (pred(prof.pts[i])) return prof.pts[i][2];
  return null;
}

// ---- mugs ----------------------------------------------------------------------------------------

export const MUG_MODELS = {
  // a commercial diner mug: thick walls, rolled rim, very consistent from one to the next
  diner: { R: 0.041, H: 0.094, t: 0.0065, belly: 0.04, flare: 0.02, foot: 0.9, rimRoll: 0.0045,
    handle: { top: 0.78, bottom: 0.25, reach: 0.032, thick: 0.0068, squareness: 0.3 },
    sd: 0.008, glaze: '#f1eee6', interior: null, clay: '#d9cdb8', speckle: 0, mottle: 0.015, wobble: 0 },
  // a handmade stoneware mug: speckled oatmeal glaze, uneven, thick, a glaze that breaks at edges
  stoneware: { R: 0.044, H: 0.088, t: 0.008, belly: 0.1, flare: -0.03, foot: 0.82, rimRoll: 0.003,
    handle: { top: 0.72, bottom: 0.3, reach: 0.03, thick: 0.0085, squareness: 0.1 },
    sd: 0.03, glaze: '#d6cbb0', interior: null, clay: '#a0785a', speckle: 0.0025, mottle: 0.035, wobble: 0.02 },
  // a mass-produced coloured mug with a white inside
  colored: { R: 0.04, H: 0.1, t: 0.005, belly: 0.0, flare: 0.06, foot: 0.92, rimRoll: 0.0025,
    handle: { top: 0.8, bottom: 0.3, reach: 0.034, thick: 0.006, squareness: 0.55 },
    sd: 0.006, glaze: '#2f5d8a', interior: '#f3f1ec', clay: '#e3d9c6', speckle: 0, mottle: 0.02, wobble: 0 },
};

// One mug: its model's dimensions with this one's own variation, then what its years did to it.
// opts: { model, seed, age (years), glaze (override), print: {text, family, font, color, size},
//         chip: true | {angle, size}, stain: 0..1 (how much coffee or tea it has held) }
export function mug(rand, noise, opts) {
  const M = MUG_MODELS[opts.model];
  const v = (x, sd = M.sd) => x * (1 + rand.near(0, sd));
  const age = opts.age ?? 0;
  const ageN = clamp(age / 20);   // 0 new .. 1 twenty years of use
  const R = v(M.R), H = v(M.H), t = v(M.t, M.sd * 2), rimRoll = v(M.rimRoll, M.sd * 3);
  const belly = M.belly + rand.near(0, M.sd * 2), flare = M.flare + rand.near(0, M.sd * 2);
  const footR = R * v(M.foot, M.sd);
  const base = t * 1.4;

  // the outer wall: r(y) with belly (bulge mid-height) and flare (wider at the rim)
  const wall = (y) => {
    const s = y / H;
    return R * (1 + belly * Math.sin(Math.PI * s) * 0.6 + flare * (s - 0.5));
  };
  const pts = [[0, 0.004], [footR * 0.92, 0.004], [footR * 0.95, 0.0], [footR, 0.0], [wall(0.008), 0.008]];
  for (let i = 1; i <= 24; i++) pts.push([wall(0.008 + (H - 0.008) * (i / 24)), 0.008 + (H - 0.008) * (i / 24)]);
  const rTop = wall(H);
  for (let i = 1; i <= 8; i++) {   // the rim: a half-roll over the top
    const a = (Math.PI * i) / 8;
    pts.push([rTop - t / 2 + Math.cos(a) * (t / 2 + rimRoll * 0.3), H + Math.sin(a) * rimRoll]);
  }
  for (let i = 1; i <= 20; i++) {   // the inner wall back down
    const y = H - (H - base) * (i / 20);
    pts.push([wall(y) - t, y]);
  }
  pts.push([(wall(base) - t) * 0.6, base - 0.0005], [0, base - 0.001]);
  const prof = resample(pts, 160);
  const lathePts = prof.pts.map(([r, y]) => new THREE.Vector2(r, y));
  const geo = new THREE.LatheGeometry(lathePts, 128);

  // handmade wobble: the body is not quite round, more so toward the rim
  const wob = M.wobble ? [rand.range(0, TAU), rand.range(0, TAU), rand.range(0.5, 1), rand.range(0.3, 0.8)] : null;
  const pos = geo.attributes.position;
  const chip = opts.chip ? { angle: opts.chip.angle ?? rand.range(0, TAU), size: opts.chip.size ?? rand.range(0.004, 0.008) } : null;
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    const phi = Math.atan2(x, z);
    if (wob) {
      const k = 1 + M.wobble * (y / H) * (wob[2] * Math.sin(2 * phi + wob[0]) + wob[3] * Math.sin(3 * phi + wob[1]));
      x *= k; z *= k;
    }
    if (chip && y > H - chip.size) {   // a piece knocked out of the rim
      let d = Math.abs(((phi - chip.angle + Math.PI * 3) % TAU) - Math.PI);
      const w = chip.size / R;   // angular half-width
      if (d < w) {
        const depth = chip.size * Math.sqrt(1 - (d / w) ** 2);
        y = Math.min(y, H + rimRoll - depth * 1.6);
      }
    }
    pos.setXYZ(i, x, y, z);
  }
  geo.computeVertexNormals();

  // ---- the surface, painted in UV space: u around (phi = u * TAU), v along the profile ----
  const W = 1024, Hc = 1024;
  const c = canvas(W, Hc);
  const glaze = hex(opts.glaze ?? M.glaze);
  const inside = M.interior ? hex(M.interior) : glaze;
  const clay = hex(M.clay);
  const vFoot = vWhere(prof, ([r, y, vv]) => y >= 0.006 && r > footR * 0.99) ?? 0.05;   // glaze starts above the foot
  const vRim = vWhere(prof, ([r, y]) => y >= H + rimRoll * 0.95) ?? 0.5;              // the top of the rim
  const cyOf = (vv) => (1 - vv) * Hc;
  const ox = rand.range(0, 100), tint = [rand.near(0, 2), rand.near(0, 2), rand.near(0, 2)];
  paint(c, (px, py) => {
    const vv = 1 - py / Hc;
    if (vv < vFoot) return clay.map((k) => k * (0.92 + 0.08 * noise.fbm(px * 0.05, py * 0.05, 2)));   // bare foot ring
    const col = vv > vRim + 0.01 ? inside : glaze;
    const m = noise.fbmWrap(px * 0.012 + ox, py * 0.012, W * 0.012, 4) * M.mottle;
    // glaze thins and breaks over the rim's edge, showing the body's colour through it
    const breakT = M.mottle > 0.05 ? clamp(1 - Math.abs(vv - vRim) * 60) * 0.35 : 0;
    return mix(col.map((k, i) => k * (1 + m) + tint[i]), clay, breakT);
  });
  const ctx = c.getContext('2d');
  if (M.speckle) {   // iron speckles in the clay come up through the glaze
    const n = Math.round(W * Hc * M.speckle);
    for (let k = 0; k < n; k++) {
      ctx.fillStyle = rgb([70 + rand() * 30, 50 + rand() * 20, 30], rand.range(0.4, 0.9));
      const s = rand.range(0.6, 2.2);
      ctx.beginPath();
      ctx.arc(rand() * W, rand.range(0, cyOf(vFoot)), s, 0, TAU);
      ctx.fill();
    }
  }

  // pixels per metre around and along, for things that must keep their shape
  const pxU = W / (TAU * R), pxV = Hc / prof.L;
  const truth = { kind: 'mug', model: opts.model, age, R, H, belly, flare, glaze: opts.glaze ?? M.glaze,
    handle: {}, marks: [] };

  if (opts.print) {   // a print: a slogan, a diner's name, a logo line
    const p = opts.print;
    const uC = ((opts.printAngle ?? Math.PI * 1.5) / TAU) % 1;   // default: across from the handle
    const yC = H * (p.height ?? 0.55);
    const vC = vWhere(prof, ([r, y]) => y >= yC) ?? 0.3;
    const size = (p.size ?? 0.016) * pxV;
    for (const shift of [0, -W, W]) {   // drawn three times so a print across the seam wraps
      print(c, rand, noise, p.text, { x: uC * W + shift, y: cyOf(vC), size, sx: pxU / pxV, sy: 1,
        family: p.family, font: p.font ?? 'bold', color: hex(p.color ?? '#222222'), age: ageN * (p.wear ?? 1),
        letterSpacing: p.spacing ?? 0 });
    }
    truth.marks.push({ what: 'print', text: p.text, at: { angle: uC * TAU, height: yC }, faded: ageN });
  }

  if (age > 0) {
    // crazing: a web of fine cracks in the glaze, more with years; inside it takes up the stain
    const nC = Math.round(ageN * ageN * 260);
    if (nC) {
      crazing(c, rand, { y0: cyOf(vRim - 0.02), y1: cyOf(vFoot), count: Math.round(nC * 0.5), color: [120, 110, 95], alpha: 0.25 });
      crazing(c, rand, { y0: 0, y1: cyOf(vRim + 0.02), count: nC, color: [110, 75, 40], alpha: 0.3 + 0.4 * (opts.stain ?? 0) });
      truth.marks.push({ what: 'crazing', amount: ageN * ageN });
    }
    // the stain line inside, where coffee or tea stood, and the brown film below it
    const stain = (opts.stain ?? 0) * clamp(age / 8);
    if (stain > 0.02) {
      const fillY = H * rand.range(0.7, 0.82);
      const vFill = vWhere(prof, ([r, y, vv]) => vv > vRim && y <= fillY) ?? 0.7;
      adjust(c, (px, py, col) => {
        const vv = 1 - py / Hc;
        if (vv < vFill) return col;
        const k = stain * (0.35 + 0.25 * noise.fbmWrap(px * 0.02, py * 0.02, W * 0.02, 3));
        return mix(col, [120, 80, 45], clamp(k));
      });
      for (let s = 0; s < 3; s++) {   // the line itself, and older lines just below it
        const vv = vFill + s * rand.range(0.005, 0.02);
        ctx.strokeStyle = rgb([95, 60, 30], stain * rand.range(0.25, 0.55));
        ctx.lineWidth = rand.range(2, 6);
        ctx.beginPath();
        for (let px = 0; px <= W; px += 8) {
          const py = cyOf(vv) + noise.fbm(px * 0.01 + s, 0, 2) * 6;
          if (px === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
      }
      truth.marks.push({ what: 'stain', level: fillY, amount: stain });
    }
    // the rim worn by lips and by being stacked, glaze rubbed thin in places
    const nWear = Math.round(ageN * 14);
    for (let k = 0; k < nWear; k++) {
      patch(c, { x: rand() * W, y: cyOf(vRim) + rand.near(0, 4), rx: rand.range(8, 30), ry: rand.range(2, 5),
        color: mix(glaze, clay, 0.6), alpha: rand.range(0.2, 0.6) * ageN });
    }
    // utensil marks: grey scratches inside from spoons, and on the outside from the drawer
    scratches(c, rand, { count: Math.round(ageN * 60), color: [120, 120, 125], alpha: 0.35, len: [6, 30],
      y0: cyOf(vRim + 0.05), y1: cyOf(Math.min(1, vRim + 0.4)) });
    if (nWear) truth.marks.push({ what: 'rim wear', amount: ageN });
  }

  if (chip) {   // the chip shows bare clay, rough, where the glaze broke away
    const cu = (((chip.angle % TAU) + TAU) % TAU) / TAU;
    const half = (chip.size / (TAU * R)) * W * 1.3;
    for (const shift of [0, -W, W]) {
      patch(c, { x: cu * W + shift, y: cyOf(vRim), rx: half, ry: (chip.size * pxV) * 1.2, color: clay, alpha: 0.95, edge: 0.25 });
    }
    truth.marks.push({ what: 'chip', angle: chip.angle, size: chip.size });
  }

  const mat = new THREE.MeshPhysicalMaterial({ map: texture(c, { wrap: true }), roughness: 0.32, clearcoat: 0.7,
    clearcoatRoughness: 0.12, side: THREE.DoubleSide });
  const body = new THREE.Mesh(geo, mat);

  // ---- the handle -----------------------------------------------------------------------------
  const Hd = M.handle;
  const hv = (x, sd = M.sd * 2) => x * (1 + rand.near(0, sd));
  const yTop = H * hv(Hd.top), yBot = H * hv(Hd.bottom), reach = hv(Hd.reach), thick = hv(Hd.thick);
  const sq = clamp(Hd.squareness + rand.near(0, 0.05));
  const rIn = (y) => wall(y) - thick * 0.6;
  const ctrl = [
    [rIn(yTop), yTop],
    [wall(yTop) + reach * (0.55 + 0.3 * sq), yTop + thick * 0.6],
    [wall((yTop + yBot) / 2) + reach, (yTop + yBot) / 2 + (yTop - yBot) * 0.1 * (1 - sq)],
    [wall(yBot) + reach * (0.6 + 0.3 * sq), yBot - thick * 0.3],
    [rIn(yBot), yBot],
  ];
  const curve = new THREE.CatmullRomCurve3(ctrl.map(([r, y]) => new THREE.Vector3(r, y, 0)), false, 'centripetal');
  const hgeo = new THREE.TubeGeometry(curve, 48, thick, 16, false);
  const hc = canvas(512, 128);
  const hx = rand.range(0, 100);
  paint(hc, (px, py) => glaze.map((k, i) => k * (1 + noise.fbm(px * 0.03 + hx, py * 0.05, 3) * M.mottle) + tint[i]));
  if (M.speckle) {
    const hctx = hc.getContext('2d');
    for (let k = 0; k < 512 * 128 * M.speckle; k++) {
      hctx.fillStyle = rgb([75, 52, 32], rand.range(0.4, 0.9));
      hctx.fillRect(rand() * 512, rand() * 128, rand.range(1, 2.5), rand.range(1, 2.5));
    }
  }
  if (age > 0) {   // where the fingers go: glaze dulled and slightly greyed along the inner curve
    patch(hc, { x: 512 * rand.range(0.4, 0.6), y: 64, rx: 140, ry: 60, color: mix(glaze, [150, 145, 135], 0.35),
      alpha: 0.5 * ageN });
    crazing(hc, rand, { count: Math.round(ageN * ageN * 30), color: [120, 110, 95], alpha: 0.25 });
  }
  const handle = new THREE.Mesh(hgeo, new THREE.MeshPhysicalMaterial({ map: texture(hc), roughness: 0.32,
    clearcoat: 0.7, clearcoatRoughness: 0.12 }));
  const hAngle = Math.PI / 2;   // the handle stands at phi = pi/2 (+x)
  handle.rotation.y = hAngle - Math.PI / 2;
  Object.assign(truth.handle, { top: yTop, bottom: yBot, reach, thick, squareness: sq });

  const g = new THREE.Group();
  g.add(body, handle);
  body.castShadow = body.receiveShadow = handle.castShadow = handle.receiveShadow = true;
  g.userData.truth = truth;
  return g;
}

// ---- books ---------------------------------------------------------------------------------------

// One book lying on its back cover: covers on +y/-y, spine on -x, page edges on +x and +-z.
// opts: { w, h, d, cover: '#hex', binding: 'cloth'|'paper', title, author, titleFamily, foil: '#hex',
//         age (years), sun: 0..1 (how much light its spine has had), damp: bool, dogEars: n }
export function book(rand, noise, opts) {
  const w = opts.w, h = opts.h, d = opts.d;
  const age = opts.age ?? 0, ageN = clamp(age / 40);
  const base = hex(opts.cover);
  const faded = mix(base, [205, 200, 185], 0.55);
  const foil = hex(opts.foil ?? '#d8c27a');
  const truth = { kind: 'book', w, h, d, cover: opts.cover, binding: opts.binding, title: opts.title,
    author: opts.author, age, marks: [] };

  // the front cover (as seen from above: canvas left is the spine edge, top is the far edge)
  const cc = canvas(512, Math.round(512 * h / w));
  if (opts.binding === 'cloth') cloth(cc, rand, noise, { base }); else paint(cc, () => base);
  const pxM = 512 / w;
  if (opts.binding === 'paper') {   // a printed jacket: a band and a rule
    const ctx = cc.getContext('2d');
    ctx.fillStyle = rgb(mix(base, [255, 255, 255], 0.75));
    ctx.fillRect(0, cc.height * 0.62, 512, cc.height * 0.2);
    ctx.fillStyle = rgb(mix(base, [0, 0, 0], 0.4));
    ctx.fillRect(40, cc.height * 0.15, 432, 3);
  }
  const titleCol = opts.binding === 'cloth' ? foil : hex(opts.titleColor ?? '#1d1d1d');
  const lines = opts.title.split('\n');
  lines.forEach((line, i) => print(cc, rand, noise, line, { x: 256, y: cc.height * (0.28 + i * 0.09),
    size: opts.titleSize ?? 40, family: opts.titleFamily ?? 'Georgia, serif', font: opts.titleFont ?? 'bold',
    color: titleCol, age: ageN * 0.45 }));
  print(cc, rand, noise, opts.author, { x: 256, y: cc.height * (opts.binding === 'paper' ? 0.72 : 0.82), size: 24,
    family: opts.titleFamily ?? 'Georgia, serif', font: 'normal', color: titleCol, age: ageN * 0.45, letterSpacing: 2 });

  // the spine: title along it, running from the top of the book to the bottom
  const sc = canvas(Math.round(96 * h / d), 96);   // along the spine x across it, at the face's own aspect
  if (opts.binding === 'cloth') cloth(sc, rand, noise, { base }); else paint(sc, () => base);
  print(sc, rand, noise, opts.title.replace('\n', ' '), { x: sc.width * 0.42, y: 48, size: 34,
    family: opts.titleFamily ?? 'Georgia, serif', font: opts.titleFont ?? 'bold', color: titleCol, age: ageN * 0.55 });
  print(sc, rand, noise, opts.author.split(' ').slice(-1)[0], { x: sc.width * 0.88, y: 48, size: 26,
    family: opts.titleFamily ?? 'Georgia, serif', font: 'normal', color: titleCol, age: ageN * 0.55 });

  // age: the spine bleached by the window, edges and corners rubbed through to the board
  const sun = (opts.sun ?? 0) * clamp(age / 15);
  if (sun > 0) {
    const sx = rand.range(0, 100);
    adjust(sc, (px, py, col) => mix(col, faded, clamp(sun * (0.8 + 0.2 * noise.fbm(px * 0.01 + sx, py * 0.02, 2)))));
    adjust(cc, (px, py, col) => mix(col, faded, clamp(sun * 0.6 * Math.max(0, 1 - px / 60))));   // the strip by the spine
    truth.marks.push({ what: 'sun-faded spine', amount: sun });
  }
  if (ageN > 0) {
    const board = [150, 135, 110];
    const corners = [[512, 0], [512, cc.height]];   // the two outer corners take the knocks
    for (const [x, y] of corners) {
      patch(cc, { x, y, rx: 20 + 70 * ageN * rand.range(0.6, 1.2), ry: 20 + 70 * ageN * rand.range(0.6, 1.2), color: board,
        alpha: 0.7 * ageN, edge: 0.7 });
    }
    for (const x of [0, sc.width]) {   // the head and tail of the spine fray
      patch(sc, { x, y: 48, rx: 40 * ageN + 4, ry: 60, color: board, alpha: 0.6 * ageN });
    }
    scratches(cc, rand, { count: Math.round(ageN * 25), color: mix(base, [255, 255, 255], 0.4), alpha: 0.4, len: [10, 80] });
    truth.marks.push({ what: 'worn corners', amount: ageN });
  }
  if (opts.ring) {   // someone set a cup down on it once
    ring(cc, rand, { x: 512 * opts.ring[0], y: cc.height * opts.ring[1], r: 0.038 * pxM, color: [90, 60, 35], alpha: 0.35, width: 4 });
    truth.marks.push({ what: 'cup ring', at: opts.ring });
  }

  // the page block: stacked edges, yellowing, foxing with age
  const pageTex = (wPx, hPx, lineAlong) => {
    const pc = canvas(wPx, hPx);
    paper(pc, rand, noise, { age: ageN, edgeYellow: false });
    const ctx = pc.getContext('2d');
    for (let k = 0; k < (lineAlong === 'x' ? hPx : wPx); k += rand.range(1.5, 3.5)) {   // the edges of leaves
      ctx.fillStyle = rgb([170, 160, 140], rand.range(0.1, 0.35));
      if (lineAlong === 'x') ctx.fillRect(0, k, wPx, 0.7); else ctx.fillRect(k, 0, 0.7, hPx);
    }
    for (let k = 0; k < ageN * 40; k++) {   // foxing: rust-brown spots
      patch(pc, { x: rand() * wPx, y: rand() * hPx, rx: rand.range(1, 4), ry: rand.range(1, 4), color: [150, 100, 60], alpha: 0.5 });
    }
    if (opts.damp) {   // a tide line where it once got wet
      ring(pc, rand, { x: wPx * rand.range(0.2, 0.8), y: hPx * 1.05, r: hPx * 0.7, color: [150, 120, 80], alpha: 0.4, width: 2 });
    }
    return texture(pc);
  };
  const along = pageTex(512, 64, 'x');   // +x and +-z faces show the leaves edge-on
  const back = canvas(256, Math.round(256 * h / w));
  if (opts.binding === 'cloth') cloth(back, rand, noise, { base }); else paint(back, () => mix(base, [0, 0, 0], 0.1));

  const std = (map, rough = 0.85) => new THREE.MeshStandardMaterial({ map, roughness: rough });
  const coverRough = opts.binding === 'cloth' ? 0.9 : 0.55;
  const mats = [std(along), std(texture(sc), coverRough), std(texture(cc), coverRough), std(texture(back), coverRough),
    std(along), std(along)];
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), mats);
  mesh.castShadow = mesh.receiveShadow = true;
  mesh.position.y = d / 2;
  const g = new THREE.Group();
  g.add(mesh);
  g.userData.truth = truth;
  return g;
}

// ---- a bottle --------------------------------------------------------------------------------------

// A glass bottle of oil with a paper label. opts: { glass: '#hex', liquid: '#hex', fill, label: {brand,
// product, note, color, ink}, age, drip: bool (oil has run down the label), torn: bool }
export function bottle(rand, noise, opts) {
  const age = opts.age ?? 0, ageN = clamp(age / 10);
  const R = 0.034 * (1 + rand.near(0, 0.01)), H = 0.24;
  const pts = [[0, 0.002], [R * 0.85, 0.002], [R, 0.012]];
  for (let i = 1; i <= 10; i++) pts.push([R, 0.012 + (H * 0.62 - 0.012) * i / 10]);
  for (let i = 1; i <= 14; i++) {   // the shoulder into the neck
    const s = i / 14;
    pts.push([R - (R - 0.0125) * (0.5 - 0.5 * Math.cos(Math.PI * s)), H * 0.62 + H * 0.2 * s]);
  }
  pts.push([0.0125, H * 0.95], [0.014, H * 0.955], [0.014, H * 0.975], [0.0125, H * 0.98]);
  const prof = resample(pts, 100);
  const glass = new THREE.Mesh(new THREE.LatheGeometry(prof.pts.map(([r, y]) => new THREE.Vector2(r, y)), 96),
    new THREE.MeshPhysicalMaterial({ color: opts.glass, transmission: 1, roughness: 0.04, thickness: 0.004, ior: 1.5,
      transparent: true, opacity: 1, side: THREE.DoubleSide }));
  const fillH = H * 0.62 * (opts.fill ?? 0.7);
  const liquid = new THREE.Mesh(new THREE.CylinderGeometry(R * 0.93, R * 0.93, fillH, 64),
    new THREE.MeshPhysicalMaterial({ color: opts.liquid, transmission: 0.6, roughness: 0.1, thickness: 0.05 }));
  liquid.position.y = fillH / 2 + 0.004;
  liquid.userData.gerund = 'pooling';   // the oil is doing something else than its glass
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.0152, 0.0152, 0.022, 32),
    new THREE.MeshStandardMaterial({ color: opts.cap ?? '#3b3b3b', roughness: 0.5, metalness: 0.3 }));
  cap.position.y = H * 0.975 + 0.008;

  // the label: a band of paper wrapped two thirds of the way round
  const L = opts.label;
  const lw = 1024, lh = 512, arc = TAU * 0.62;
  const lc = canvas(lw, lh);
  paper(lc, rand, noise, { base: hex(L.color ?? '#efe6cf'), age: ageN * 0.8 });
  const pxU = lw / (arc * R), pxV = lh / 0.1;
  const ink = hex(L.ink ?? '#2a3b22');
  const ctx = lc.getContext('2d');
  ctx.strokeStyle = rgb(ink);
  ctx.lineWidth = 3;
  ctx.strokeRect(30, 30, lw - 60, lh - 60);
  print(lc, rand, noise, L.brand, { x: lw / 2, y: lh * 0.3, size: 0.016 * pxV, sx: pxU / pxV, family: 'Georgia, serif',
    font: 'italic', color: ink, age: ageN * 0.5 });
  print(lc, rand, noise, L.product, { x: lw / 2, y: lh * 0.55, size: 0.02 * pxV, sx: pxU / pxV, family: 'Georgia, serif',
    font: 'bold', color: ink, age: ageN * 0.5, letterSpacing: 4 });
  print(lc, rand, noise, L.note, { x: lw / 2, y: lh * 0.76, size: 0.008 * pxV, sx: pxU / pxV,
    family: 'Helvetica, Arial, sans-serif', font: 'normal', color: ink, age: ageN * 0.5 });
  const truth = { kind: 'bottle', glass: opts.glass, label: L, age, marks: [] };
  if (opts.drip) {   // oil has run down the label: translucent, darker, a long streak
    const x0 = lw * rand.range(0.2, 0.8);
    for (let y = 0; y < lh; y += 4) {
      patch(lc, { x: x0 + noise.fbm(y * 0.01, 3, 2) * 30, y, rx: 26 - y * 0.02, ry: 8, color: [170, 140, 70], alpha: 0.22 });
    }
    truth.marks.push({ what: 'oil drip', at: x0 / lw });
  }
  const alpha = canvas(lw, lh);   // a torn corner: the paper simply is not there
  alpha.getContext('2d').fillStyle = '#fff';
  alpha.getContext('2d').fillRect(0, 0, lw, lh);
  if (opts.torn) {
    const a = alpha.getContext('2d');
    a.fillStyle = '#000';
    a.beginPath();
    a.moveTo(lw, lh * 0.55);
    for (let k = 0; k <= 12; k++) a.lineTo(lw - k * 14 - rand.range(0, 10), lh * 0.55 + k * 19 + rand.range(-6, 6));
    a.lineTo(lw, lh);
    a.fill();
    truth.marks.push({ what: 'torn label corner' });
  }
  const labelMat = new THREE.MeshStandardMaterial({ map: texture(lc), alphaMap: texture(alpha, { srgb: false }),
    alphaTest: 0.5, roughness: 0.8, side: THREE.DoubleSide });
  const label = new THREE.Mesh(new THREE.CylinderGeometry(R * 1.004, R * 1.004, 0.1, 96, 1, true, -arc / 2, arc), labelMat);   // centred on +z
  label.position.y = H * 0.33;
  const g = new THREE.Group();
  for (const m of [glass, liquid, cap, label]) { m.castShadow = true; m.receiveShadow = true; g.add(m); }
  g.userData.truth = truth;
  return g;
}

// ---- the table -------------------------------------------------------------------------------------

export function table(rand, noise, { w = 1.3, d = 0.85, age = 12 }) {
  const c = canvas(2048, Math.round(2048 * d / w));
  wood(c, rand, noise, { base: hex('#9a6a42'), dark: hex('#5c3a20'), rings: 7 });
  const ageN = clamp(age / 30);
  scratches(c, rand, { count: Math.round(260 * ageN), color: [210, 180, 140], alpha: 0.35, len: [20, 160], angle: 0 });
  scratches(c, rand, { count: Math.round(80 * ageN), color: [40, 25, 15], alpha: 0.3, len: [10, 50] });
  const pxM = c.width / w;
  const truth = { kind: 'table', age, marks: [] };
  for (let k = 0; k < Math.round(5 * ageN); k++) {   // rings from glasses and mugs set down wet
    const x = rand.range(0.15, 0.85) * c.width, y = rand.range(0.15, 0.85) * c.height;
    ring(c, rand, { x, y, r: rand.range(0.03, 0.045) * pxM, color: [225, 210, 185], alpha: 0.3, width: 5 });
    truth.marks.push({ what: 'water ring', at: [x / c.width, y / c.height] });
  }
  // where elbows and plates go, the finish is worn pale along the near edge
  patch(c, { x: c.width * 0.5, y: c.height * 0.97, rx: c.width * 0.35, ry: c.height * 0.12, color: [190, 150, 110], alpha: 0.35 * ageN });
  const mat = new THREE.MeshStandardMaterial({ map: texture(c), roughness: 0.55 });
  const top = new THREE.Mesh(new THREE.BoxGeometry(w, 0.035, d), mat);
  top.position.y = -0.0175;
  top.receiveShadow = true;
  const g = new THREE.Group();
  g.add(top);
  g.userData.truth = truth;
  return g;
}
