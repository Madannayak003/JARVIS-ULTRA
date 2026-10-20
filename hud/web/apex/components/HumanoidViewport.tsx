import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import {
  MoodState,
  TIMING,
  clamp,
  computeAssemblyAndShockwave,
  computeBreathing,
  computeHeadTurn,
  createMoodTransitionState,
  evaluateCubicBezier,
  smooth01,
  stepMoodTransition,
} from '../utils/humanoidLogic';
import {
  ASSET_PATHS,
  AssemblyData,
  BackdropSampledGeometry,
  BoilMote2D,
  Humanoid3DFigureData,
  LoadedHumanoidAssets,
  buildHumanoid3DFigure,
  cleanAssemblyPlate,
  cleanIdlePlate,
  createEdgeBoilMotes,
  extractGoldVeins,
  extractListeningRings,
  loadAllHumanoidAssets,
  sampleAssemblyParticles,
  sampleBackdropGeometry,
  sampleSilhouetteEdges,
} from '../utils/imageSampling';
import {
  CLUSTER_FRAGMENT_SHADER,
  CLUSTER_VERTEX_SHADER,
  HUMAN_FRAGMENT_SHADER,
  HUMAN_VERTEX_SHADER,
} from '../utils/shaders';
import { BackdropCanvas, ShockwaveRefState } from './BackdropCanvas';
import { DiagnosticsSnapshot, TuningParams } from './TechnicalDetailsPanel';

interface HumanoidViewportProps {
  mood: MoodState;
  effectsEnabled: boolean;
  reducedMotion: boolean;
  compareActive: boolean;
  assemblyTrigger: number;
  skipRequested: boolean;
  shockwaveTrigger: number;
  tuning: TuningParams;
  attentionRef: React.MutableRefObject<{ x: number; y: number; fingerHold?: number }>;
  micEnergyRef: React.MutableRefObject<number>;
  cameraActive: boolean;
  cameraStatus: string;
  techDetailsOpen?: boolean;
  onDiagnosticsUpdate: (snap: DiagnosticsSnapshot) => void;
  onAssemblyStatusChange: (isAssembling: boolean, pct: number) => void;
}

interface SparkMote2D {
  ox: number;
  oy: number;
  ph: number;
  sp: number;
  size: number;
  bright: boolean;
}

function createChestSparkMotes2D(): SparkMote2D[] {
  let seed = 424171;
  const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);
  const gauss = () => (rng() + rng() + rng() - 1.5) / 1.5;
  return Array.from({ length: 240 }, () => ({
    ox: gauss() * 0.028,
    oy: gauss() * 0.024,
    ph: rng() * Math.PI * 2,
    sp: 0.6 + rng() * 1.8,
    size: 0.7 + rng() * 1.4,
    bright: rng() < 0.2,
  }));
}

