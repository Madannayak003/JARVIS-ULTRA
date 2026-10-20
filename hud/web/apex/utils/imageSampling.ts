import * as THREE from 'three';
import { classifyPaletteBucket, smooth01, srgbToLinear } from './humanoidLogic';

export const ASSET_PATHS = {
  backdrop: '/humanoid/backdrop-v1.webp',
  idle: '/humanoid/apex-idle-v1.webp',
  listening: '/humanoid/apex-listening-v1.webp',
  thinking: '/humanoid/apex-thinking-v1.webp',
  speaking: '/humanoid/apex-speaking-v1.webp',
  strong: '/humanoid/apex-speaking-strong-v1.webp',
  assembly25: '/humanoid/apex-assembly-25-v1.webp',
  assembly60: '/humanoid/apex-assembly-60-v1.webp',
} as const;

export const PALETTE_SRGB = ['#19ddff', '#bfeeff', '#ffb54d', '#ffd98a'] as const;

export const PALETTE_LINEAR: [number, number, number][] = PALETTE_SRGB.map((hex) => [
  srgbToLinear(parseInt(hex.slice(1, 3), 16) / 255),
  srgbToLinear(parseInt(hex.slice(3, 5), 16) / 255),
  srgbToLinear(parseInt(hex.slice(5, 7), 16) / 255),
]);

export interface LoadedHumanoidAssets {
  idle: HTMLImageElement;
  listening: HTMLImageElement;
  thinking: HTMLImageElement;
  speaking: HTMLImageElement;
  strong: HTMLImageElement;
  assembly25: HTMLImageElement;
  assembly60: HTMLImageElement;
  backdrop: HTMLImageElement;
}

export function loadAllHumanoidAssets(): Promise<LoadedHumanoidAssets> {
  const entries = Object.entries(ASSET_PATHS) as [keyof LoadedHumanoidAssets, string][];
  const result: Partial<LoadedHumanoidAssets> = {};

  return Promise.all(
    entries.map(
      ([key, src]) =>
        new Promise<void>((resolve, reject) => {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.decoding = 'async';
          img.onload = () => {
            result[key] = img;
            resolve();
          };
          img.onerror = () => reject(new Error(`Failed to load required artwork asset: ${src}`));
          img.src = src;
        })
    )
  ).then(() => result as LoadedHumanoidAssets);
}

/**
 * Cleans sparse stray outer pixels while preserving silhouette and crown particle dust (bU).
 */
export function cleanIdlePlate(img: HTMLImageElement): HTMLCanvasElement {
  const w = Math.min(1100, img.width || 1100);
  const h = Math.round((w * (img.height || w)) / (img.width || w));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, w, h);
  const imgData = ctx.getImageData(0, 0, w, h);
  const data = imgData.data;

  const lum = new Float32Array(w * h);
  for (let i = 0, p = 0; p < w * h; i += 4, p++) {
    lum[p] = data[i] + data[i + 1] + data[i + 2];
  }

  const integral = new Float64Array((w + 1) * (h + 1));
  for (let y = 0; y < h; y++) {
    let rowSum = 0;
    for (let x = 0; x < w; x++) {
      rowSum += lum[y * w + x];
      integral[(y + 1) * (w + 1) + (x + 1)] = integral[y * (w + 1) + (x + 1)] + rowSum;
    }
  }

  const boxAvg = (cx: number, cy: number, r: number) => {
    const x0 = Math.max(0, cx - r);
    const y0 = Math.max(0, cy - r);
    const x1 = Math.min(w, cx + r + 1);
    const y1 = Math.min(h, cy + r + 1);
    return (
      (integral[y1 * (w + 1) + x1] -
        integral[y0 * (w + 1) + x1] -
        integral[y1 * (w + 1) + x0] +
        integral[y0 * (w + 1) + x0]) /
      ((x1 - x0) * (y1 - y0))
    );
  };

  const isCyanBody = (x: number, y: number) => {
    const idx = (y * w + x) * 4;
    return lum[y * w + x] > 80 && data[idx + 2] >= data[idx];
  };

  const margin = Math.round(w * 0.015);
  for (let y = 0; y < h; y++) {
    let left = -1;
    let right = -1;
    for (let x = 2; x < w - 2; x++) {
      if (isCyanBody(x, y)) {
        left = x;
        break;
      }
    }
    for (let x = w - 3; x >= 2; x--) {
      if (isCyanBody(x, y)) {
        right = x;
        break;
      }
    }
    for (let x = 0; x < w; x++) {
      if (
        (left === -1 || x < left - margin || x > right + margin) &&
        lum[y * w + x] > 30 &&
        boxAvg(x, y, 6) < 42
      ) {
        const idx = (y * w + x) * 4;
        data[idx] *= 0.24;
        data[idx + 1] *= 0.24;
        data[idx + 2] *= 0.24;
      }
    }
  }
  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

