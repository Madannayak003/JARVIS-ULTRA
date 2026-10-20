import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { ASSET_PATHS, BackdropSampledGeometry } from '../utils/imageSampling';
import { BACKDROP_FRAGMENT_SHADER, BACKDROP_VERTEX_SHADER } from '../utils/shaders';

export interface ShockwaveRefState {
  active: boolean;
  elapsed: number;
  originX: number;
  originY: number;
  strength: number;
}

interface BackdropCanvasProps {
  sampled: BackdropSampledGeometry | null;
  visible: boolean;
  pointsVisible?: boolean;
  effectsEnabled: boolean;
  reducedMotion: boolean;
  shockwaveRef: React.MutableRefObject<ShockwaveRefState>;
}

export const BackdropCanvas: React.FC<BackdropCanvasProps> = ({
  sampled,
  visible,
  pointsVisible,
  effectsEnabled,
  reducedMotion,
  shockwaveRef,
}) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const effectivePointsVisible = pointsVisible !== undefined ? pointsVisible : visible;
  const stateRef = useRef({ visible: effectivePointsVisible, effectsEnabled, reducedMotion });
  stateRef.current = { visible: effectivePointsVisible, effectsEnabled, reducedMotion };

  useEffect(() => {
    const container = mountRef.current;
    if (!container || !sampled) return;

    const isHeadless =
      typeof navigator !== 'undefined' &&
      (navigator.webdriver || /HeadlessChrome/i.test(navigator.userAgent));

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: false,
      powerPreference: 'high-performance',
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    const dpr = isHeadless ? 1 : Math.min(window.devicePixelRatio || 1, 1.5);
    renderer.setPixelRatio(dpr);

    const canvas = renderer.domElement;
    canvas.style.position = 'absolute';
    canvas.style.inset = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.mixBlendMode = 'screen';
    container.innerHTML = '';
    container.appendChild(canvas);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 2);
    camera.position.z = 1;

    const uniforms = {
      uT: { value: 0 },
      uPixelRatio: { value: dpr },
      uSizeK: { value: 1 },
      uRest: { value: 0.22 },
      uPulse: { value: 2.6 },
      uMap: { value: new THREE.Vector4(2, -2, -1, 1) },
      uWave: { value: new THREE.Vector4(0, 0, 0, 0) },
      uWaveK: { value: new THREE.Vector2(1.78, 0.4) },
    };

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: BACKDROP_VERTEX_SHADER,
      fragmentShader: BACKDROP_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    });

    const points = new THREE.Points(sampled.geometry, material);
    points.frustumCulled = false;
    scene.add(points);

    const updateSize = () => {
      const w = Math.max(1, container.clientWidth || window.innerWidth);
      const h = Math.max(1, container.clientHeight || window.innerHeight);
      renderer.setSize(w, h, false);
      uniforms.uSizeK.value = Math.max(0.6, h / 1020);

      const scale = Math.max(w / sampled.aspect, h);
      const imgW = scale * sampled.aspect;
      const imgH = scale;
      const offX = (w - imgW) * 0.5;
      const offY = (h - imgH) * 0.42;

      uniforms.uMap.value.set(
        (imgW / w) * 2,
        -(imgH / h) * 2,
        (offX / w) * 2 - 1,
        1 - (offY / h) * 2
      );
    };
    updateSize();
    window.addEventListener('resize', updateSize);

    let contextLost = false;
    const onLost = (e: Event) => {
      e.preventDefault();
      contextLost = true;
    };
    const onRestored = () => {
      contextLost = false;
    };
    canvas.addEventListener('webglcontextlost', onLost, false);
    canvas.addEventListener('webglcontextrestored', onRestored, false);

    let rafId = 0;
    let lastTime = performance.now();
    let lastRenderTime = 0;

    const tick = (now: number) => {
      rafId = requestAnimationFrame(tick);
      if (document.hidden || contextLost) return;

      const { visible: vis, effectsEnabled: fx, reducedMotion: rm } = stateRef.current;
      const sw = shockwaveRef.current;
      if (!vis && !sw.active) return;
      if (!fx || rm) return;

      if (isHeadless && now - lastRenderTime < 66) return;
      lastRenderTime = now;

      const dt = Math.min(0.05, (now - lastTime) / 1000);
      lastTime = now;

      uniforms.uT.value += dt;

      const w = Math.max(1, container.clientWidth || window.innerWidth);
      const h = Math.max(1, container.clientHeight || window.innerHeight);
      const minScale = Math.min(w, h) / h;

      if (sw.active && sw.elapsed >= 0 && sw.elapsed < 4.5) {
        uniforms.uWave.value.set(
          sw.originX * minScale,
          sw.originY * minScale,
          sw.elapsed * 1.5 * minScale,
          Math.exp(-sw.elapsed / 1.8) * sw.strength
        );
        uniforms.uWaveK.value.set(w / h, 0.45 * minScale);
      } else {
        uniforms.uWave.value.w = 0;
      }

      renderer.render(scene, camera);
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', updateSize);
      canvas.removeEventListener('webglcontextlost', onLost);
      canvas.removeEventListener('webglcontextrestored', onRestored);
      material.dispose();
      renderer.dispose();
    };
  }, [sampled, shockwaveRef]);

  const showDynamicHighlights = effectivePointsVisible && effectsEnabled && !reducedMotion;

  return (
    <div
      data-testid="backdrop-layer"
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none select-none overflow-hidden"
    >
      <img
        src={ASSET_PATHS.backdrop}
        alt="Atmospheric mountain range backdrop"
        referrerPolicy="no-referrer"
        draggable={false}
        className="absolute inset-0 w-full h-full object-cover"
        style={{
          objectPosition: 'center 42%',
          opacity: visible ? 1 : 0,
          transition: reducedMotion ? 'none' : 'opacity 900ms ease',
        }}
      />
      <div
        ref={mountRef}
        className="absolute inset-0"
        style={{
          opacity: showDynamicHighlights ? 1 : 0,
          transition: reducedMotion ? 'none' : 'opacity 900ms ease',
        }}
      />
    </div>
  );
};
