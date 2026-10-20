const TIMING = {
  ignition: 6.2,
};

let ctx: AudioContext | null = null;
let masterGain: GainNode | null = null;
let compressor: DynamicsCompressorNode | null = null;
let dryBus: GainNode | null = null;
let reverbShort: ConvolverNode | null = null;
let reverbLong: ConvolverNode | null = null;
let reverbShortGain: GainNode | null = null;
let reverbLongGain: GainNode | null = null;
let noiseBuf: AudioBuffer | null = null;
let activeNodes: AudioScheduledSourceNode[] = [];
let soundEnabled = true;

function createReverbImpulse(audioCtx: AudioContext, duration: number, decay: number): AudioBuffer {
  const len = Math.floor(audioCtx.sampleRate * duration);
  const buf = audioCtx.createBuffer(2, len, audioCtx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const data = buf.getChannelData(ch);
    for (let i = 0; i < len; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
    }
  }
  return buf;
}

function makeDriveCurve(amount: number): Float32Array<ArrayBuffer> {
  const curve = new Float32Array(1024);
  for (let i = 0; i < 1024; i++) {
    const x = (i * 2) / 1024 - 1;
    curve[i] = ((1 + amount) * x) / (1 + amount * Math.abs(x));
  }
  return curve;
}

function ensureAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  if (ctx) return ctx;
  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return null;

  ctx = new AudioCtx();
  compressor = ctx.createDynamicsCompressor();
  compressor.threshold.value = -8;
  compressor.knee.value = 12;
  compressor.ratio.value = 3.5;
  compressor.attack.value = 0.006;
  compressor.release.value = 0.25;

  masterGain = ctx.createGain();
  masterGain.gain.value = soundEnabled ? 0.45 : 0;

  dryBus = ctx.createGain();
  reverbShort = ctx.createConvolver();
  reverbShort.buffer = createReverbImpulse(ctx, 2.8, 2.4);
  reverbLong = ctx.createConvolver();
  reverbLong.buffer = createReverbImpulse(ctx, 5.2, 1.7);

  reverbShortGain = ctx.createGain();
  reverbShortGain.gain.value = 0.72;
  reverbLongGain = ctx.createGain();
  reverbLongGain.gain.value = 0.82;

  dryBus.connect(compressor);
  reverbShort.connect(reverbShortGain);
  reverbShortGain.connect(compressor);
  reverbLong.connect(reverbLongGain);
  reverbLongGain.connect(compressor);
  compressor.connect(masterGain);
  masterGain.connect(ctx.destination);

  const noiseLen = Math.floor(ctx.sampleRate * 2);
  noiseBuf = ctx.createBuffer(1, noiseLen, ctx.sampleRate);
  const nd = noiseBuf.getChannelData(0);
  for (let i = 0; i < noiseLen; i++) nd[i] = Math.random() * 2 - 1;

  return ctx;
}

function routeToBuses(node: AudioNode, sendShort: number, sendLong: number) {
  if (!ctx || !dryBus || !reverbShort || !reverbLong) return;
  node.connect(dryBus);
  if (sendShort > 0) {
    const g = ctx.createGain();
    g.gain.value = sendShort;
    node.connect(g);
    g.connect(reverbShort);
  }
  if (sendLong > 0) {
    const g = ctx.createGain();
    g.gain.value = sendLong;
    node.connect(g);
    g.connect(reverbLong);
  }
}

function trackSource(src: AudioScheduledSourceNode) {
  activeNodes.push(src);
  src.onended = () => {
    activeNodes = activeNodes.filter((n) => n !== src);
  };
}

export function unlockAudioOnUserGesture(): void {
  try {
    const audioCtx = ensureAudioContext();
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  } catch {
    // Ignore audio context errors in restricted environments
  }
}

export async function unlockAudioOnUserGestureAsync(): Promise<boolean> {
  try {
    const audioCtx = ensureAudioContext();
    if (!audioCtx) return false;
    if (audioCtx.state === 'suspended') await audioCtx.resume();
    return audioCtx.state === 'running';
  } catch {
    return false;
  }
}

export function setSoundEnabled(enabled: boolean): void {
  soundEnabled = enabled;
  if (masterGain && ctx) {
    masterGain.gain.setTargetAtTime(enabled ? 0.45 : 0, ctx.currentTime, 0.04);
  }
  if (!enabled) {
    stopAllActiveSounds();
  }
}

export function isSoundEnabled(): boolean {
  return soundEnabled;
}

export function stopAllActiveSounds(): void {
  const nodes = [...activeNodes];
  activeNodes = [];
  for (const n of nodes) {
    try {
      n.stop();
    } catch {
      // Already stopped
    }
  }
}