/**
 * Removes solid black background rectangles from assembly reference plates
 * so they composite transparently over the mountain backdrop.
 */
export function cleanAssemblyPlate(img: HTMLImageElement): HTMLCanvasElement {
  const w = Math.min(1100, img.width || 1100);
  const h = Math.round((w * (img.height || w)) / (img.width || w));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, w, h);
  const imgData = ctx.getImageData(0, 0, w, h);
  const data = imgData.data;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const lum = r + g + b;
    if (lum < 28) {
      data[i + 3] = 0;
    } else {
      const a = Math.min(255, (lum - 28) * 1.6);
      data[i + 3] = Math.min(data[i + 3], a);
    }
  }

  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

/**
 * Extracts golden neck and upper chest filaments for additive living pulse (RU).
 */
export function extractGoldVeins(img: HTMLImageElement | HTMLCanvasElement): HTMLCanvasElement {
  const w = Math.min(1024, img.width || 1024);
  const h = Math.round((w * (img.height || w)) / (img.width || w));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, w, h);
  const imgData = ctx.getImageData(0, 0, w, h);
  const data = imgData.data;
  const neckRow = Math.round(h * 0.56);

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      if (!(y >= neckRow && data[idx] > 78 && data[idx] > data[idx + 2] * 1.55)) {
        data[idx + 3] = 0;
      }
    }
  }
  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

/**
 * Extracts alpha-mapped concentric listening rings from apex-listening-v1.webp.
 */
export function extractListeningRings(img: HTMLImageElement): HTMLCanvasElement {
  const w = Math.min(1024, img.width || 1024);
  const h = Math.round((w * (img.height || w)) / (img.width || w));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, w, h);
  const imgData = ctx.getImageData(0, 0, w, h);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    data[i + 3] = Math.min(255, Math.max(data[i], data[i + 1], data[i + 2]) * 1.5);
  }
  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

export interface EdgeSample {
  x: number;
  y: number;
  nx: number;
  ny: number;
}

export interface BoilMote2D {
  e: EdgeSample;
  t: number;
  rate: number;
  amp: number;
  wob: number;
  size: number;
  bright: boolean;
}

export function sampleSilhouetteEdges(img: HTMLImageElement | HTMLCanvasElement): EdgeSample[] {
  const canvas = document.createElement('canvas');
  canvas.width = 384;
  canvas.height = 384;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, 384, 384);
  const data = ctx.getImageData(0, 0, 384, 384).data;
  const isEdge = (x: number, y: number) => {
    const i = (y * 384 + x) * 4;
    return data[i] + data[i + 1] + data[i + 2] > 80 && data[i + 2] >= data[i];
  };

  const edges: EdgeSample[] = [];
  for (let y = 6; y < 380; y += 1) {
    for (let x = 4; x < 380; x++) {
      if (isEdge(x, y)) {
        edges.push({ x: x / 384, y: y / 384, nx: -1, ny: 0 });
        break;
      }
    }
    for (let x = 379; x >= 4; x--) {
      if (isEdge(x, y)) {
        edges.push({ x: x / 384, y: y / 384, nx: 1, ny: 0 });
        break;
      }
    }
  }
  for (let x = 6; x < 378; x += 2) {
    for (let y = 4; y < 380; y++) {
      if (isEdge(x, y)) {
        edges.push({ x: x / 384, y: y / 384, nx: 0, ny: -1 });
        break;
      }
    }
  }
  return edges;
}

export function createEdgeBoilMotes(edges: EdgeSample[]): BoilMote2D[] {
  if (!edges.length) return [];
  let seed = 51733;
  const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);
  return Array.from({ length: 380 }, () => ({
    e: edges[Math.floor(rng() * edges.length)],
    t: rng() * 8,
    rate: 0.22 + rng() * 0.5,
    amp: 0.012 + rng() * 0.026,
    wob: 0.003 + rng() * 0.006,
    size: 0.6 + rng() * 1.3,
    bright: rng() < 0.15,
  }));
}

export interface AssemblyData {
  n: number;
  aspectRatio: number;
  x: Float32Array;
  y: Float32Array;
  sx: Float32Array;
  sy: Float32Array;
  c1x: Float32Array;
  c1y: Float32Array;
  c2x: Float32Array;
  c2y: Float32Array;
  delay: Float32Array;
  dur: Float32Array;
  size: Float32Array;
  buckets: { color: string; idx: Uint32Array }[];
}

/**
 * Samples up to 9,500 particles with cubic Bézier birth trajectories from the lower-chest source.
 */
