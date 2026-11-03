// Procedural surfaces: glaze, clay, wood, cloth, paper, glass labels, and what age does to each
// (fading, wear where hands go, stains, crazing, flaking print). Painted in UV space on canvases.
import * as THREE from 'three';

export function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

export function texture(c, { wrap = false, srgb = true } = {}) {
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  if (wrap) t.wrapS = THREE.RepeatWrapping;
  t.anisotropy = 8;
  t.needsUpdate = true;
  return t;
}

export const clamp = (x, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, x));
export const mix = (a, b, t) => a.map((x, i) => x + (b[i] - x) * t);

export function hex(h) {
  const n = parseInt(h.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function rgb(c, a = 1) {
  return `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
}

// Fill a canvas pixel by pixel: fn(x, y) -> [r, g, b] (0..255).
export function paint(c, fn) {
  const ctx = c.getContext('2d');
  const img = ctx.createImageData(c.width, c.height);
  const d = img.data;
  for (let y = 0; y < c.height; y++) {
    for (let x = 0; x < c.width; x++) {
      const [r, g, b] = fn(x, y);
      const i = (y * c.width + x) * 4;
      d[i] = r; d[i + 1] = g; d[i + 2] = b; d[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return ctx;
}

// Adjust existing pixels: fn(x, y, [r, g, b]) -> [r, g, b].
export function adjust(c, fn) {
  const ctx = c.getContext('2d');
  const img = ctx.getImageData(0, 0, c.width, c.height);
  const d = img.data;
  for (let y = 0; y < c.height; y++) {
    for (let x = 0; x < c.width; x++) {
      const i = (y * c.width + x) * 4;
      const [r, g, b] = fn(x, y, [d[i], d[i + 1], d[i + 2]]);
      d[i] = clamp(r, 0, 255); d[i + 1] = clamp(g, 0, 255); d[i + 2] = clamp(b, 0, 255);
    }
  }
  ctx.putImageData(img, 0, 0);
}

// Fine branching cracks in a glaze (crazing): denser with age.
export function crazing(c, rand, { x0 = 0, y0 = 0, x1 = c.width, y1 = c.height, count = 40, color = [90, 80, 60], alpha = 0.35 }) {
  const ctx = c.getContext('2d');
  ctx.lineWidth = 0.8;
  for (let n = 0; n < count; n++) {
    let x = rand.range(x0, x1), y = rand.range(y0, y1);
    let a = rand() * Math.PI * 2;
    ctx.strokeStyle = rgb(color, alpha * rand.range(0.4, 1));
    ctx.beginPath();
    ctx.moveTo(x, y);
    const steps = rand.int(6, 22);
    for (let s = 0; s < steps; s++) {
      a += rand.near(0, 0.6);
      x += Math.cos(a) * rand.range(3, 9);
      y += Math.sin(a) * rand.range(3, 9);
      if (x < x0 || x > x1 || y < y0 || y > y1) break;
      ctx.lineTo(x, y);
      if (rand.chance(0.12)) {   // a branch
        ctx.moveTo(x, y);
      }
    }
    ctx.stroke();
  }
}

// Text printed or stamped onto a surface, then aged: faded toward the surface and flaked away
// where the noise says the print wore through. sx, sy: pixels per unit length across and along
// (UV space is not square on a lathe), so letters keep their shape on the object.
export function print(c, rand, noise, text, {
  x, y, size, font = 'bold', family = 'Helvetica, Arial, sans-serif', color = [30, 30, 30],
  sx = 1, sy = 1, rotate = 0, age = 0, align = 'center', letterSpacing = 0,
}) {
  const tmp = canvas(c.width, c.height);
  const t = tmp.getContext('2d');
  t.save();
  t.translate(x, y);
  t.rotate(rotate);
  t.scale(sx, sy);
  t.font = `${font} ${size}px ${family}`;
  t.textAlign = align;
  t.textBaseline = 'middle';
  t.fillStyle = rgb(color);
  if (letterSpacing) t.letterSpacing = `${letterSpacing}px`;
  t.fillText(text, 0, 0);
  t.restore();
  if (age > 0) {   // fade and flake: the print wears where hands and washing reach it
    const img = t.getImageData(0, 0, tmp.width, tmp.height);
    const d = img.data;
    const seed = rand.range(0, 1000);
    for (let py = 0; py < tmp.height; py++) {
      for (let px = 0; px < tmp.width; px++) {
        const i = (py * tmp.width + px) * 4 + 3;
        if (!d[i]) continue;
        const flake = noise.fbm(px * 0.06 + seed, py * 0.06, 4);
        const keep = clamp(1 - age * 0.55 - (flake > 0.35 - age * 0.5 ? age * 1.2 : 0));
        d[i] = d[i] * keep;
      }
    }
    t.putImageData(img, 0, 0);
  }
  c.getContext('2d').drawImage(tmp, 0, 0);
}

// A soft-edged patch: wear, a stain, a faded area, a grease mark.
export function patch(c, { x, y, rx, ry, color, alpha, rotate = 0, edge = 0.6, mode = 'source-over' }) {
  const ctx = c.getContext('2d');
  ctx.save();
  ctx.globalCompositeOperation = mode;
  ctx.translate(x, y);
  ctx.rotate(rotate);
  ctx.scale(1, ry / rx);
  const g = ctx.createRadialGradient(0, 0, rx * (1 - edge), 0, 0, rx);
  g.addColorStop(0, rgb(color, alpha));
  g.addColorStop(1, rgb(color, 0));
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(0, 0, rx, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

// A ring left by something wet set down: a darker rim, irregular, with a fainter body.
export function ring(c, rand, { x, y, r, color, alpha, width = 3 }) {
  const ctx = c.getContext('2d');
  ctx.save();
  for (let k = 0; k < 3; k++) {
    ctx.strokeStyle = rgb(color, alpha * rand.range(0.5, 1));
    ctx.lineWidth = width * rand.range(0.6, 1.4);
    ctx.beginPath();
    const start = rand() * Math.PI * 2, span = Math.PI * rand.range(1.3, 2);
    for (let a = 0; a <= span; a += 0.05) {
      const rr = r * (1 + 0.03 * Math.sin(a * 3 + k) + rand.near(0, 0.004));
      const px = x + Math.cos(start + a) * rr, py = y + Math.sin(start + a) * rr;
      if (a === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }
  ctx.restore();
}

// Scratches: thin straight-ish lines, lighter or darker than the surface.
export function scratches(c, rand, { count, color, alpha, len = [10, 60], x0 = 0, y0 = 0, x1 = c.width, y1 = c.height, angle = null }) {
  const ctx = c.getContext('2d');
  for (let n = 0; n < count; n++) {
    const x = rand.range(x0, x1), y = rand.range(y0, y1);
    const a = angle === null ? rand() * Math.PI : angle + rand.near(0, 0.25);
    const l = rand.range(len[0], len[1]);
    ctx.strokeStyle = rgb(color, alpha * rand.range(0.3, 1));
    ctx.lineWidth = rand.range(0.5, 1.4);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + Math.cos(a) * l * 0.5 + rand.near(0, 2), y + Math.sin(a) * l * 0.5 + rand.near(0, 2),
      x + Math.cos(a) * l, y + Math.sin(a) * l);
    ctx.stroke();
  }
}

// Wood: boards laid along x, each its own cut of the tree: long grain lines that drift and pinch,
// fine pores, a slightly different tone per board, and the seams between them.
export function wood(c, rand, noise, { base, dark, boards = 6 }) {
  const bw = c.height / boards;
  const per = [...Array(boards)].map(() => ({ o: rand.range(0, 500), tone: rand.near(0, 0.06), f: rand.range(0.035, 0.07) }));
  paint(c, (x, y) => {
    const k = Math.min(boards - 1, Math.floor(y / bw));
    const b = per[k];
    const drift = noise.fbm(x * 0.0012 + b.o, y * 0.004, 3) * 60 + noise.fbm(x * 0.006 + b.o, y * 0.01, 2) * 6;
    const g = ((y + drift) * b.f) % 1;
    const line = Math.pow(1 - Math.abs(g * 2 - 1), 10);   // a thin dark latewood line
    const pores = noise.fbm(x * 0.03 + b.o, y * 0.9, 2) * 0.5 + 0.5;
    const t = clamp(0.18 + 0.35 * line + 0.18 * pores + b.tone + noise.fbm(x * 0.0008, y * 0.002 + b.o, 2) * 0.12);
    const seam = Math.abs((y % bw) - bw / 2) > bw / 2 - 1.5 ? 0.55 : 0;   // the gap between boards
    return mix(mix(base, dark, t), [35, 22, 12], seam);
  });
}

// Woven cloth (book covers): a fine warp and weft, and fibre mottle.
export function cloth(c, rand, noise, { base, weave = 0.08 }) {
  const ox = rand.range(0, 100);
  paint(c, (x, y) => {
    const w = (Math.sin(x * 1.6) * Math.sin(y * 1.6) > 0 ? 1 : -1) * weave;
    const m = noise.fbm(x * 0.02 + ox, y * 0.02, 4) * 0.08;
    const k = 1 + w + m;
    return base.map((v) => v * k);
  });
}

// Paper: off-white with fibre, yellowed toward the edges with age.
export function paper(c, rand, noise, { base = [242, 236, 222], age = 0, edgeYellow = true }) {
  const ox = rand.range(0, 100);
  const yellow = [214, 190, 140];
  paint(c, (x, y) => {
    const f = noise.fbm(x * 0.05 + ox, y * 0.05, 3) * 0.04;
    const ex = Math.min(x, c.width - x) / c.width, ey = Math.min(y, c.height - y) / c.height;
    const edge = edgeYellow ? clamp(1 - Math.min(ex, ey) * 8) : 0;
    const t = clamp(age * 0.35 + edge * age * 0.5 + noise.fbm(x * 0.01, y * 0.01 + ox, 3) * age * 0.2);
    return mix(base, yellow, t).map((v) => v * (1 + f));
  });
}