function playFmSpark(opts: {
  f?: number;
  ratio?: number;
  index?: number;
  indexEnd?: number;
  dur?: number;
  peak?: number;
  attack?: number;
  delay?: number;
  fEnd?: number | null;
  send?: number;
  big?: number;
  drive?: number;
  t0?: number;
}) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled) return;
  const {
    f = 440,
    ratio = 2.76,
    index = 600,
    indexEnd = 8,
    dur = 0.2,
    peak = 0.18,
    attack = 0.012,
    delay = 0,
    fEnd = null,
    send = 0.45,
    big = 0,
    drive = 0,
    t0,
  } = opts;

  const start = (t0 ?? audioCtx.currentTime) + delay;
  const carrier = audioCtx.createOscillator();
  carrier.type = 'sine';
  carrier.frequency.setValueAtTime(f, start);
  if (fEnd) carrier.frequency.exponentialRampToValueAtTime(fEnd, start + dur);

  const mod = audioCtx.createOscillator();
  mod.type = 'sine';
  mod.frequency.setValueAtTime(f * ratio, start);
  if (fEnd) mod.frequency.exponentialRampToValueAtTime(fEnd * ratio, start + dur);

  const modGain = audioCtx.createGain();
  modGain.gain.setValueAtTime(Math.max(index, 1), start);
  modGain.gain.exponentialRampToValueAtTime(Math.max(indexEnd, 1), start + dur);
  mod.connect(modGain);
  modGain.connect(carrier.frequency);

  const env = audioCtx.createGain();
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(peak, start + attack);
  env.gain.exponentialRampToValueAtTime(0.0001, start + dur);

  let out: AudioNode = env;
  carrier.connect(env);
  if (drive > 0) {
    const shaper = audioCtx.createWaveShaper();
    shaper.curve = makeDriveCurve(drive);
    env.connect(shaper);
    out = shaper;
  }
  routeToBuses(out, send, big);
  carrier.start(start);
  mod.start(start);
  carrier.stop(start + dur + 0.05);
  mod.stop(start + dur + 0.05);
  trackSource(carrier);
  trackSource(mod);
}

function playSubBass(opts: {
  f?: number;
  dur?: number;
  peak?: number;
  delay?: number;
  fEnd?: number | null;
  send?: number;
  big?: number;
  attack?: number;
  t0?: number;
}) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled) return;
  const {
    f = 62,
    dur = 0.22,
    peak = 0.22,
    delay = 0,
    fEnd = null,
    send = 0.15,
    big = 0,
    attack = 0.016,
    t0,
  } = opts;
  const start = (t0 ?? audioCtx.currentTime) + delay;
  const osc = audioCtx.createOscillator();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(f, start);
  if (fEnd) osc.frequency.exponentialRampToValueAtTime(fEnd, start + dur);

  const env = audioCtx.createGain();
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(peak, start + attack);
  env.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(env);
  routeToBuses(env, send, big);
  osc.start(start);
  osc.stop(start + dur + 0.05);
  trackSource(osc);
}

function playNoiseSweep(opts: {
  from?: number;
  to?: number;
  q?: number;
  dur?: number;
  peak?: number;
  attack?: number;
  delay?: number;
  type?: BiquadFilterType;
  send?: number;
  big?: number;
  t0?: number;
}) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled || !noiseBuf) return;
  const {
    from = 400,
    to = 2400,
    q = 7,
    dur = 0.3,
    peak = 0.16,
    attack = 0.04,
    delay = 0,
    type = 'bandpass',
    send = 0.55,
    big = 0,
    t0,
  } = opts;
  const start = (t0 ?? audioCtx.currentTime) + delay;
  const src = audioCtx.createBufferSource();
  src.buffer = noiseBuf;
  src.loop = true;

  const filter = audioCtx.createBiquadFilter();
  filter.type = type;
  filter.Q.value = q;
  filter.frequency.setValueAtTime(from, start);
  filter.frequency.exponentialRampToValueAtTime(to, start + dur);

  const env = audioCtx.createGain();
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(peak, start + attack);
  env.gain.exponentialRampToValueAtTime(0.0001, start + dur);

  src.connect(filter);
  filter.connect(env);
  routeToBuses(env, send, big);
  src.start(start);
  src.stop(start + dur + 0.06);
  trackSource(src);
}