export function sampleAssemblyParticles(img: HTMLImageElement | HTMLCanvasElement): AssemblyData {
  const h = Math.round((372 * (img.height || 372)) / (img.width || 372));
  const aspectRatio = (img.width || 372) / (img.height || 372);
  const canvas = document.createElement('canvas');
  canvas.width = 372;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, 372, h);
  const data = ctx.getImageData(0, 0, 372, h).data;

  const candidates: [number, number, number, number, number][] = [];
  for (let y = 2; y < h - 2; y++) {
    for (let x = 2; x < 370; x++) {
      const i = (y * 372 + x) * 4;
      const sum = data[i] + data[i + 1] + data[i + 2];
      if (sum > 95) {
        candidates.push([x / 372, y / h, data[i], data[i + 2], sum]);
      }
    }
  }

  const count = Math.min(9500, candidates.length);
  let seed = 977231;
  const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);
  const stride = candidates.length / Math.max(1, count);

  const out: AssemblyData = {
    n: 0,
    aspectRatio,
    x: new Float32Array(count),
    y: new Float32Array(count),
    sx: new Float32Array(count),
    sy: new Float32Array(count),
    c1x: new Float32Array(count),
    c1y: new Float32Array(count),
    c2x: new Float32Array(count),
    c2y: new Float32Array(count),
    delay: new Float32Array(count),
    dur: new Float32Array(count),
    size: new Float32Array(count),
    buckets: [],
  };

  const bucketLists: number[][] = [[], [], [], []];
  for (let i = 0; i < count; i++) {
    const [px, py, r, b, sum] =
      candidates[Math.min(candidates.length - 1, Math.floor(i * stride + rng() * stride))];
    const idx = out.n++;
    out.x[idx] = px;
    out.y[idx] = py;
    out.sx[idx] = 0.5 + (rng() * 2 - 1) * 0.028;
    out.sy[idx] = 0.94 + (rng() * 2 - 1) * 0.016;
    out.c1x[idx] = 0.88 + rng() * 0.28;
    out.c1y[idx] = 0.72 + rng() * 0.16;
    out.c2x[idx] = 0.78 + rng() * 0.3;
    out.c2y[idx] = 0.12 + rng() * 0.22;
    out.delay[idx] = ((px - 0.06) / 0.88) * 4.6 + rng() * 0.45;
    out.dur[idx] = 1.0 + rng() * 0.4;
    out.size[idx] = 1.2 + (sum / 765) * 1.5;

    const bucket = r > b * 1.4 ? (r > 175 ? 3 : 2) : sum > 430 ? 1 : 0;
    bucketLists[bucket].push(idx);
  }

  out.buckets = bucketLists.map((list, idx) => ({
    color: PALETTE_SRGB[idx],
    idx: Uint32Array.from(list),
  }));

  return out;
}

function compositeMoodPlate(
  imgs: {
    idle: HTMLCanvasElement | HTMLImageElement;
    thinking: HTMLImageElement;
    speaking: HTMLImageElement;
    strong: HTMLImageElement;
  },
  mode: 'idle' | 'thinking' | 'speaking' | 'strong',
  w: number,
  h: number
): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, w, h);
  ctx.drawImage(imgs.idle, 0, 0, w, h);

  const blendFaceEllipse = (
    overlay: HTMLImageElement,
    alpha: number,
    cx: number,
    cy: number,
    rx: number,
    ry: number
  ) => {
    if (!overlay) return;
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(w * cx, h * cy, w * rx, h * ry, 0, 0, Math.PI * 2);
    ctx.clip();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = alpha;
    ctx.drawImage(overlay, 0, 0, w, h);
    ctx.restore();
    ctx.globalAlpha = 1;
  };

  if (mode === 'thinking') {
    blendFaceEllipse(imgs.thinking, 0.628, 0.5, 0.4, 0.19, 0.2);
  } else if (mode === 'speaking') {
    blendFaceEllipse(imgs.speaking, 0.55, 0.5, 0.43, 0.2, 0.19);
  } else if (mode === 'strong') {
    blendFaceEllipse(imgs.speaking, 0.42, 0.5, 0.43, 0.2, 0.19);
    blendFaceEllipse(imgs.strong, 0.68, 0.5, 0.43, 0.21, 0.2);
  }

  return canvas;
}

export interface Humanoid3DFigureData {
  count: number;
  frontCount: number;
  backCount: number;
  dustCount: number;
  boilCount: number;
  pivotY: number;
  palette: [number, number, number][];
  plates: {
    idle: HTMLCanvasElement;
    thinking: HTMLCanvasElement;
    speaking: HTMLCanvasElement;
    strong: HTMLCanvasElement;
  };
  pos: Float32Array;
  size: Float32Array;
  w: Float32Array;
  kind: Uint8Array;
  boil: Float32Array;
  bright: Uint8Array;
  bucket: Uint8Array;
  nx: Float32Array;
  shadow: HTMLCanvasElement;
}