export const HumanoidViewport: React.FC<HumanoidViewportProps> = ({
  mood,
  effectsEnabled,
  reducedMotion,
  compareActive,
  assemblyTrigger,
  skipRequested,
  shockwaveTrigger,
  tuning,
  attentionRef,
  micEnergyRef,
  cameraStatus,
  techDetailsOpen = false,
  onDiagnosticsUpdate,
  onAssemblyStatusChange,
}) => {
  const frameContainerRef = useRef<HTMLDivElement | null>(null);
  const canvas2dRef = useRef<HTMLCanvasElement | null>(null);
  const webglMountRef = useRef<HTMLDivElement | null>(null);
  const shockwaveRingRef = useRef<HTMLDivElement | null>(null);

  const [assetsReady, setAssetsReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [listeningRingUrl, setListeningRingUrl] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>('ASSEMBLING... 25%');
  const [isAssembling, setIsAssembling] = useState<boolean>(true);
  const [hornPeakReached, setHornPeakReached] = useState<boolean>(false);

  const processedRef = useRef<{
    assets: LoadedHumanoidAssets;
    cleanedIdle: HTMLCanvasElement;
    cleanedAssembly25: HTMLCanvasElement;
    cleanedAssembly60: HTMLCanvasElement;
    veins: HTMLCanvasElement;
    listeningRings: HTMLCanvasElement;
    edgeMotes: BoilMote2D[];
    assembly: AssemblyData;
    fig: Humanoid3DFigureData;
    backdrop: BackdropSampledGeometry;
    sparks2d: SparkMote2D[];
  } | null>(null);

  const shockwaveRef = useRef<ShockwaveRefState>({
    active: false,
    elapsed: 99,
    originX: 0,
    originY: 0.14,
    strength: 0,
  });

  const clickPulseRef = useRef<{ x: number; y: number; strength: number; time: number }>({
    x: 0,
    y: 0,
    strength: 0,
    time: -99000,
  });

  const assemblyStartRef = useRef<number>(performance.now());
  const skippedRef = useRef<boolean>(skipRequested);
  skippedRef.current = skipRequested;

  const livePropsRef = useRef({
    mood,
    effectsEnabled,
    reducedMotion,
    compareActive,
    tuning,
    cameraStatus,
    onDiagnosticsUpdate,
    onAssemblyStatusChange,
  });
  livePropsRef.current = {
    mood,
    effectsEnabled,
    reducedMotion,
    compareActive,
    tuning,
    cameraStatus,
    onDiagnosticsUpdate,
    onAssemblyStatusChange,
  };

  // Load and process all reference artworks once
  useEffect(() => {
    let mounted = true;
    loadAllHumanoidAssets()
      .then((assets) => {
        if (!mounted) return;
        try {
          const cleanedIdle = cleanIdlePlate(assets.idle);
          const cleanedAssembly25 = cleanAssemblyPlate(assets.assembly25);
          const cleanedAssembly60 = cleanAssemblyPlate(assets.assembly60);
          const veins = extractGoldVeins(assets.idle);
          const listeningRings = extractListeningRings(assets.listening);
          try {
            listeningRings.toBlob((blob) => {
              if (blob && mounted) {
                setListeningRingUrl(URL.createObjectURL(blob));
              }
            }, 'image/png');
          } catch {
            // Ignore blob error
          }
          const edgeMotes = createEdgeBoilMotes(sampleSilhouetteEdges(assets.idle));
          const assembly = sampleAssemblyParticles(cleanedIdle);
          const fig = buildHumanoid3DFigure(
            {
              idle: cleanedIdle,
              thinking: assets.thinking,
              speaking: assets.speaking,
              strong: assets.strong,
            },
            900
          );
          const backdrop = sampleBackdropGeometry(assets.backdrop);
          const sparks2d = createChestSparkMotes2D();

          processedRef.current = {
            assets,
            cleanedIdle,
            cleanedAssembly25,
            cleanedAssembly60,
            veins,
            listeningRings,
            edgeMotes,
            assembly,
            fig,
            backdrop,
            sparks2d,
          };
          if (!skippedRef.current) {
            assemblyStartRef.current = performance.now();
          }
          setAssetsReady(true);
        } catch (err) {
          setLoadError(
            err instanceof Error ? err.message : 'Failed to initialize particle sampling buffers.'
          );
        }
      })
      .catch((err) => {
        if (!mounted) return;
        setLoadError(
          err instanceof Error ? err.message : 'Required reference artwork failed to load.'
        );
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Restart assembly when assemblyTrigger increments
  useEffect(() => {
    if (assemblyTrigger > 0) {
      assemblyStartRef.current = performance.now();
      setIsAssembling(true);
      setHornPeakReached(false);
    }
  }, [assemblyTrigger]);

  // Diagnostics / Hand-pinch shockwave trigger (3D humanoid light pulse)
  useEffect(() => {
    if (shockwaveTrigger > 0) {
      clickPulseRef.current = {
        x: attentionRef.current.x,
        y: -attentionRef.current.y,
        strength: 1.0,
        time: performance.now(),
      };
    }
  }, [shockwaveTrigger, attentionRef]);

  // Pointer head turning & 3D particle click wavefront listener
  useEffect(() => {
    const getNormalizedPointer = (e: PointerEvent) => {
      const el = frameContainerRef.current;
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return null;
      return {
        x: clamp(((e.clientX - rect.left) / rect.width) * 2 - 1, -1, 1),
        y: clamp(((e.clientY - rect.top) / rect.height) * 2 - 1, -1, 1),
      };
    };

    const isFingerRecent = () => {
      const hold = attentionRef.current.fingerHold;
      return hold !== undefined && performance.now() - hold < 1200;
    };

    const onPointerMove = (e: PointerEvent) => {
      if (isFingerRecent()) return;
      const pt = getNormalizedPointer(e);
      if (pt) {
        attentionRef.current.x = pt.x;
        attentionRef.current.y = pt.y;
      }
    };

    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.closest('button') ||
          target.closest('aside') ||
          target.closest('nav') ||
          target.closest('header') ||
          target.closest('section'))
      ) {
        return;
      }
      const pt = getNormalizedPointer(e);
      if (pt) {
        if (!isFingerRecent()) {
          attentionRef.current.x = pt.x;
          attentionRef.current.y = pt.y;
        }
        clickPulseRef.current = {
          x: pt.x,
          y: -pt.y,
          strength: 1,
          time: performance.now(),
        };
      }
    };

    const onResetPointer = () => {
      if (!isFingerRecent()) {
        attentionRef.current.x = 0;
        attentionRef.current.y = 0;
      }
    };

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('blur', onResetPointer);
    document.documentElement.addEventListener('mouseleave', onResetPointer);

    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('blur', onResetPointer);
      document.documentElement.removeEventListener('mouseleave', onResetPointer);
    };
  }, [attentionRef]);

  // Main Three.js + 2D Assembly/Shadow Render Loop
  useEffect(() => {
    if (!assetsReady || !processedRef.current) return;
    const proc = processedRef.current;
    const fig = proc.fig;
    const mount = webglMountRef.current;
    const canvas2d = canvas2dRef.current;
    const frameEl = frameContainerRef.current;
    if (!mount || !canvas2d || !frameEl) return;

    const isHeadless =
      typeof navigator !== 'undefined' &&
      (navigator.webdriver || /HeadlessChrome/i.test(navigator.userAgent));

    const dpr = isHeadless ? 1 : Math.min(window.devicePixelRatio || 1, 1.75);

    // 1. Setup Three.js Renderer, Scene, Camera
    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: false,
      powerPreference: 'high-performance',
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.setPixelRatio(dpr);

    const glCanvas = renderer.domElement;
    glCanvas.style.position = 'absolute';
    glCanvas.style.inset = '0';
    glCanvas.style.width = '100%';
    glCanvas.style.height = '100%';
    glCanvas.style.pointerEvents = 'none';
    glCanvas.style.opacity = '0';
    glCanvas.style.transition = 'opacity 140ms ease';
    mount.innerHTML = '';
    mount.appendChild(glCanvas);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.05, 10);
    camera.position.set(0, 0, 3);

    // Create CanvasTextures with sRGB color space & no flipY (matching shader UV layout)
    const makePlateTexture = (plateCanvas: HTMLCanvasElement) => {
      const tex = new THREE.CanvasTexture(plateCanvas);
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.flipY = false;
      tex.generateMipmaps = false;
      tex.minFilter = THREE.LinearFilter;
      tex.magFilter = THREE.LinearFilter;
      tex.wrapS = THREE.ClampToEdgeWrapping;
      tex.wrapT = THREE.ClampToEdgeWrapping;
      return tex;
    };

    const textures = {
      idle: makePlateTexture(fig.plates.idle),
      thinking: makePlateTexture(fig.plates.thinking),
      speaking: makePlateTexture(fig.plates.speaking),
      strong: makePlateTexture(fig.plates.strong),
    };

    // Build Humanoid BufferGeometry
    const humanGeo = new THREE.BufferGeometry();
    humanGeo.setAttribute('position', new THREE.BufferAttribute(fig.pos, 3));
    humanGeo.setAttribute('aWeight', new THREE.BufferAttribute(fig.w, 1));
    humanGeo.setAttribute('aKind', new THREE.BufferAttribute(fig.kind, 1));
    humanGeo.setAttribute('aSize', new THREE.BufferAttribute(fig.size, 1));
    humanGeo.setAttribute('aBoil', new THREE.BufferAttribute(fig.boil, 4));
    humanGeo.setAttribute('aBright', new THREE.BufferAttribute(fig.bright, 4, true));
    humanGeo.setAttribute('aBucket', new THREE.BufferAttribute(fig.bucket, 4));
    humanGeo.setAttribute('aNx', new THREE.BufferAttribute(fig.nx, 1));
    humanGeo.setDrawRange(0, fig.count);

    const humanUniforms = {
      uYaw: { value: 0 },
      uPitch: { value: 0 },
      uBreathe: { value: 1 },
      uBreathY: { value: 0 },
      uBackK: { value: 0 },
      uVein: { value: 1 },
      uSize: { value: 2.9 },
      uPixelRatio: { value: dpr },
      uBoilT: { value: 0 },
      uVeinT: { value: 0 },
      uWaveT: { value: 0 },
      uBoilAmp: { value: 1 },
      uPivotY: { value: fig.pivotY },
      uStateA: { value: 0 },
      uStateB: { value: 0 },
      uBloomR: { value: 9 },
      uStrongMix: { value: 0 },
      uEnergy: { value: 0 },
      uRim: { value: 0.9 },
      uDotSharp: { value: 0.32 },
      uEffectsOff: { value: 0 },
      uAsmP: { value: 1 },
      uTexA: { value: textures.idle },
      uTexB: { value: textures.idle },
      uTexS: { value: textures.strong },
      uStrongA: { value: 0 },
      uStrongB: { value: 0 },
      uPulseA: { value: 1 },
      uPulseB: { value: 1 },
      uPatchUV: { value: 2.9 / 1020 },
      uAttn: { value: new THREE.Vector2(0, 0) },
      uClick: { value: new THREE.Vector4(0, 0, 0, 99) },
      uPalCyan: { value: new THREE.Color(...fig.palette[0]) },
      uPalPale: { value: new THREE.Color(...fig.palette[1]) },
    };

    const humanMat = new THREE.ShaderMaterial({
      uniforms: humanUniforms,
      vertexShader: HUMAN_VERTEX_SHADER,
      fragmentShader: HUMAN_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
    });

    const humanPoints = new THREE.Points(humanGeo, humanMat);
    humanPoints.frustumCulled = false;
    scene.add(humanPoints);

    // Build Lower-Chest Energy Cluster Geometry & Material (fU)
    const clusterGeo = new THREE.BufferGeometry();
    {
      let seed = 424171;
      const rng = () => ((seed = (seed * 16807) % 2147483647), (seed - 1) / 2147483646);
      const gauss = () => (rng() + rng() + rng() - 1.5) / 1.5;
      const cPos = new Float32Array(240 * 3);
      const cOff = new Float32Array(240 * 2);
      const cPh = new Float32Array(240);
      const cSp = new Float32Array(240);
      const cSz = new Float32Array(240);
      const cBr = new Float32Array(240);
      for (let i = 0; i < 240; i++) {
        cOff[i * 2] = gauss() * 0.056;
        cOff[i * 2 + 1] = gauss() * 0.048;
        cPh[i] = rng() * Math.PI * 2;
        cSp[i] = 0.6 + rng() * 1.8;
        cSz[i] = 0.7 + rng() * 1.4;
        cBr[i] = rng() < 0.2 ? 1 : 0;
      }
      clusterGeo.setAttribute('position', new THREE.BufferAttribute(cPos, 3));
      clusterGeo.setAttribute('aOff', new THREE.BufferAttribute(cOff, 2));
      clusterGeo.setAttribute('aPh', new THREE.BufferAttribute(cPh, 1));
      clusterGeo.setAttribute('aSp', new THREE.BufferAttribute(cSp, 1));
      clusterGeo.setAttribute('aSz', new THREE.BufferAttribute(cSz, 1));
      clusterGeo.setAttribute('aBr', new THREE.BufferAttribute(cBr, 1));
    }

    const clusterUniforms = {
      uT: { value: 0 },
      uStr: { value: 0.55 },
      uSizeK: { value: 1.6 },
      uPixelRatio: { value: dpr },
    };

    const clusterMat = new THREE.ShaderMaterial({
      uniforms: clusterUniforms,
      vertexShader: CLUSTER_VERTEX_SHADER,
      fragmentShader: CLUSTER_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    });

    const clusterPoints = new THREE.Points(clusterGeo, clusterMat);
    clusterPoints.renderOrder = 4;
    clusterPoints.frustumCulled = false;
    scene.add(clusterPoints);

    renderer.compile(scene, camera);

    const ctx2d = canvas2d.getContext('2d', { alpha: true })!;
    // Offscreen scratch canvases for assembly mask & glow
    const offscreen = {
      w: 0,
      h: 0,
      b: document.createElement('canvas'),
      bctx: null as CanvasRenderingContext2D | null,
      m: document.createElement('canvas'),
      mctx: null as CanvasRenderingContext2D | null,
      g: document.createElement('canvas'),
      gctx: null as CanvasRenderingContext2D | null,
    };

    const ensureOffscreen = (w: number, h: number) => {
      if (offscreen.w === w && offscreen.h === h && offscreen.bctx) return offscreen;
      offscreen.w = w;
      offscreen.h = h;
      offscreen.b.width = w;
      offscreen.b.height = h;
      offscreen.bctx = offscreen.b.getContext('2d', { alpha: true });
      offscreen.m.width = w;
      offscreen.m.height = h;
      offscreen.mctx = offscreen.m.getContext('2d', { alpha: true });
      offscreen.g.width = w;
      offscreen.g.height = h;
      offscreen.gctx = offscreen.g.getContext('2d', { alpha: true });
      return offscreen;
    };

    const syncViewportSize = () => {
      const rect = frameEl.getBoundingClientRect();
      const w = Math.max(1, Math.round(rect.width));
      const h = Math.max(1, Math.round(rect.height));
      renderer.setSize(w, h, false);
      const pw = Math.max(1, Math.round(w * dpr));
      const ph = Math.max(1, Math.round(h * dpr));
      if (canvas2d.width !== pw || canvas2d.height !== ph) {
        canvas2d.width = pw;
        canvas2d.height = ph;
      }
      return { w, h, pw, ph };
    };
    syncViewportSize();
    window.addEventListener('resize', syncViewportSize);

    let contextLost = false;
    const onLost = (e: Event) => {
      e.preventDefault();
      contextLost = true;
    };
    const onRestored = () => {
      contextLost = false;
    };
    glCanvas.addEventListener('webglcontextlost', onLost, false);
    glCanvas.addEventListener('webglcontextrestored', onRestored, false);

    // Mutable animation loop state
    let transitionState = createMoodTransitionState(livePropsRef.current.mood);
    let headYaw = 0;
    let headPitch = 0;
    let clusterTime = 0;
    let frameCount = 0;
    let fpsAccumTime = 0;
    let currentFps = 60;
    let lastTick = performance.now();
    let lastRenderTick = 0;
    let lastDiagTime = 0;
    let lastStatusStr = '';
    let wasAssembling = true;
    let wasHornPeak = false;
    let settledStartSec = -1;
    let rafId = 0;

    const getAspectFitRect = (
      imgW: number,
      imgH: number,
      canvasW: number,
      canvasH: number
    ) => {
      const imgAspect = imgW / Math.max(1, imgH);
      const canvasAspect = canvasW / Math.max(1, canvasH);
      let drawW = canvasW;
      let drawH = canvasH;
      let offsetX = 0;
      let offsetY = 0;

      if (canvasAspect > imgAspect) {
        drawW = canvasH * imgAspect;
        offsetX = (canvasW - drawW) * 0.5;
      } else {
        drawH = canvasW / imgAspect;
        offsetY = (canvasH - drawH) * 0.5;
      }

      return { offsetX, offsetY, drawW, drawH, imgAspect };
    };

    const drawCenteredImage = (
      targetCtx: CanvasRenderingContext2D,
      img: HTMLImageElement | HTMLCanvasElement,
      w: number,
      h: number,
      alpha = 1,
      scale = 1
    ) => {
      if (!img || alpha <= 0.002) return;
      const imgW = img.width || 1100;
      const imgH = img.height || 1100;
      const { offsetX, offsetY, drawW, drawH } = getAspectFitRect(imgW, imgH, w, h);

      targetCtx.save();
      targetCtx.globalAlpha = clamp(alpha, 0, 1);
      targetCtx.translate(w * 0.5, h * 0.5);
      targetCtx.scale(scale, scale);
      targetCtx.translate(-w * 0.5, -h * 0.5);
      targetCtx.drawImage(img, offsetX, offsetY, drawW, drawH);
      targetCtx.restore();
    };

    const drawChestSourceSparks2D = (
      targetCtx: CanvasRenderingContext2D,
      w: number,
      h: number,
      timeSec: number,
      alpha: number,
      speedMult = 1,
      coreGlow = 1
    ) => {
      if (alpha <= 0.01) return;
      const t = timeSec * speedMult;
      const cx = w * 0.5;
      const cy = h * 0.94;
      const rad = Math.min(w, h) * 0.034;
      const glowRad = Math.min(rad * 4.2, Math.max(4, h - cy - 1));

      targetCtx.save();
      targetCtx.globalCompositeOperation = 'lighter';
      if (coreGlow > 0.01) {
        const grad = targetCtx.createRadialGradient(cx, cy, 0, cx, cy, glowRad);
        grad.addColorStop(0, `rgba(235,255,255,${0.85 * alpha * coreGlow})`);
        grad.addColorStop(0.22, `rgba(90,228,255,${0.55 * alpha * coreGlow})`);
        grad.addColorStop(0.55, `rgba(25,130,200,${0.22 * alpha * coreGlow})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        targetCtx.fillStyle = grad;
        targetCtx.fillRect(cx - glowRad, cy - glowRad, glowRad * 2, glowRad * 2);
      }
      const scaleK = Math.min(w, h) / 1000;
      const ampK = 1 + (speedMult - 1) * 0.25;
      for (const s of proc.sparks2d) {
        const dx = Math.sin(t * s.sp + s.ph) * 0.004 * ampK;
        const dy = Math.cos(t * s.sp * 0.8 + s.ph) * 0.0035 * ampK;
        targetCtx.globalAlpha = alpha * (s.bright ? 0.9 : 0.5);
        targetCtx.fillStyle = s.bright ? '#d8fbff' : '#19ddff';
        const sz = s.size * scaleK;
        targetCtx.fillRect(cx + (s.ox + dx) * w - sz / 2, cy + (s.oy + dy) * h - sz / 2, sz, sz);
      }
      targetCtx.restore();
    };

    const drawEdgeBoil2D = (
      targetCtx: CanvasRenderingContext2D,
      w: number,
      h: number,
      dt: number,
      currentMood: MoodState,
      energy: number,
      alpha: number
    ) => {
      if (alpha <= 0.01 || !proc.edgeMotes.length) return;
      const speed =
        currentMood === 'speaking' || currentMood === 'strong'
          ? 2.6 + energy * 3
          : currentMood === 'listening'
            ? 2
            : currentMood === 'thinking'
              ? 1.5
              : 1;
      targetCtx.save();
      targetCtx.globalCompositeOperation = 'lighter';
      for (const m of proc.edgeMotes) {
        m.t += dt * m.rate * speed;
        const cycle = m.t % 1;
        const exc = Math.sin(Math.PI * cycle);
        const wob = Math.sin(m.t * 4.1) * m.wob;
        const px = (m.e.x + m.e.nx * exc * m.amp + m.e.ny * wob) * w;
        const py = (m.e.y + m.e.ny * exc * m.amp + m.e.nx * wob) * h;
        targetCtx.globalAlpha = alpha * (0.18 + 0.58 * exc) * (m.bright ? 1.3 : 1);
        targetCtx.fillStyle = m.bright ? '#d8fbff' : '#19ddff';
        targetCtx.beginPath();
        targetCtx.arc(px, py, (m.size * Math.min(w, h)) / 1000, 0, Math.PI * 2);
        targetCtx.fill();
      }
      targetCtx.restore();
    };

    const tick = (now: number) => {
      rafId = requestAnimationFrame(tick);
      if (document.hidden || contextLost) return;
      if (isHeadless && now - lastRenderTick < 66) return;
      lastRenderTick = now;

      const dt = Math.min(0.05, Math.max(0.001, (now - lastTick) / 1000));
      lastTick = now;
      const elapsedSec = now / 1000;

      frameCount++;
      fpsAccumTime += dt;
      if (fpsAccumTime >= 0.5) {
        currentFps = Math.round(frameCount / fpsAccumTime);
        frameCount = 0;
        fpsAccumTime = 0;
      }

      const {
        mood: targetMood,
        effectsEnabled: fx,
        reducedMotion: rm,
        tuning: tun,
        cameraStatus: camStat,
        onDiagnosticsUpdate: emitDiag,
        onAssemblyStatusChange: emitAsm,
      } = livePropsRef.current;

      const { w, h, pw, ph } = syncViewportSize();
      ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Compute Assembly & Shockwave metrics
      const asmElapsed = (now - assemblyStartRef.current) / 1000;
      const asmMetrics = computeAssemblyAndShockwave(asmElapsed, skippedRef.current, fx, rm);

      if (wasAssembling !== asmMetrics.isAssembling) {
        wasAssembling = asmMetrics.isAssembling;
        if (!asmMetrics.isAssembling) {
          settledStartSec = elapsedSec;
        }
        setIsAssembling(asmMetrics.isAssembling);
        emitAsm(
          asmMetrics.isAssembling,
          asmMetrics.isAssembling ? Math.round(asmMetrics.progress * 100) : 100
        );
      }

      const nowHornPeak = !asmMetrics.isAssembling || asmElapsed >= TIMING.hornPeak;
      if (wasHornPeak !== nowHornPeak) {
        wasHornPeak = nowHornPeak;
        setHornPeakReached(nowHornPeak);
      }

      // Assembly-completion shockwave ring (strictly driven by hornPeak at 6.808s, NEVER by user clicks)
      const birthWaveElapsed =
        skippedRef.current || !fx || rm ? 99 : asmElapsed - TIMING.hornPeak;
      const ringEl = shockwaveRingRef.current;
      if (ringEl) {
        if (birthWaveElapsed <= 0 || birthWaveElapsed > 4.5) {
          ringEl.style.opacity = '0';
        } else {
          const rect = frameEl.getBoundingClientRect();
          const ht = birthWaveElapsed * 0.75 * rect.height;
          const cx = rect.left + rect.width * 0.5;
          const cy = rect.top + rect.height * 0.43;
          const gn = 2.6 * ht;
          ringEl.style.opacity = String(Math.min(1, 0.9 * Math.exp(-birthWaveElapsed / 1.6)));
          ringEl.style.width = `${gn}px`;
          ringEl.style.height = `${gn}px`;
          ringEl.style.left = `${cx - gn * 0.5}px`;
          ringEl.style.top = `${cy - gn * 0.5}px`;
        }
      }

      // Mountain backdrop shockwave (strictly driven by hornPeak at 6.808s)
      const backdropWaveActive = birthWaveElapsed >= 0 && birthWaveElapsed < 4.5 && fx && !rm;
      shockwaveRef.current = {
        active: backdropWaveActive,
        elapsed: backdropWaveActive ? birthWaveElapsed : 99,
        originX: 0,
        originY: 0.14,
        strength: backdropWaveActive ? 1.0 : 0,
      };

      const breathScale2D = !fx || rm ? 1 : 1 + Math.sin(elapsedSec * 0.95) * 0.0035;
      let assemblyPctValue = 100;
      const endRamp = asmMetrics.isAssembling
        ? clamp((asmMetrics.progress - 0.84) / 0.16, 0, 1)
        : 0;

      if (asmMetrics.isAssembling) {
        // Stage 4/5: 2D Assembly Renderer (Progressive left-to-right reveal + 9,500 cubic-Bézier particles)
        glCanvas.style.opacity = '0';
        ctx2d.fillStyle = '#000';
        ctx2d.fillRect(0, 0, w, h);

        const off = ensureOffscreen(pw, ph);
        const revealEdge = 0.06 + ((asmElapsed - 1.75) * 0.88) / 4.6;
        if (revealEdge > 0.01 && off.bctx && off.mctx) {
          off.bctx.globalCompositeOperation = 'source-over';
          off.bctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          off.bctx.fillStyle = '#000';
          off.bctx.fillRect(0, 0, w, h);
          drawCenteredImage(off.bctx, proc.cleanedIdle, w, h, 1, breathScale2D);

          off.mctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          off.mctx.clearRect(0, 0, w, h);
          const grad = off.mctx.createLinearGradient(
            (revealEdge - 0.12) * w,
            0,
            (revealEdge + 0.05) * w,
            0
          );
          grad.addColorStop(0, 'rgba(255,255,255,1)');
          grad.addColorStop(1, 'rgba(255,255,255,0)');
          off.mctx.fillStyle = grad;
          off.mctx.fillRect(0, 0, w, h);

          off.bctx.globalCompositeOperation = 'destination-in';
          off.bctx.setTransform(1, 0, 0, 1, 0, 0);
          off.bctx.drawImage(off.m, 0, 0);
          off.bctx.globalCompositeOperation = 'source-over';
          ctx2d.drawImage(off.b, 0, 0, pw, ph, 0, 0, w, h);
        }

        const asm = proc.assembly;
        const imgAspect = asm.aspectRatio || 1;
        const { offsetX, offsetY, drawW, drawH } = getAspectFitRect(
          372,
          Math.round(372 / imgAspect),
          w,
          h
        );
        const toPxX = (nx: number) => offsetX + nx * drawW;
        const toPxY = (ny: number) => offsetY + ny * drawH;

        let settledCount = 0;
        ctx2d.save();
        ctx2d.globalCompositeOperation = 'lighter';
        const dotScale = Math.min(w, h) / 1000;

        for (const bucket of asm.buckets) {
          ctx2d.fillStyle = bucket.color;
          const indices = bucket.idx;
          for (let j = 0; j < indices.length; j++) {
            const idx = indices[j];
            const localT = (asmElapsed - asm.delay[idx]) / asm.dur[idx];
            if (localT <= 0) continue;
            let px: number;
            let py: number;
            if (localT < 1) {
              px = evaluateCubicBezier(
                localT,
                toPxX(asm.sx[idx]),
                toPxX(asm.c1x[idx]),
                toPxX(asm.c2x[idx]),
                toPxX(asm.x[idx])
              );
              py = evaluateCubicBezier(
                localT,
                toPxY(asm.sy[idx]),
                toPxY(asm.c1y[idx]),
                toPxY(asm.c2y[idx]),
                toPxY(asm.y[idx])
              );
              const u = smooth01(localT);
              ctx2d.globalAlpha = 0.45 + 0.5 * u;
            } else {
              settledCount++;
              const fadeOut = 1 - smooth01((asmElapsed - asm.delay[idx] - asm.dur[idx] - 0.35) / 0.8);
              if (fadeOut <= 0.015) continue;
              px = toPxX(asm.x[idx]);
              py = toPxY(asm.y[idx]);
              ctx2d.globalAlpha = fadeOut * 0.9;
            }
            const sz = asm.size[idx] * dotScale;
            ctx2d.fillRect(px - sz * 0.5, py - sz * 0.5, sz, sz);
          }
        }
        ctx2d.restore();

        assemblyPctValue = Math.min(
          99,
          Math.max(
            1,
            Math.round(
              Math.max(asmMetrics.progress, (settledCount / Math.max(1, asm.n)) * 0.99) * 100
            )
          )
        );

        const sourceAlpha =
          Math.max(0.55, 1 - smooth01((asmMetrics.progress - 0.82) / 0.15)) *
          smooth01(asmElapsed / 0.5);
        drawChestSourceSparks2D(ctx2d, w, h, elapsedSec, sourceAlpha, 2 + 3 * endRamp, 1);

        // Ignition radial face glow during final 16% of assembly
        const ignitionFaceGlow = Math.sin(Math.PI * Math.min(0.5, endRamp));
        if (ignitionFaceGlow > 0.01 && off.gctx) {
          off.gctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          off.gctx.globalCompositeOperation = 'source-over';
          off.gctx.clearRect(0, 0, w, h);
          off.gctx.fillStyle = '#000';
          off.gctx.fillRect(0, 0, w, h);
          drawCenteredImage(off.gctx, proc.cleanedIdle, w, h, 1, breathScale2D);
          const faceGrad = off.gctx.createRadialGradient(
            w * 0.5,
            h * 0.43,
            0,
            w * 0.5,
            h * 0.43,
            w * 0.37
          );
          faceGrad.addColorStop(0, 'rgba(255,255,255,1)');
          faceGrad.addColorStop(1, 'rgba(255,255,255,0)');
          off.gctx.globalCompositeOperation = 'destination-in';
          off.gctx.fillStyle = faceGrad;
          off.gctx.fillRect(0, 0, w, h);

          ctx2d.save();
          ctx2d.globalCompositeOperation = 'lighter';
          ctx2d.globalAlpha = ignitionFaceGlow * 0.8;
          ctx2d.drawImage(off.g, 0, 0, pw, ph, 0, 0, w, h);
          ctx2d.restore();
        }

        if (fx && !rm) {
          drawEdgeBoil2D(
            ctx2d,
            w,
            h,
            dt,
            'idle',
            0,
            smooth01((asmMetrics.progress - 0.6) / 0.4) * (0.8 + 1.4 * endRamp)
          );
        }
      } else {
        // Settled 3D Mode: Show Three.js canvas and draw only soft silhouette shadow over mountain backdrop
        glCanvas.style.opacity = '1';
        ctx2d.clearRect(0, 0, w, h);
        if (livePropsRef.current.compareActive && livePropsRef.current.tuning.compareMode === 'split') {
          ctx2d.fillStyle = '#000';
          ctx2d.fillRect(0, 0, w, h);
        } else if (fig.shadow) {
          drawCenteredImage(ctx2d, fig.shadow, w, h, 1, 1);
        }

        if (fx && !rm) {
          const spkEn =
            targetMood === 'strong'
              ? Math.max(0.82, tun.speakingEnergy)
              : targetMood === 'speaking'
                ? tun.speakingEnergy
                : 0;
          drawEdgeBoil2D(ctx2d, w, h, dt, targetMood, spkEn, 1);
        }
      }

      // Step Stage 3 Face-Centred Radial Mood Transition
      const effectiveMood: MoodState = asmMetrics.isAssembling ? 'idle' : targetMood;
      const stepped = stepMoodTransition(transitionState, effectiveMood, dt, rm || !fx);
      transitionState = stepped.state;

      const plateArray = [textures.idle, textures.thinking, textures.speaking];
      humanUniforms.uAsmP.value = 1.0;
      humanUniforms.uStateA.value = transitionState.a;
      humanUniforms.uStateB.value = transitionState.b;
      humanUniforms.uBloomR.value = stepped.bloomRadius;
      humanUniforms.uTexA.value = plateArray[transitionState.a];
      humanUniforms.uTexB.value = plateArray[transitionState.b];

      // Speaking & Strong Speaking Energy
      const micVal = micEnergyRef.current;
      const baseEnergy =
        effectiveMood === 'strong'
          ? Math.max(0.85, tun.speakingEnergy, micVal)
          : effectiveMood === 'speaking'
            ? Math.max(tun.speakingEnergy, micVal)
            : 0;
      const strongMix =
        effectiveMood === 'strong' ? 1.0 : smooth01((baseEnergy - 0.34) / 0.4);

      humanUniforms.uEnergy.value = baseEnergy;
      humanUniforms.uStrongMix.value = strongMix;
      humanUniforms.uStrongA.value =
        transitionState.a === 2
          ? transitionState.moodA === 'strong'
            ? 1
            : strongMix
          : 0;
      humanUniforms.uStrongB.value =
        transitionState.b === 2
          ? transitionState.moodB === 'strong'
            ? 1
            : strongMix
          : 0;

      const surgeBoost = 1 + 0.9 * asmMetrics.birthSurge;
      const thinkPulse = fx && !rm ? 1 + 0.02 * Math.sin(elapsedSec * 2.1) : 1;
      humanUniforms.uPulseA.value = (transitionState.a === 1 ? thinkPulse : 1) * surgeBoost;
      humanUniforms.uPulseB.value = (transitionState.b === 1 ? thinkPulse : 1) * surgeBoost;

      // Stage 5: Mouse / Finger Head Turning
      const headTurn = computeHeadTurn(
        asmMetrics.isAssembling ? 0 : attentionRef.current.x,
        asmMetrics.isAssembling ? 0 : attentionRef.current.y,
        headYaw,
        headPitch,
        dt,
        effectiveMood,
        tun.turnSensitivity,
        fx,
        rm
      );
      headYaw = headTurn.yaw;
      headPitch = headTurn.pitch;
      humanUniforms.uYaw.value = headYaw;
      humanUniforms.uPitch.value = headPitch;
      humanUniforms.uBackK.value = headTurn.backK;

      // Stage 8: Chest Breathing
      const breathing = computeBreathing(elapsedSec, fx, rm);
      humanUniforms.uBreathe.value = breathing.uBreathe;
      humanUniforms.uBreathY.value = breathing.uBreathY;

      // Stage 7: 3D Click Wavefront & Birth Shockwave in Humanoid Shader
      const clickAge = (now - clickPulseRef.current.time) / 1000;
      const clickStr =
        clickPulseRef.current.strength > 0.5 && clickAge >= 0 && clickAge < 2.5
          ? Math.exp(-clickAge * 1.9)
          : 0;

      let uClickX = 0;
      let uClickY = 0;
      let uClickZ = 0;
      let uClickW = 99;

      if (clickStr > 0.001 && fx && !rm) {
        uClickX = clickPulseRef.current.x;
        uClickY = clickPulseRef.current.y;
        uClickZ = clickStr;
        uClickW = clickAge;
      } else if (birthWaveElapsed >= 0 && birthWaveElapsed < 4.0 && fx && !rm) {
        uClickX = 0;
        uClickY = 0.14;
        uClickZ = 1.35 * Math.exp(-birthWaveElapsed / 1.6);
        uClickW = birthWaveElapsed * (1.5 / 2.6);
      }
      humanUniforms.uClick.value.set(uClickX, uClickY, uClickZ, uClickW);

      // Advance dynamic shader clocks (click accelerates edge boil & chest spark cluster by up to 2.5x)
      const boostAge = clickStr > 0.001 ? clickAge : uClickW;
      const clickBoost =
        fx && !rm && boostAge >= 0 && boostAge < 3 ? 1 + 1.5 * Math.exp(-boostAge / 0.6) : 1;
      const isSpeaking = effectiveMood === 'speaking' || effectiveMood === 'strong';
      const isListening = effectiveMood === 'listening';
      const isThinking = effectiveMood === 'thinking';

      humanUniforms.uEffectsOff.value = !fx || rm ? 1.0 : 0.0;
      humanUniforms.uVein.value =
        !fx || rm
          ? 1.0
          : (isSpeaking ? 0.85 + baseEnergy * 0.55 : isListening ? 1.05 : 1.0) *
            (1 + asmMetrics.birthSurge);

      if (fx && !rm) {
        humanUniforms.uBoilT.value +=
          dt *
          (isSpeaking ? 2.6 + baseEnergy * 3 : isListening ? 2.0 : isThinking ? 1.5 : 1.0) *
          clickBoost *
          (1 + 3 * asmMetrics.birthSurge);
        humanUniforms.uVeinT.value += dt * (isSpeaking ? 0.55 : isListening ? 0.45 : 0.25);
        humanUniforms.uWaveT.value += dt;
      }

      humanUniforms.uBoilAmp.value = tun.boilAmp * (1 + 2.8 * asmMetrics.birthSurge);
      humanUniforms.uRim.value = tun.rimStrength;
      humanUniforms.uDotSharp.value = tun.dotSharpness;
      humanUniforms.uSize.value = 2.9 * Math.max(0.6, h / 1020);
      humanUniforms.uPatchUV.value = humanUniforms.uSize.value / Math.max(1, h);
      humanUniforms.uAttn.value.set(
        clamp(attentionRef.current.x, -1, 1),
        -clamp(attentionRef.current.y, -1, 1)
      );

      // Update Lower-Chest Energy Cluster
      clusterPoints.visible = fx && !rm && !asmMetrics.isAssembling;
      if (fx && !rm) {
        const clusterSpeed = isSpeaking
          ? 2.2 + baseEnergy * 2
          : isListening
            ? 1.6
            : isThinking
              ? 1.3
              : 1.0;
        clusterTime += dt * clusterSpeed * clickBoost * (1 + 3 * asmMetrics.birthSurge);
        clusterUniforms.uT.value = clusterTime;
        clusterUniforms.uStr.value = 0.55 * (1 + 2 * asmMetrics.birthSurge);
        clusterUniforms.uSizeK.value = 1.6 * Math.max(0.6, h / 1020);
      }

      if (!asmMetrics.isAssembling) {
        renderer.render(scene, camera);
      }

      const nextStatus = asmMetrics.isAssembling
        ? `ASSEMBLING... ${assemblyPctValue}%`
        : targetMood === 'strong'
          ? 'STATUS: SPEAKING · INTENSITY: HIGH'
          : `STATUS: ${targetMood.toUpperCase()}`;
      if (nextStatus !== lastStatusStr) {
        lastStatusStr = nextStatus;
        setStatusText(nextStatus);
        emitAsm(asmMetrics.isAssembling, assemblyPctValue);
      }

      if (now - lastDiagTime > 250) {
        lastDiagTime = now;
        emitDiag({
          fps: currentFps,
          totalParticles: fig.count + 240,
          frontParticles: fig.frontCount,
          backParticles: fig.backCount,
          dustParticles: fig.dustCount,
          boilParticles: fig.boilCount,
          backdropParticles: proc.backdrop.pointCount,
          assemblyParticles: proc.assembly.n,
          yawDeg: (headYaw * 180) / Math.PI,
          pitchDeg: (headPitch * 180) / Math.PI,
          bloomRadius: stepped.bloomRadius,
          moodA: transitionState.moodA,
          moodB: transitionState.moodB,
          assemblyPct: assemblyPctValue,
          shockwaveActive: backdropWaveActive,
          cameraStatus: camStat,
        });
      }
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', syncViewportSize);
      glCanvas.removeEventListener('webglcontextlost', onLost);
      glCanvas.removeEventListener('webglcontextrestored', onRestored);
      humanGeo.dispose();
      humanMat.dispose();
      clusterGeo.dispose();
      clusterMat.dispose();
      Object.values(textures).forEach((t) => t.dispose());
      renderer.dispose();
    };
  }, [assetsReady, attentionRef, micEnergyRef]);

  // Select reference image for Stage 2 Source Comparison
  const currentReferenceSrc =
    mood === 'listening'
      ? ASSET_PATHS.listening
      : mood === 'thinking'
        ? ASSET_PATHS.thinking
        : mood === 'speaking'
          ? ASSET_PATHS.speaking
          : mood === 'strong'
            ? ASSET_PATHS.strong
            : ASSET_PATHS.idle;

  return (
    <div
      data-testid="humanoid-viewport"
      data-assembling={isAssembling ? 'true' : 'false'}
      className={`relative w-full h-full overflow-hidden ${
        isAssembling ? 'bg-black' : 'bg-[#050608]'
      } select-none`}
    >
      {/* Stage 6: Atmospheric Mountain Backdrop (fades in when assembly completes) */}
      <BackdropCanvas
        sampled={processedRef.current?.backdrop ?? null}
        visible={assetsReady && tuning.backdropVisible && !isAssembling}
        pointsVisible={assetsReady && tuning.backdropVisible && !isAssembling}
        effectsEnabled={effectsEnabled}
        reducedMotion={reducedMotion}
        shockwaveRef={shockwaveRef}
      />

      {/* Loading / Error Fallback Banner */}
      {loadError && (
        <div
          role="alert"
          className="fixed inset-x-0 top-20 mx-auto max-w-md z-50 rounded-xl border border-red-400/50 bg-[#050608]/95 p-4 text-center text-xs text-red-200"
        >
          <div className="font-semibold uppercase tracking-wider mb-1">
            Reference Artwork Load Error
          </div>
          <div>{loadError}</div>
        </div>
      )}

      {!assetsReady && !loadError && (
        <div className="fixed inset-0 z-20 grid place-items-center pointer-events-none">
          <div className="text-center space-y-2">
            <div className="text-[#00E5FF] text-sm tracking-[0.28em] uppercase">
              SAMPLING REFERENCE PLATES...
            </div>
            <div className="text-[#C8F7FF]/60 text-xs tracking-widest">
              Constructing 3D contour particle buffers
            </div>
          </div>
        </div>
      )}

      {/* Main Centered Humanoid Portrait Frame */}
      <div
        ref={frameContainerRef}
        data-testid="humanoid-portrait-frame"
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 overflow-hidden"
        style={{
          width:
            compareActive && tuning.compareMode === 'side-by-side'
              ? 'min(46vw, 82vh)'
              : 'min(100vw, 100vh)',
          height:
            compareActive && tuning.compareMode === 'side-by-side'
              ? 'min(46vw, 82vh)'
              : 'min(100vw, 100vh)',
          left: compareActive && tuning.compareMode === 'side-by-side' ? '73%' : '50%',
          transition: 'width 220ms ease, height 220ms ease, left 220ms ease',
        }}
      >
        {/* 2D Canvas Layer (Assembly cubic-Bézier particles, silhouette shadow, edge motes) */}
        <canvas
          ref={canvas2dRef}
          aria-label="Animated cyan and gold APEX humanoid"
          className="block w-full h-full"
        />

        {/* Listening Mode Concentric Rings Overlay */}
        {listeningRingUrl && assetsReady && mood === 'listening' && (
          <div aria-hidden="true" className="absolute inset-0 pointer-events-none">
            <img
              src={listeningRingUrl}
              alt=""
              referrerPolicy="no-referrer"
              className="absolute inset-0 w-full h-full"
              style={{
                mixBlendMode: 'plus-lighter',
                opacity: effectsEnabled && !reducedMotion ? undefined : 0.28,
                animation:
                  effectsEnabled && !reducedMotion
                    ? 'humRingBase 3.4s ease-in-out infinite'
                    : 'none',
              }}
            />
            {effectsEnabled && !reducedMotion && (
              <>
                <img
                  src={listeningRingUrl}
                  alt=""
                  referrerPolicy="no-referrer"
                  className="absolute inset-0 w-full h-full"
                  style={{
                    mixBlendMode: 'plus-lighter',
                    animation: 'humRingPulse 4.55s linear infinite',
                  }}
                />
                <img
                  src={listeningRingUrl}
                  alt=""
                  referrerPolicy="no-referrer"
                  className="absolute inset-0 w-full h-full"
                  style={{
                    mixBlendMode: 'plus-lighter',
                    animation: 'humRingPulse 4.55s linear infinite',
                    animationDelay: '2.27s',
                  }}
                />
              </>
            )}
          </div>
        )}

        {/* 3D Three.js Particle Canvas Mount */}
        <div
          ref={webglMountRef}
          data-testid="threejs-particle-mount"
          className="absolute inset-0 pointer-events-none"
        />

        {/* Stage 2: Split-Screen or Overlay Original Source Image Comparison */}
        {compareActive && tuning.compareMode === 'split' && (
          <div
            data-testid="compare-split-overlay"
            className="absolute inset-0 pointer-events-none overflow-hidden"
            style={{
              clipPath: `inset(0 ${Math.round((1 - tuning.compareSplit) * 100)}% 0 0)`,
            }}
          >
            <img
              src={currentReferenceSrc}
              alt="Original APEX reference artwork"
              referrerPolicy="no-referrer"
              draggable={false}
              className="w-full h-full object-contain bg-black"
            />
            <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-[#050608]/90 border border-[#FFB733]/50 text-[#FFB733] text-[10px] tracking-widest uppercase">
              Original Source Artwork ({mood.toUpperCase()})
            </div>
          </div>
        )}

        {compareActive && tuning.compareMode === 'split' && (
          <>
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-[#00E5FF] shadow-[0_0_12px_#00E5FF] pointer-events-none"
              style={{ left: `${tuning.compareSplit * 100}%` }}
            />
            <div className="absolute top-4 right-4 px-2.5 py-1 rounded bg-[#050608]/90 border border-[#00E5FF]/50 text-[#00E5FF] text-[10px] tracking-widest uppercase pointer-events-none">
              Three.js Particle Render
            </div>
          </>
        )}

        {compareActive && tuning.compareMode === 'overlay' && (
          <div
            data-testid="compare-direct-overlay"
            className="absolute inset-0 pointer-events-none"
          >
            <img
              src={currentReferenceSrc}
              alt="Original APEX reference artwork overlay"
              referrerPolicy="no-referrer"
              draggable={false}
              className="w-full h-full object-contain opacity-50 mix-blend-difference"
            />
            <div className="absolute top-4 left-4 px-2.5 py-1 rounded bg-[#050608]/90 border border-[#00E5FF]/50 text-[#00E5FF] text-[10px] tracking-widest uppercase">
              50% Alignment Overlay · Source vs Particle Render
            </div>
          </div>
        )}


        <div
          aria-live="polite"
          data-testid="humanoid-status-readout"
          className={`absolute top-2.5 sm:top-[16%] left-1/2 -translate-x-1/2 sm:left-auto sm:translate-x-0 ${
            techDetailsOpen ? 'sm:right-[350px]' : 'sm:right-[5.8%]'
          } max-w-[90%] sm:max-w-[32%] px-2 py-0.5 rounded sm:rounded-none bg-[#050608]/75 sm:bg-transparent backdrop-blur-xs sm:backdrop-blur-none border border-[#00E5FF]/20 sm:border-0 text-center sm:text-right text-[#00E5FF] tracking-[0.16em] leading-relaxed pointer-events-none transition-all duration-200 z-10`}
          style={{
            fontSize: 'clamp(10px, 1.1vmin, 13px)',
            textShadow: '0 0 12px rgba(0, 229, 255, 0.55)',
          }}
        >
          <div>{statusText}</div>
          {!effectsEnabled && (
            <div className="text-[#FFB733] text-[10px] tracking-widest mt-0.5">
              BASELINE MODE · EFFECTS OFF
            </div>
          )}
          {reducedMotion && (
            <div className="text-[#C8F7FF]/75 text-[10px] tracking-widest mt-0.5">
              REDUCED MOTION ACTIVE
            </div>
          )}
        </div>
      </div>

      {/* Stage 2: Side-by-Side Original Reference Frame when compareMode === 'side-by-side' */}
      {compareActive && tuning.compareMode === 'side-by-side' && (
        <div
          data-testid="compare-side-by-side-source"
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 overflow-hidden border border-[#FFB733]/35 rounded-lg bg-[#050608]"
          style={{
            left: '27%',
            width: 'min(46vw, 82vh)',
            height: 'min(46vw, 82vh)',
          }}
        >
          <img
            src={currentReferenceSrc}
            alt="Original source reference artwork"
            referrerPolicy="no-referrer"
            draggable={false}
            className="w-full h-full object-contain"
          />
          <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-[#050608]/90 border border-[#FFB733]/50 text-[#FFB733] text-[10px] tracking-widest uppercase">
            Source Reference ({mood.toUpperCase()})
          </div>
        </div>
      )}

      {/* Assembly-completion shockwave ring (strictly driven by hornPeak at 6.808s, never by user clicks) */}
      <div
        ref={shockwaveRingRef}
        data-testid="assembly-shockwave-ring"
        aria-hidden="true"
        className="fixed left-0 top-0 w-0 h-0 rounded-full pointer-events-none opacity-0 z-10"
        style={{
          mixBlendMode: 'screen',
          background:
            'radial-gradient(circle, rgba(0,0,0,0) 0 58%, rgba(150,225,255,0.8) 77%, rgba(0,0,0,0) 96%)',
          willChange: 'width, height, left, top, opacity',
        }}
      />
    </div>
  );
};
