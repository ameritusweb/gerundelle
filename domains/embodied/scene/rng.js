// Seeded randomness and value noise: the scene is the same scene every time it is built from the
// same seed, so what the mind finds in it can be checked against what was put there.

export function makeRand(seed) {
  let a = seed >>> 0;
  const next = () => {   // mulberry32
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  next.range = (lo, hi) => lo + (hi - lo) * next();
  next.int = (lo, hi) => Math.floor(next.range(lo, hi + 1));
  next.pick = (xs) => xs[Math.floor(next() * xs.length)];
  next.gauss = () => {   // Box-Muller: real variation clusters near the norm
    const u = Math.max(next(), 1e-9), v = next();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  next.near = (mean, sd) => mean + sd * next.gauss();
  next.chance = (p) => next() < p;
  return next;
}

export function makeNoise(rand) {
  const perm = new Uint8Array(512);
  const p = [...Array(256).keys()];
  for (let i = 255; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [p[i], p[j]] = [p[j], p[i]];
  }
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
  const grad = (h) => (h / 255) * 2 - 1;
  const fade = (t) => t * t * (3 - 2 * t);
  const lerp = (a, b, t) => a + (b - a) * t;

  function value(x, y) {   // value noise in [-1, 1]
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const X = xi & 255, Y = yi & 255;
    const a = grad(perm[perm[X] + Y]), b = grad(perm[perm[X + 1] + Y]);
    const c = grad(perm[perm[X] + Y + 1]), d = grad(perm[perm[X + 1] + Y + 1]);
    const u = fade(xf), v = fade(yf);
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  }

  function fbm(x, y, octaves = 4) {
    let s = 0, amp = 0.5, f = 1, norm = 0;
    for (let i = 0; i < octaves; i++) {
      s += amp * value(x * f, y * f);
      norm += amp;
      amp *= 0.5;
      f *= 2;
    }
    return s / norm;
  }

  // periodic in x with period px (for textures that wrap around a lathe)
  function fbmWrap(x, y, px, octaves = 4) {
    const t = x / px;
    return (1 - t) * fbm(x, y, octaves) + t * fbm(x - px, y, octaves);
  }

  return { value, fbm, fbmWrap };
}