function playAssemblyHarmonicRise(t0: number) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled) return;
  const chk = 1.55;
  const thr = 5.35;
  const span = thr - chk;
  const start = chk - 0.2;
  const end = chk + span;

  const outGain = audioCtx.createGain();
  outGain.gain.setValueAtTime(0.0001, t0 + start);
  outGain.gain.exponentialRampToValueAtTime(0.08, t0 + chk);
  outGain.gain.exponentialRampToValueAtTime(0.19, t0 + end - 0.12);
  outGain.gain.exponentialRampToValueAtTime(0.0001, t0 + end + 0.14);

  const lp = audioCtx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.Q.value = 7;
  lp.frequency.setValueAtTime(120, t0 + start);
  lp.frequency.exponentialRampToValueAtTime(4400, t0 + end);

  const shaper = audioCtx.createWaveShaper();
  shaper.curve = makeDriveCurve(1);

  const preGain = audioCtx.createGain();
  preGain.gain.setValueAtTime(1, t0 + start);
  preGain.gain.setValueAtTime(1, t0 + chk + span * 0.6);
  preGain.gain.linearRampToValueAtTime(4.2, t0 + end);

  [55, 82.5, 110.9].forEach((freq, idx) => {
    const osc = audioCtx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, t0 + start);
    osc.frequency.exponentialRampToValueAtTime(freq * 2.9, t0 + end);
    const g = audioCtx.createGain();
    g.gain.value = [1, 0.5, 0.28][idx];
    osc.connect(g);
    g.connect(preGain);
    osc.start(t0 + start);
    osc.stop(t0 + end + 0.35);
    trackSource(osc);
  });

  preGain.connect(shaper);
  shaper.connect(lp);
  lp.connect(outGain);
  routeToBuses(outGain, 0.6, 0.4);
}

function playPreIgnitionCall(t0: number) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled) return;
  const thr = 5.35;
  const call = 5.92;
  const dur = call - thr;

  const osc = audioCtx.createOscillator();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(2900, t0 + thr);
  osc.frequency.linearRampToValueAtTime(3280, t0 + call);

  const g = audioCtx.createGain();
  g.gain.setValueAtTime(0.0001, t0 + thr);
  g.gain.exponentialRampToValueAtTime(0.028, t0 + thr + 0.05);
  g.gain.exponentialRampToValueAtTime(0.0001, t0 + call);

  osc.connect(g);
  routeToBuses(g, 0.8, 0.6);
  osc.start(t0 + thr);
  osc.stop(t0 + call + 0.05);
  trackSource(osc);

  playNoiseSweep({
    from: 280,
    to: 5200,
    q: 1.2,
    dur: dur * 0.95,
    peak: 0.1,
    attack: dur * 0.88,
    send: 0.5,
    big: 0.6,
    t0: t0 + thr,
  });
}

function playTripodHorn(t0: number, dur = 3.2) {
  const audioCtx = ensureAudioContext();
  if (!audioCtx || !soundEnabled) return;

  const mix = audioCtx.createGain();
  const bend = [0.93, 1, 1.05, 1, 0.955];
  const baseFreq = 52;
  const oscs: OscillatorNode[] = [];

  [
    [-0.62, -9],
    [0, 0],
    [0.62, 11],
  ].forEach(([pan, detune]) => {
    const osc = audioCtx.createOscillator();
    osc.type = 'sawtooth';
    osc.detune.value = detune;
    osc.frequency.setValueCurveAtTime(
      new Float32Array(bend.map((b) => baseFreq * b)),
      t0,
      dur
    );
    const g = audioCtx.createGain();
    g.gain.value = 0.32;
    osc.connect(g);
    if (audioCtx.createStereoPanner) {
      const p = audioCtx.createStereoPanner();
      p.pan.value = pan;
      g.connect(p);
      p.connect(mix);
    } else {
      g.connect(mix);
    }
    osc.start(t0);
    osc.stop(t0 + dur + 0.12);
    trackSource(osc);
    oscs.push(osc);
  });

  const wobbleOsc = audioCtx.createOscillator();
  wobbleOsc.type = 'sine';
  wobbleOsc.frequency.value = 0.75;
  const wobbleGain = audioCtx.createGain();
  wobbleGain.gain.value = baseFreq * 0.014;
  wobbleOsc.connect(wobbleGain);
  oscs.forEach((o) => wobbleGain.connect(o.frequency));
  wobbleOsc.start(t0);
  wobbleOsc.stop(t0 + dur + 0.12);
  trackSource(wobbleOsc);

  const sub = audioCtx.createOscillator();
  sub.type = 'sine';
  sub.frequency.setValueAtTime(baseFreq / 2, t0);
  const subG = audioCtx.createGain();
  subG.gain.value = 0.55;
  sub.connect(subG);
  subG.connect(mix);
  sub.start(t0);
  sub.stop(t0 + dur + 0.12);
  trackSource(sub);

  if (noiseBuf) {
    const nSrc = audioCtx.createBufferSource();
    nSrc.buffer = noiseBuf;
    nSrc.loop = true;
    const nBp = audioCtx.createBiquadFilter();
    nBp.type = 'bandpass';
    nBp.frequency.value = 430;
    nBp.Q.value = 1.1;
    const nG = audioCtx.createGain();
    nG.gain.value = 0.07;
    nSrc.connect(nBp);
    nBp.connect(nG);
    nG.connect(mix);
    nSrc.start(t0);
    nSrc.stop(t0 + dur + 0.12);
    trackSource(nSrc);
  }

  const shaper = audioCtx.createWaveShaper();
  shaper.curve = makeDriveCurve(2.8);
  mix.connect(shaper);

  const formantSum = audioCtx.createGain();
  [
    [205, 5, 1],
    [540, 7, 0.62],
    [1150, 9, 0.28],
  ].forEach(([freq, q, gain]) => {
    const bp = audioCtx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = freq;
    bp.Q.value = q;
    const fg = audioCtx.createGain();
    fg.gain.value = gain;
    shaper.connect(bp);
    bp.connect(fg);
    fg.connect(formantSum);
  });

  const dryShaper = audioCtx.createGain();
  dryShaper.gain.value = 0.42;
  shaper.connect(dryShaper);
  dryShaper.connect(formantSum);

  const lp = audioCtx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 4400;
  lp.Q.value = 0.7;

  const env = audioCtx.createGain();
  env.gain.setValueAtTime(0.0001, t0);
  env.gain.exponentialRampToValueAtTime(0.52, t0 + dur * 0.19);
  env.gain.setValueAtTime(0.52, t0 + dur * 0.52);
  env.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);

  formantSum.connect(lp);
  lp.connect(env);
  routeToBuses(env, 0.5, 1.0);
}