/**
 * Builds the 3D particle geometry buffers and texture plates from the reference artworks (IU).
 */
export function buildHumanoid3DFigure(
  imgs: {
    idle: HTMLCanvasElement | HTMLImageElement;
    thinking: HTMLImageElement;
    speaking: HTMLImageElement;
    strong: HTMLImageElement;
  },
  resolutionWidth = 900
): Humanoid3DFigureData {
  const W = resolutionWidth;
  const H = Math.round((W * (imgs.idle.height || W)) / (imgs.idle.width || W));

  const idlePlate = compositeMoodPlate(imgs, 'idle', W, H);
  const thinkingPlate = compositeMoodPlate(imgs, 'thinking', W, H);
  const speakingPlate = compositeMoodPlate(imgs, 'speaking', W, H);
  const strongPlate = compositeMoodPlate(imgs, 'strong', W, H);

  const getPixels = (c: HTMLCanvasElement) => c.getContext('2d')!.getImageData(0, 0, W, H).data;
  const dIdle = getPixels(idlePlate);
  const dThink = getPixels(thinkingPlate);
  const dSpeak = getPixels(speakingPlate);
  const dStrong = getPixels(strongPlate);

  const sumRgb = (arr: Uint8ClampedArray, idx: number) => arr[idx] + arr[idx + 1] + arr[idx + 2];

  const leftEdge = new Int16Array(H).fill(-1);
  const rightEdge = new Int16Array(H).fill(-1);
  const topEdge = new Int16Array(W).fill(-1);

  const isRowSpan = (x: number, y: number) =>
    sumRgb(dIdle, (y * W + x) * 4) > 40 &&
    sumRgb(dIdle, (y * W + x + 1) * 4) > 40 &&
    sumRgb(dIdle, (y * W + x + 2) * 4) > 40;

  const isColSpan = (x: number, y: number) =>
    sumRgb(dIdle, (y * W + x) * 4) > 40 &&
    sumRgb(dIdle, ((y + 1) * W + x) * 4) > 40 &&
    sumRgb(dIdle, ((y + 2) * W + x) * 4) > 40;

  for (let y = 0; y < H - 2; y++) {
    for (let x = 2; x < W - 4; x++) {
      if (isRowSpan(x, y)) {
        leftEdge[y] = x;
        break;
      }
    }
    for (let x = W - 5; x >= 2; x--) {
      if (isRowSpan(x, y)) {
        rightEdge[y] = x;
        break;
      }
    }
  }

  let crownStartRow = 2;
  for (let y = 2; y < H - 2; y++) {
    let lit = 0;
    for (let x = 2; x < W - 2; x++) {
      if (sumRgb(dIdle, (y * W + x) * 4) > 120) lit++;
    }
    if (lit >= W * 0.14) {
      crownStartRow = Math.max(2, y - 8);
      break;
    }
  }

  for (let x = 2; x < W - 2; x++) {
    for (let y = crownStartRow; y < H - 4; y++) {
      if (isColSpan(x, y)) {
        topEdge[x] = y;
        break;
      }
    }
  }

  // Locate neck narrowest row for natural head turning pivot
  let neckRow = Math.round(H * 0.64);
  let minSpan = 1e9;
  for (let y = Math.round(H * 0.45); y < Math.round(H * 0.8); y++) {
    if (leftEdge[y] >= 0 && rightEdge[y] > leftEdge[y] && rightEdge[y] - leftEdge[y] < minSpan) {
      minSpan = rightEdge[y] - leftEdge[y];
      neckRow = y;
    }
  }

  const neckNormY = neckRow / H;
  const headWeightAt = (py: number) => smooth01((neckNormY - py) / 0.17);

  const depthAt = (ndcX: number, row: number, weight: number) => {
    if (leftEdge[row] < 0 || rightEdge[row] <= leftEdge[row]) return 0;
    const centerNdcX = (leftEdge[row] + rightEdge[row]) / W - 1;
    const halfWidth = Math.min(0.6, (rightEdge[row] - leftEdge[row]) / W);
    const zSphere = Math.sqrt(
      Math.max(0, halfWidth * halfWidth - (ndcX - centerNdcX) * (ndcX - centerNdcX))
    );
    const py = row / H;
    const depthScale =
      py < neckNormY - 0.04 ? 0.85 : Math.max(0.28, 0.85 - (py - (neckNormY - 0.04)) * 3.2);
    return zSphere * (depthScale + 0.1 * weight) * (1 - 0.06 * weight);
  };

  const primaryPixels: number[] = [];
  const haloPixels: number[] = [];
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      const idx4 = (y * W + x) * 4;
      const maxSum = Math.max(
        sumRgb(dIdle, idx4),
        sumRgb(dThink, idx4),
        sumRgb(dSpeak, idx4),
        sumRgb(dStrong, idx4)
      );
      if (maxSum > 60) {
        primaryPixels.push(y * W + x);
      } else if (maxSum > 16 && (x & 1) === 0 && (y & 1) === 0) {
        haloPixels.push(y * W + x);
      }
    }
  }

  const frontCount = primaryPixels.length + haloPixels.length;
  const backCount = Math.round(frontCount * 0.16);
  const dustCount = 10000;

  const contourNormals: [number, number, number, number][] = [];
  const clampArr = (arr: Int16Array, idx: number, lo: number, hi: number) =>
    arr[Math.max(lo, Math.min(hi, idx))];

  const maxBoilRow = Math.floor(H * 0.92);
  for (let y = 6; y < maxBoilRow; y++) {
    if (
      leftEdge[y] >= 2 &&
      clampArr(leftEdge, y + 3, 0, H - 1) >= 0 &&
      clampArr(leftEdge, y - 3, 0, H - 1) >= 0
    ) {
      const slope = (clampArr(leftEdge, y + 3, 0, H - 1) - clampArr(leftEdge, y - 3, 0, H - 1)) / 6;
      const len = Math.hypot(1, slope) || 1;
      contourNormals.push([leftEdge[y] / W, y / H, -1 / len, -slope / len]);
    }
    if (
      rightEdge[y] >= 2 &&
      clampArr(rightEdge, y + 3, 0, H - 1) >= 0 &&
      clampArr(rightEdge, y - 3, 0, H - 1) >= 0
    ) {
      const slope =
        (clampArr(rightEdge, y + 3, 0, H - 1) - clampArr(rightEdge, y - 3, 0, H - 1)) / 6;
      const len = Math.hypot(1, slope) || 1;
      contourNormals.push([rightEdge[y] / W, y / H, 1 / len, slope / len]);
    }
  }

  for (let x = 6; x < W - 6; x += 2) {
    if (
      topEdge[x] >= 2 &&
      topEdge[x] / H < 0.85 &&
      clampArr(topEdge, x + 3, 0, W - 1) >= 0 &&
      clampArr(topEdge, x - 3, 0, W - 1) >= 0
    ) {
      const slope = (clampArr(topEdge, x + 3, 0, W - 1) - clampArr(topEdge, x - 3, 0, W - 1)) / 6;
      const len = Math.hypot(slope, 1) || 1;
      contourNormals.push([x / W, topEdge[x] / H, slope / len, 1 / len]);
    }
  }

  const boilCount = Math.min(1300, contourNormals.length);
  const totalCount = backCount + dustCount + frontCount + boilCount;

  const fig: Humanoid3DFigureData = {
    count: totalCount,
    frontCount,
    backCount,
    dustCount,
    boilCount,
    pivotY: 1 - 2 * neckNormY,
    palette: PALETTE_LINEAR,
    plates: {
      idle: idlePlate,
      thinking: thinkingPlate,
      speaking: speakingPlate,
      strong: strongPlate,
    },
    pos: new Float32Array(totalCount * 3),
    size: new Float32Array(totalCount).fill(1),
    w: new Float32Array(totalCount),
    kind: new Uint8Array(totalCount),
    boil: new Float32Array(totalCount * 4),
    bright: new Uint8Array(totalCount * 4),
    bucket: new Uint8Array(totalCount * 4),
    nx: new Float32Array(totalCount),
    shadow: document.createElement('canvas'),
  };

  let seed = 3311;
  const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);
  const stateArrays = [dIdle, dThink, dSpeak, dStrong];

  const writeStateBuckets = (particleIdx: number, pixelIdx4: number) => {
    for (let s = 0; s < 4; s++) {
      const arr = stateArrays[s];
      fig.bright[particleIdx * 4 + s] = Math.min(
        255,
        Math.round((sumRgb(arr, pixelIdx4) / 765) * 255)
      );
      fig.bucket[particleIdx * 4 + s] = classifyPaletteBucket(
        arr[pixelIdx4],
        arr[pixelIdx4 + 1],
        arr[pixelIdx4 + 2]
      );
    }
  };

  const upperFrontCandidates: number[] = [];
  for (let i = 0; i < frontCount; i++) {
    const isHalo = i >= primaryPixels.length;
    const pix = isHalo ? haloPixels[i - primaryPixels.length] : primaryPixels[i];
    const px = pix % W;
    const py = (pix / W) | 0;
    const idx4 = pix * 4;
    const pIdx = backCount + dustCount + i;
    const u = px / W;
    const v = py / H;
    const stagger = py & 1 ? 0.5 / W : 0;
    const ndcX = (u + stagger) * 2 - 1;
    const ndcY = 1 - v * 2;
    const weight = headWeightAt(v);

    fig.pos[pIdx * 3] = ndcX;
    fig.pos[pIdx * 3 + 1] = ndcY;
    fig.pos[pIdx * 3 + 2] = depthAt(ndcX, py, weight);
    fig.w[pIdx] = weight;
    fig.kind[pIdx] = 0;

    if (leftEdge[py] >= 0 && rightEdge[py] > leftEdge[py]) {
      const centerNdcX = (leftEdge[py] + rightEdge[py]) / W - 1;
      const halfWidth = Math.min(0.6, (rightEdge[py] - leftEdge[py]) / W);
      fig.nx[pIdx] = Math.max(-1, Math.min(1, (ndcX - centerNdcX) / Math.max(halfWidth, 1e-4)));
    }
    if (isHalo) {
      fig.size[pIdx] = 2;
    }
    writeStateBuckets(pIdx, idx4);
    if (!isHalo && v < 0.72 && sumRgb(dIdle, idx4) > 60) {
      upperFrontCandidates.push(pIdx);
    }
  }

  // Back shell particles (kind = 1)
  for (let i = 0; i < backCount; i++) {
    const srcIdx = upperFrontCandidates.length
      ? upperFrontCandidates[Math.floor(rng() * upperFrontCandidates.length)]
      : backCount + dustCount;
    fig.pos[i * 3] = fig.pos[srcIdx * 3];
    fig.pos[i * 3 + 1] = fig.pos[srcIdx * 3 + 1];
    fig.pos[i * 3 + 2] = -fig.pos[srcIdx * 3 + 2] * 0.85;
    fig.w[i] = fig.w[srcIdx];
    fig.kind[i] = 1;
    fig.nx[i] = fig.nx[srcIdx];
    for (let s = 0; s < 4; s++) {
      fig.bright[i * 4 + s] = fig.bright[srcIdx * 4 + s] >> 1;
      fig.bucket[i * 4 + s] = fig.bucket[srcIdx * 4 + s];
    }
  }

  // Interior head dust (kind = 5)
  {
    const minRow = Math.round(H * 0.06);
    const maxRow = Math.round((neckNormY - 0.02) * H);
    let placed = 0;
    let attempts = 0;
    while (placed < dustCount && attempts++ < dustCount * 40) {
      const row = minRow + Math.floor(rng() * Math.max(1, maxRow - minRow));
      if (leftEdge[row] < 2 || rightEdge[row] <= leftEdge[row] + 4) continue;
      const u = (leftEdge[row] + 2 + Math.floor(rng() * (rightEdge[row] - leftEdge[row] - 4))) / W;
      const v = row / H;
      const ndcX = u * 2 - 1;
      const ndcY = 1 - v * 2;
      const maxZ = depthAt(ndcX, row, headWeightAt(v));
      if (maxZ < 0.02) continue;
      const zFactor = (rng() * 2 - 1) * 0.9;
      if (rng() > 0.4 + 0.6 * (1 - Math.abs(zFactor))) continue;

      const pIdx = backCount + placed++;
      fig.pos[pIdx * 3] = ndcX;
      fig.pos[pIdx * 3 + 1] = ndcY;
      fig.pos[pIdx * 3 + 2] = zFactor * maxZ;
      fig.w[pIdx] = headWeightAt(v);
      fig.kind[pIdx] = 5;
      const bkt = rng() < 0.15 ? 1 : 0;
      for (let s = 0; s < 4; s++) {
        fig.bright[pIdx * 4 + s] = 46;
        fig.bucket[pIdx * 4 + s] = bkt;
      }
    }
  }

  // Edge boiler motes (kind = 3)
  for (let i = 0; i < boilCount; i++) {
    const [u, v, nx, ny] = contourNormals[Math.floor(rng() * contourNormals.length)];
    const pIdx = backCount + dustCount + frontCount + i;
    fig.pos[pIdx * 3] = u * 2 - 1;
    fig.pos[pIdx * 3 + 1] = 1 - v * 2;
    fig.pos[pIdx * 3 + 2] = 0;
    fig.w[pIdx] = headWeightAt(v);
    fig.kind[pIdx] = 3;
    const bkt = rng() < 0.15 ? 1 : 0;
    for (let s = 0; s < 4; s++) {
      fig.bright[pIdx * 4 + s] = 215;
      fig.bucket[pIdx * 4 + s] = bkt;
    }
    const amp = 0.012 + rng() * 0.042;
    fig.boil[pIdx * 4] = nx * amp;
    fig.boil[pIdx * 4 + 1] = ny * amp;
    fig.boil[pIdx * 4 + 2] = rng();
    fig.boil[pIdx * 4 + 3] = 0.22 + rng() * 0.5;
  }

  // Silhouette occlusion shadow canvas for backdrop separation
  {
    const shCanvas = fig.shadow;
    shCanvas.width = W;
    shCanvas.height = H;
    const shCtx = shCanvas.getContext('2d')!;
    const shData = shCtx.createImageData(W, H);
    let fullCropRow = Math.round(H * 0.82);
    for (let y = 0; y < H; y++) {
      if (leftEdge[y] >= 0 && rightEdge[y] - leftEdge[y] >= W * 0.96) {
        fullCropRow = y;
        break;
      }
    }
    for (let y = 0; y < H; y++) {
      if (y >= fullCropRow) {
        for (let x = 0; x < W; x++) {
          shData.data[(y * W + x) * 4 + 3] = 255;
        }
      } else {
        if (leftEdge[y] < 0 || rightEdge[y] <= leftEdge[y]) continue;
        for (let x = leftEdge[y]; x <= rightEdge[y]; x++) {
          shData.data[(y * W + x) * 4 + 3] = 255;
        }
      }
    }
    shCtx.putImageData(shData, 0, 0);
    const blurCanvas = document.createElement('canvas');
    blurCanvas.width = Math.max(2, Math.round(W / 8));
    blurCanvas.height = Math.max(2, Math.round(H / 8));
    blurCanvas.getContext('2d')!.drawImage(shCanvas, 0, 0, blurCanvas.width, blurCanvas.height);
    shCtx.clearRect(0, 0, W, H);
    shCtx.drawImage(blurCanvas, 0, 0, W, H);
    shCtx.fillStyle = '#000';
    shCtx.fillRect(0, Math.min(H - 1, fullCropRow + 6), W, H);
  }

  return fig;
}

