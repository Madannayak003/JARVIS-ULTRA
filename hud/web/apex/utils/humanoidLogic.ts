export type MoodState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'strong';

export const TIMING = {
  assemblyTotal: 7.4,
  ignition: 6.2,
  hornPeak: 6.2 + 3.2 * 0.19, // 6.808s
  shockwaveDuration: 2.5,
};

export const PALETTE_HEX = ['#00E5FF', '#C8F7FF', '#F5A623', '#FFB733'] as const;

export function clamp(val: number, min = 0, max = 1): number {
  return Math.max(min, Math.min(max, val));
}

export function smoothstep(edge0: number, edge1: number, x: number): number {
  if (edge0 === edge1) return x < edge0 ? 0 : 1;
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

export function smooth01(x: number): number {
  const t = clamp(x, 0, 1);
  return t * t * (3 - 2 * t);
}

export function srgbToLinear(c: number): number {
  const v = clamp(c, 0, 1);
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

/**
 * Classifies an RGB pixel (0-255) into one of the 4 APEX role/palette buckets:
 * 0: Cyan contour particle
 * 1: Pale cyan-white highlight
 * 2: Warm amber-orange energy core
 * 3: Bright gold filament / intense core highlight
 */
export function classifyPaletteBucket(r: number, g: number, b: number): 0 | 1 | 2 | 3 {
  const sum = r + g + b;
  if (r > b * 1.4) {
    return r > 175 ? 3 : 2;
  }
  return sum > 430 ? 1 : 0;
}

/**
 * Maps a high-level MoodState to the shader's numeric plate index:
 * 0 = idle/listening base plate, 1 = thinking plate, 2 = speaking/strong plate
 */
export function moodToShaderIndex(mood: MoodState): 0 | 1 | 2 {
  if (mood === 'speaking' || mood === 'strong') return 2;
  if (mood === 'thinking') return 1;
  return 0;
}

export function getTransitionDuration(shaderIndex: 0 | 1 | 2): number {
  if (shaderIndex === 2) return 0.7;
  if (shaderIndex === 0) return 1.2;
  return 0.95;
}

export interface RadialTransitionState {
  a: 0 | 1 | 2;
  b: 0 | 1 | 2;
  t: number;
  dur: number;
  pending: (0 | 1 | 2) | null;
  moodA: MoodState;
  moodB: MoodState;
  pendingMood: MoodState | null;
}

export function createMoodTransitionState(initialMood: MoodState = 'idle'): RadialTransitionState {
  const idx = moodToShaderIndex(initialMood);
  return {
    a: idx,
    b: idx,
    t: 9,
    dur: 0.95,
    pending: null,
    moodA: initialMood,
    moodB: initialMood,
    pendingMood: null,
  };
}

/**
 * Advances the face-centred radial mood transition state machine.
 * If a new mood arrives while a transition is in flight, it accelerates completion (4x)
 * and immediately replaces any obsolete pending state without queuing a long chain.
 */
export function stepMoodTransition(
  state: RadialTransitionState,
  targetMood: MoodState,
  dt: number,
  reducedMotion = false
): {
  state: RadialTransitionState;
  progress: number;
  bloomRadius: number;
} {
  const targetIdx = moodToShaderIndex(targetMood);
  if (reducedMotion) {
    const next: RadialTransitionState = {
      a: targetIdx,
      b: targetIdx,
      t: 9,
      dur: getTransitionDuration(targetIdx),
      pending: null,
      moodA: targetMood,
      moodB: targetMood,
      pendingMood: null,
    };
    return { state: next, progress: 1, bloomRadius: 9 };
  }

  const next: RadialTransitionState = { ...state };
  const currentProgress = Math.min(1, next.t / next.dur);

  if (targetMood === next.moodB && targetIdx === next.b) {
    next.pending = null;
    next.pendingMood = null;
  } else if (currentProgress >= 1) {
    next.a = next.b;
    next.moodA = next.moodB;
    next.b = targetIdx;
    next.moodB = targetMood;
    next.t = 0;
    next.dur = getTransitionDuration(targetIdx);
    next.pending = null;
    next.pendingMood = null;
  } else {
    next.pending = targetIdx;
    next.pendingMood = targetMood;
  }

  const speedMultiplier = next.pending !== null ? 4 : 1;
  next.t += Math.max(0, dt) * speedMultiplier;

  if (next.pending !== null && next.t / next.dur >= 1) {
    next.a = next.b;
    next.moodA = next.moodB;
    next.b = next.pending;
    next.moodB = next.pendingMood ?? targetMood;
    next.t = 0;
    next.dur = getTransitionDuration(next.b);
    next.pending = null;
    next.pendingMood = null;
  }

  const progress = Math.min(1, next.t / next.dur);
  const bloomRadius = progress >= 1 ? 9 : smooth01(progress) * 1.75;

  return { state: next, progress, bloomRadius };
}

export interface HeadTurnState {
  yaw: number;
  pitch: number;
  backK: number;
  effK: number;
}

/**
 * Computes damped mouse/pointer head turning angles and shading gates.
 * Conservative turn angles prevent particle gaps and preserve neutral front fidelity.
 */
export function computeHeadTurn(
  pointerX: number,
  pointerY: number,
  currentYaw: number,
  currentPitch: number,
  dt: number,
  mood: MoodState,
  turnSensitivity = 1.0,
  effectsEnabled = true,
  reducedMotion = false
): HeadTurnState {
  if (!effectsEnabled || reducedMotion) {
    const decay = 1 - Math.exp(-Math.max(0, dt) * 8.0);
    const yaw = currentYaw + (0 - currentYaw) * decay;
    const pitch = currentPitch + (0 - currentPitch) * decay;
    return { yaw, pitch, backK: 0, effK: 0 };
  }

  const px = clamp(pointerX, -1, 1);
  const py = clamp(pointerY, -1, 1);

  const moodFactor =
    mood === 'speaking' || mood === 'strong' ? 0.55 : mood === 'listening' ? 1.1 : 1.0;

  const targetYaw = px * 0.44 * moodFactor * turnSensitivity;
  const targetPitch = py * 0.2 * moodFactor * turnSensitivity;

  const alpha = 1 - Math.exp(-Math.max(0, dt) * 4.2);
  const yaw = currentYaw + (targetYaw - currentYaw) * alpha;
  const pitch = currentPitch + (targetPitch - currentPitch) * alpha;

  const backK = clamp((Math.abs(yaw) + Math.abs(pitch) - 0.09) / 0.24, 0, 1);
  const effK = smoothstep(0.06, 0.3, Math.abs(yaw) + Math.abs(pitch) * 1.2);

  return { yaw, pitch, backK, effK };
}

export interface BreathingState {
  uBreathe: number;
  uBreathY: number;
}

/**
 * Computes chest-anchored breathing expansion and vertical settling without position drift.
 */
export function computeBreathing(
  elapsedTime: number,
  effectsEnabled = true,
  reducedMotion = false
): BreathingState {
  if (!effectsEnabled || reducedMotion) {
    return { uBreathe: 1.0, uBreathY: 0.0 };
  }
  return {
    uBreathe: 1 + Math.sin(elapsedTime * 0.9) * 0.004,
    uBreathY: 0.012 * Math.sin(elapsedTime * 1.37),
  };
}

export interface AssemblyWaveMetrics {
  isAssembling: boolean;
  progress: number;
  stage25Weight: number;
  stage60Weight: number;
  shockwaveActive: boolean;
  shockwaveElapsed: number;
  shockwaveRadiusNdc: number;
  shockwaveStrength: number;
  birthSurge: number;
}

/**
 * Computes assembly progress, intermediate 25% & 60% artwork weights,
 * and post-assembly expanding shockwave parameters.
 */
export function computeAssemblyAndShockwave(
  elapsedSinceStartSec: number,
  skipped: boolean,
  effectsEnabled: boolean,
  reducedMotion: boolean
): AssemblyWaveMetrics {
  if (skipped || !effectsEnabled || reducedMotion || elapsedSinceStartSec >= 90) {
    return {
      isAssembling: false,
      progress: 1,
      stage25Weight: 0,
      stage60Weight: 0,
      shockwaveActive: false,
      shockwaveElapsed: 99,
      shockwaveRadiusNdc: 0,
      shockwaveStrength: 0,
      birthSurge: 0,
    };
  }

  const t = Math.max(0, elapsedSinceStartSec);
  const total = TIMING.assemblyTotal;
  const isAssembling = t < total;
  const progress = isAssembling ? clamp(t / total, 0, 0.999) : 1;

  // Smooth bell weights around 25% (0.15..0.50) and 60% (0.40..0.82) assembly stages
  const stage25Weight = isAssembling
    ? smoothstep(0.08, 0.25, progress) * (1 - smoothstep(0.32, 0.52, progress))
    : 0;
  const stage60Weight = isAssembling
    ? smoothstep(0.38, 0.58, progress) * (1 - smoothstep(0.68, 0.88, progress))
    : 0;

  // Shockwave begins at hornPeak (~6.81s into assembly) and expands for ~2.5-4.0s
  const waveElapsed = t - TIMING.hornPeak;
  const shockwaveActive = waveElapsed >= 0 && waveElapsed <= 3.6;
  const shockwaveStrength = shockwaveActive ? Math.exp(-waveElapsed / 1.45) : 0;
  const shockwaveRadiusNdc = shockwaveActive ? waveElapsed * 1.45 : 0;

  const afterComplete = t - total;
  const birthSurge =
    afterComplete >= 0 && afterComplete < 6.5 ? Math.exp(-afterComplete / 1.9) : 0;

  return {
    isAssembling,
    progress,
    stage25Weight,
    stage60Weight,
    shockwaveActive,
    shockwaveElapsed: waveElapsed,
    shockwaveRadiusNdc,
    shockwaveStrength,
    birthSurge,
  };
}

/**
 * Evaluates a 1D cubic Bézier curve at parameter t in [0, 1].
 */
export function evaluateCubicBezier(
  t: number,
  p0: number,
  p1: number,
  p2: number,
  p3: number
): number {
  const u = smooth01(t);
  const inv = 1 - u;
  return (
    inv * inv * inv * p0 +
    3 * inv * inv * u * p1 +
    3 * inv * u * u * p2 +
    u * u * u * p3
  );
}