let activeAssemblySessionId = -1;
let playedAssemblySessionId = -1;

export function resetAssemblySoundSession(newSessionId?: number): void {
  playedAssemblySessionId = -1;
  activeAssemblySessionId = newSessionId !== undefined ? newSessionId : -1;
}

export function isAssemblySoundPlayed(sessionId: number): boolean {
  return playedAssemblySessionId === sessionId;
}

/**
 * Plays the complete assembly & shockwave soundscape only after explicit user interaction.
 * Enforces single playback per assembly session ID to prevent duplicate audio triggers.
 */
export function playAssemblySoundscape(sessionId?: number): boolean {
  if (!soundEnabled) return false;
  const audioCtx = ensureAudioContext();
  if (!audioCtx || audioCtx.state !== 'running') return false;

  // Prevent duplicate playback for the same assembly session
  if (sessionId !== undefined) {
    if (playedAssemblySessionId === sessionId) {
      return false;
    }
    playedAssemblySessionId = sessionId;
    activeAssemblySessionId = sessionId;
  }

  stopAllActiveSounds();
  const t0 = audioCtx.currentTime;

  playSubBass({ f: 30, fEnd: 44, dur: 1.5, peak: 0.13, attack: 0.7, send: 0.8, big: 1, t0 });
  playAssemblyHarmonicRise(t0);

  const count = 54;
  const tStart = 1.1;
  const tEnd = 5.29;
  for (let i = 0; i < count; i++) {
    const u = i / (count - 1);
    const sparkTime = t0 + tStart + (tEnd - tStart) * Math.pow(u, 0.62) + (Math.random() - 0.5) * 0.05;
    playFmSpark({
      f: 260 + u * 700,
      ratio: 2.76,
      index: 320 + u * 420,
      indexEnd: 7,
      dur: 0.11 + Math.random() * 0.04,
      peak: 0.018 + u * 0.026,
      attack: 0.003,
      send: 0.6,
      big: 0.3 + u * 0.35,
      drive: u > 0.7 ? (u - 0.7) * 5 : 0,
      t0: sparkTime,
    });
    if (i % 9 === 0) {
      playSubBass({
        f: 54 + u * 26,
        dur: 0.22,
        peak: 0.05 + u * 0.04,
        send: 0.35,
        big: 0.45,
        t0: sparkTime,
      });
    }
  }

  playPreIgnitionCall(t0);

  // Horn & Shockwave at TIMING.ignition (6.2s)
  playTripodHorn(t0 + TIMING.ignition, 3.2);
  playSubBass({
    f: 41,
    dur: 2.6,
    peak: 0.17,
    attack: 0.4,
    send: 0.5,
    big: 1,
    t0: t0 + TIMING.ignition + 3.2 * 0.72,
  });
  return true;
}

export function playStateChime(): void {
  if (!soundEnabled) return;
  const audioCtx = ensureAudioContext();
  if (!audioCtx || audioCtx.state !== 'running') return;
  [110, 294, 880].forEach((f, idx) => {
    playFmSpark({
      f,
      ratio: 2.76,
      index: 260,
      indexEnd: 6,
      dur: 0.66,
      peak: [0.17, 0.09, 0.05][idx],
      attack: 0.17,
      delay: idx * 0.07,
      send: 0.8,
      big: 0.6,
    });
  });
}