export interface BackdropSampledGeometry {
  geometry: THREE.BufferGeometry;
  aspect: number;
  pointCount: number;
}

/**
 * Samples bright mountain ridges and golden vein networks from backdrop-v1.webp once on load (vU).
 */
export function sampleBackdropGeometry(img: HTMLImageElement): BackdropSampledGeometry {
  const sampleW = 780;
  const origW = img.naturalWidth || 1920;
  const origH = img.naturalHeight || 1080;
  const sampleH = Math.round((sampleW * origH) / origW);

  const canvas = document.createElement('canvas');
  canvas.width = sampleW;
  canvas.height = sampleH;
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, sampleW, sampleH);
  const data = ctx.getImageData(0, 0, sampleW, sampleH).data;

  const maxChannel = (idx: number) =>
    Math.max(data[idx * 4], data[idx * 4 + 1], data[idx * 4 + 2]) / 255;
  const isWarmGold = (idx: number) =>
    data[idx * 4] > data[idx * 4 + 2] * 1.25 && data[idx * 4] > 100;

  let seed = 48271;
  const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);

  const warmIndexMap = new Int32Array(sampleW * sampleH).fill(-1);
  const warmPixels: number[] = [];
  for (let i = 0; i < sampleW * sampleH; i++) {
    if (maxChannel(i) > 0.28 && isWarmGold(i)) {
      warmIndexMap[i] = warmPixels.length;
      warmPixels.push(i);
    }
  }

  // Disjoint-set union to group connected golden mountain veins
  const parent = warmPixels.map((_, idx) => idx);
  const find = (x: number): number => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  };
  const union = (a: number, b: number) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent[ra] = rb;
  };

  for (let i = 0; i < warmPixels.length; i++) {
    const pix = warmPixels[i];
    const x = pix % sampleW;
    const y = (pix / sampleW) | 0;
    for (const [dx, dy] of [
      [1, 0],
      [0, 1],
      [1, 1],
      [-1, 1],
    ]) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || nx >= sampleW || ny < 0 || ny >= sampleH) continue;
      const neighbor = warmIndexMap[ny * sampleW + nx];
      if (neighbor >= 0) union(i, neighbor);
    }
  }

  const componentSizes = new Map<number, number>();
  const componentPhases = new Map<number, { ph: number; rate: number }>();
  for (let i = 0; i < warmPixels.length; i++) {
    const root = find(i);
    componentSizes.set(root, (componentSizes.get(root) || 0) + 1);
  }

  const getComponentTiming = (root: number) => {
    let t = componentPhases.get(root);
    if (!t) {
      t = { ph: rng(), rate: 0.42 + rng() * 0.45 };
      componentPhases.set(root, t);
    }
    return t;
  };

  interface BackdropPoint {
    u: number;
    v: number;
    r: number;
    g: number;
    b: number;
    ph: number;
    rate: number;
    base: number;
    tw: number;
    sz: number;
  }

  const points: BackdropPoint[] = [];
  const pushPoint = (
    pix: number,
    meta: { ph: number; rate: number; base: number; tw: number; sz: number }
  ) => {
    const x = pix % sampleW;
    const y = (pix / sampleW) | 0;
    points.push({
      u: (x + 0.5) / sampleW,
      v: (y + 0.5) / sampleH,
      r: data[pix * 4] / 255,
      g: data[pix * 4 + 1] / 255,
      b: data[pix * 4 + 2] / 255,
      ...meta,
    });
  };

  for (let i = 0; i < warmPixels.length; i++) {
    const root = find(i);
    const compSize = componentSizes.get(root) || 0;
    const pix = warmPixels[i];
    const lum = maxChannel(pix);
    if (compSize >= 5) {
      if (rng() < Math.min(1, 0.18 + lum * 0.4)) {
        const timing = getComponentTiming(root);
        pushPoint(pix, {
          ph: timing.ph,
          rate: timing.rate,
          base: 0.24 + lum * 0.5,
          tw: 0.5,
          sz: 1.3 + lum * 1.5,
        });
      }
    } else if (lum > 0.55 && rng() < 0.3) {
      pushPoint(pix, {
        ph: rng(),
        rate: 0.3 + rng() * 0.5,
        base: 0.22 + lum * 0.4,
        tw: rng() < 0.5 ? 1 : 0,
        sz: 1.1 + lum * 1.2,
      });
    }
  }

  for (let y = 1; y < sampleH - 1; y++) {
    for (let x = 1; x < sampleW - 1; x++) {
      const pix = y * sampleW + x;
      if (warmIndexMap[pix] >= 0) continue;
      const lum = maxChannel(pix);
      if (lum < 0.3) continue;
      const isLocalPeak =
        lum > 0.5 &&
        lum >= maxChannel(pix - 1) &&
        lum >= maxChannel(pix + 1) &&
        lum >= maxChannel(pix - sampleW) &&
        lum >= maxChannel(pix + sampleW);
      if (isLocalPeak && rng() < 0.5) {
        const ph = rng();
        const rate = 0.5 + rng() * 0.65;
        pushPoint(pix, { ph, rate, base: 0.3 + lum * 0.5, tw: 1, sz: 1.5 + lum * 1.6 });
        pushPoint(pix, { ph, rate, base: 0.05, tw: 1, sz: 6.5 + lum * 3.5 });
      } else if (!isLocalPeak && rng() < (lum - 0.28) * 0.2) {
        pushPoint(pix, {
          ph: rng(),
          rate: 0.35 + rng() * 0.6,
          base: 0.12 + lum * 0.28,
          tw: rng() < 0.1 ? 1 : 0,
          sz: 1 + lum * 1.1,
        });
      }
    }
  }

  const n = points.length;
  const aUv = new Float32Array(n * 2);
  const aCol = new Float32Array(n * 3);
  const aPh = new Float32Array(n);
  const aRate = new Float32Array(n);
  const aBase = new Float32Array(n);
  const aTw = new Float32Array(n);
  const aSz = new Float32Array(n);
  const pos = new Float32Array(n * 3);

  points.forEach((pt, i) => {
    aUv[i * 2] = pt.u;
    aUv[i * 2 + 1] = pt.v;
    aCol[i * 3] = pt.r;
    aCol[i * 3 + 1] = pt.g;
    aCol[i * 3 + 2] = pt.b;
    aPh[i] = pt.ph;
    aRate[i] = pt.rate;
    aBase[i] = pt.base;
    aTw[i] = pt.tw;
    aSz[i] = pt.sz;
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geometry.setAttribute('aUv', new THREE.BufferAttribute(aUv, 2));
  geometry.setAttribute('aCol', new THREE.BufferAttribute(aCol, 3));
  geometry.setAttribute('aPh', new THREE.BufferAttribute(aPh, 1));
  geometry.setAttribute('aRate', new THREE.BufferAttribute(aRate, 1));
  geometry.setAttribute('aBase', new THREE.BufferAttribute(aBase, 1));
  geometry.setAttribute('aTw', new THREE.BufferAttribute(aTw, 1));
  geometry.setAttribute('aSz', new THREE.BufferAttribute(aSz, 1));

  return { geometry, aspect: origW / origH, pointCount: n };
}
