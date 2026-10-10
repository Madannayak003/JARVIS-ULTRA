import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";

export interface OrbSceneApi {
  /** Rotate the camera around the orb by the given angles (radians). */
  rotateBy(deltaTheta: number, deltaPhi: number): void;

  /** Change the ULTRON visual color. */
  setUltronColor(color: string | number): void;

  /** Multiply the camera distance by `factor` (<1 zooms in, >1 zooms out). */
  zoomBy(factor: number): void;
  zoomIn(): void;
  zoomOut(): void;
  resetView(): void;
  dispose(): void;
}

const HOME_POSITION = new THREE.Vector3(0, 0.5, 5.5);
const MIN_DISTANCE = 0.6;
const MAX_DISTANCE = 40;

type UltronColorRole = "bright" | "mid" | "dim" | "faint" | "hot";

interface SpriteDrift {
  phi: number;
  theta: number;
  r: number;
  speed: number;
}

interface DebrisOrbit {
  orbitR: number;
  speed: number;
  tiltX: number;
  tiltZ: number;
  phase: number;
}

export function createOrbScene(container: HTMLElement): OrbSceneApi {
  const width = Math.max(1, container.clientWidth);
  const height = Math.max(1, container.clientHeight);

  // * ═══════════════════════════════════════════════
  // * SCENE
  // * ═══════════════════════════════════════════════
  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(
    55,
    width / height,
    0.1,
    500,
  );
  camera.position.copy(HOME_POSITION);

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
  });

  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.85;
  container.appendChild(renderer.domElement);

  // * ═══════════════════════════════════════════════
  // * POST PROCESSING
  // * ═══════════════════════════════════════════════
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));

  const bloom = new UnrealBloomPass(
    new THREE.Vector2(width, height),
    1.8,
    0.4,
    0.2,
  );
  composer.addPass(bloom);

  // * The color is driven by uColor so the HUD can switch ULTRON
  // * between red / blue / cyan / purple / green / orange / white.
  const chromaticShader = {
    uniforms: {
      tDiffuse: { value: null },
      uTime: { value: 0 },
      uIntensity: { value: 0.003 },
      uColor: { value: new THREE.Color(0xff2020) },
    },

    vertexShader: `
      varying vec2 vUv;

      void main() {
        vUv = uv;
        gl_Position =
          projectionMatrix *
          modelViewMatrix *
          vec4(position, 1.0);
      }
    `,

    fragmentShader: `
      uniform sampler2D tDiffuse;
      uniform float uTime;
      uniform float uIntensity;
      uniform vec3 uColor;

      varying vec2 vUv;

      void main() {
        vec2 dir = vUv - vec2(0.5);
        float d = length(dir);
        float offset = uIntensity * d;

        float flicker =
          1.0 +
          0.012 *
          sin(uTime * 30.0) *
          sin(uTime * 7.3);

        vec4 cr =
          texture2D(tDiffuse, vUv + dir * offset);

        vec4 cg =
          texture2D(tDiffuse, vUv);

        vec4 cb =
          texture2D(
            tDiffuse,
            vUv - dir * offset * 0.5
          );

        vec3 rgb =
          vec3(
            cr.r,
            cg.g,
            cb.b
          );

        // * Convert the warm base image into a controlled
        // * ULTRON accent without destroying the glow.
        float luminance =
          dot(
            rgb,
            vec3(0.299, 0.587, 0.114)
          );

        vec3 graded =
          mix(
            rgb,
            uColor * luminance * 2.2,
            0.34
          );

        gl_FragColor =
          vec4(
            max(rgb, graded) * flicker,
            1.0
          );
      }
    `,
  };

  const chromaticPass = new ShaderPass(chromaticShader);
  composer.addPass(chromaticPass);

  // * ═══════════════════════════════════════════════
  // * CAMERA CONTROLS
  // * ═══════════════════════════════════════════════
  const controls = new OrbitControls(
    camera,
    renderer.domElement,
  );

  controls.enableDamping = true;
  controls.dampingFactor = 0.04;
  controls.minDistance = MIN_DISTANCE;
  controls.maxDistance = MAX_DISTANCE;
  controls.zoomSpeed = 1.4;
  controls.enablePan = false;

  // * ═══════════════════════════════════════════════
  // * ULTRON COLOR SYSTEM
  // * ═══════════════════════════════════════════════
  const ultronBaseColor = new THREE.Color(0xff2020);

  // * These are only the initial creation colors.
  // * Runtime color switching uses ultronBaseColor + role.
  const C_BRIGHT = 0xff2020;
  const C_MID = 0xb80000;
  const C_DIM = 0x650000;
  const C_FAINT = 0x300000;
  const C_HOT = 0xffd8d8;

  const colorMaterials = new Map<
    THREE.Material,
    UltronColorRole
  >();

  function roleFromColor(
    color: number,
  ): UltronColorRole {
    if (color === C_BRIGHT) return "bright";
    if (color === C_MID) return "mid";
    if (color === C_DIM) return "dim";
    if (color === C_FAINT) return "faint";
    return "hot";
  }

  function colorForRole(
    base: THREE.Color,
    role: UltronColorRole,
  ): THREE.Color {
    const color = base.clone();

    switch (role) {
      case "bright":
        color.offsetHSL(0, 0.02, 0.20);
        break;

      case "mid":
        color.offsetHSL(0, 0.02, 0.05);
        break;

      case "dim":
        color.offsetHSL(0, 0, -0.12);
        break;

      case "faint":
        color.offsetHSL(0, 0, -0.25);
        break;

      case "hot":
        // * Keep the central energy almost white while retaining
        // * a slight tint from the selected ULTRON color.
        color.offsetHSL(0, -0.05, 0.38);
        break;
    }

    return color;
  }

  function registerColorMaterial(
    material: THREE.Material,
    role: UltronColorRole,
  ): void {
    colorMaterials.set(material, role);
  }

  function lineMat(
    color: number,
    opacity = 1,
  ): THREE.LineBasicMaterial {
    const material = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    registerColorMaterial(
      material,
      roleFromColor(color),
    );

    return material;
  }

  function basicGlowMat(
    color: number,
    opacity: number,
  ): THREE.MeshBasicMaterial {
    const material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    registerColorMaterial(
      material,
      roleFromColor(color),
    );

    return material;
  }

  // * ═══════════════════════════════════════════════
  // * ORB ROOT
  // * ═══════════════════════════════════════════════
  const orbGroup = new THREE.Group();
  scene.add(orbGroup);

  // * ═══════════════════════════════════════════════
  // * GEOMETRY HELPERS
  // * ═══════════════════════════════════════════════
  function latRing(
    radius: number,
    lat: number,
    segs = 120,
  ): THREE.BufferGeometry {
    const r = radius * Math.cos(lat);
    const y = radius * Math.sin(lat);
    const pts: THREE.Vector3[] = [];

    for (let i = 0; i <= segs; i++) {
      const a =
        (i / segs) *
        Math.PI *
        2;

      pts.push(
        new THREE.Vector3(
          r * Math.cos(a),
          y,
          r * Math.sin(a),
        ),
      );
    }

    return new THREE.BufferGeometry()
      .setFromPoints(pts);
  }

  function meridian(
    radius: number,
    lon: number,
    segs = 120,
  ): THREE.BufferGeometry {
    const pts: THREE.Vector3[] = [];

    for (let i = 0; i <= segs; i++) {
      const lat =
        (i / segs) *
        Math.PI -
        Math.PI / 2;

      pts.push(
        new THREE.Vector3(
          radius *
            Math.cos(lat) *
            Math.cos(lon),
          radius * Math.sin(lat),
          radius *
            Math.cos(lat) *
            Math.sin(lon),
        ),
      );
    }

    return new THREE.BufferGeometry()
      .setFromPoints(pts);
  }

  // * ═══════════════════════════════════════════════
  // * LAYER 1 — OUTER ULTRON SHELL
  // * ═══════════════════════════════════════════════
  const outerShell = new THREE.Group();
  const R1 = 2.0;

  for (let i = -15; i <= 15; i++) {
    const lat =
      (i / 15) *
      (Math.PI / 2) *
      0.95;

    const opacity =
      i % 3 === 0
        ? 0.5
        : 0.12;

    const color =
      i % 3 === 0
        ? C_MID
        : C_FAINT;

    outerShell.add(
      new THREE.Line(
        latRing(R1, lat),
        lineMat(color, opacity),
      ),
    );
  }

  for (let i = 0; i < 24; i++) {
    const lon =
      (i / 24) *
      Math.PI *
      2;

    const isMajor =
      i % 6 === 0;

    outerShell.add(
      new THREE.Line(
        meridian(R1, lon),
        lineMat(
          isMajor
            ? C_MID
            : C_FAINT,
          isMajor
            ? 0.6
            : 0.1,
        ),
      ),
    );
  }

  // * Four broad ULTRON cross-energy bands.
  const CROSS_LINES = 18;
  const CROSS_SPREAD = 0.25;

  for (let i = 0; i < 4; i++) {
    const lon =
      (i / 4) *
      Math.PI *
      2;

    for (
      let j = 0;
      j < CROSS_LINES;
      j++
    ) {
      const t =
        (j /
          (CROSS_LINES - 1)) *
          2 -
        1;

      const offset =
        (t * CROSS_SPREAD) /
        2;

      const falloff =
        1 -
        Math.abs(t) *
          0.7;

      const opacity =
        0.85 * falloff;

      const color =
        Math.abs(t) < 0.3
          ? C_BRIGHT
          : C_MID;

      outerShell.add(
        new THREE.Line(
          meridian(
            R1,
            lon + offset,
            200,
          ),
          lineMat(
            color,
            opacity,
          ),
        ),
      );
    }
  }

  // * Bright equator band.
  const EQ_LINES = 20;
  const EQ_SPREAD = 0.35;

  for (
    let j = 0;
    j < EQ_LINES;
    j++
  ) {
    const t =
      (j /
        (EQ_LINES - 1)) *
        2 -
      1;

    const offset =
      (t * EQ_SPREAD) /
      2;

    const falloff =
      1 -
      Math.abs(t) *
        0.65;

    const opacity =
      0.8 * falloff;

    const color =
      Math.abs(t) < 0.3
        ? C_BRIGHT
        : C_MID;

    outerShell.add(
      new THREE.Line(
        latRing(
          R1,
          offset,
          200,
        ),
        lineMat(
          color,
          opacity,
        ),
      ),
    );
  }

  orbGroup.add(outerShell);

  // * ═══════════════════════════════════════════════
  // * LAYER 2 — GRID PANELS
  // * ═══════════════════════════════════════════════
  const panelGroup = new THREE.Group();

  function createSpherePanel(
    latCenter: number,
    lonCenter: number,
    latSpan: number,
    lonSpan: number,
    radius: number,
    divisions = 4,
  ): THREE.Group {
    const group = new THREE.Group();
    const mat = lineMat(
      C_DIM,
      0.25,
    );

    for (
      let i = 0;
      i <= divisions;
      i++
    ) {
      const lat =
        latCenter -
        latSpan / 2 +
        (i / divisions) *
          latSpan;

      const pts: THREE.Vector3[] =
        [];

      for (
        let j = 0;
        j <= divisions * 4;
        j++
      ) {
        const lon =
          lonCenter -
          lonSpan / 2 +
          (j /
            (divisions * 4)) *
            lonSpan;

        pts.push(
          new THREE.Vector3(
            radius *
              Math.cos(lat) *
              Math.cos(lon),
            radius *
              Math.sin(lat),
            radius *
              Math.cos(lat) *
              Math.sin(lon),
          ),
        );
      }

      group.add(
        new THREE.Line(
          new THREE.BufferGeometry()
            .setFromPoints(pts),
          mat,
        ),
      );
    }

    for (
      let j = 0;
      j <= divisions;
      j++
    ) {
      const lon =
        lonCenter -
        lonSpan / 2 +
        (j / divisions) *
          lonSpan;

      const pts: THREE.Vector3[] =
        [];

      for (
        let i = 0;
        i <= divisions * 4;
        i++
      ) {
        const lat =
          latCenter -
          latSpan / 2 +
          (i /
            (divisions * 4)) *
            latSpan;

        pts.push(
          new THREE.Vector3(
            radius *
              Math.cos(lat) *
              Math.cos(lon),
            radius *
              Math.sin(lat),
            radius *
              Math.cos(lat) *
              Math.sin(lon),
          ),
        );
      }

      group.add(
        new THREE.Line(
          new THREE.BufferGeometry()
            .setFromPoints(pts),
          mat,
        ),
      );
    }

    return group;
  }

  for (let i = 0; i < 30; i++) {
    const lat =
      (Math.random() - 0.5) *
      Math.PI *
      0.8;

    const lon =
      Math.random() *
      Math.PI *
      2;

    const size =
      0.15 +
      Math.random() *
        0.25;

    panelGroup.add(
      createSpherePanel(
        lat,
        lon,
        size,
        size,
        R1 + 0.01,
        3 +
          Math.floor(
            Math.random() * 3,
          ),
      ),
    );
  }

  orbGroup.add(panelGroup);

  // * ═══════════════════════════════════════════════
  // * LAYER 3 — SECONDARY SHELL / ARCS
  // * ═══════════════════════════════════════════════
  const shell2 = new THREE.Group();
  const R2 = 2.12;

  for (let i = 0; i < 16; i++) {
    const lat =
      (Math.random() - 0.5) *
      Math.PI *
      0.85;

    const startLon =
      Math.random() *
      Math.PI *
      2;

    const arcLen =
      0.3 +
      Math.random() *
        1.2;

    const pts: THREE.Vector3[] =
      [];

    const segs = 60;
    const r =
      R2 *
      Math.cos(lat);

    const y =
      R2 *
      Math.sin(lat);

    for (
      let j = 0;
      j <= segs;
      j++
    ) {
      const a =
        startLon +
        (j / segs) *
          arcLen;

      pts.push(
        new THREE.Vector3(
          r * Math.cos(a),
          y,
          r * Math.sin(a),
        ),
      );
    }

    shell2.add(
      new THREE.Line(
        new THREE.BufferGeometry()
          .setFromPoints(pts),
        lineMat(
          C_MID,
          0.2 +
            Math.random() *
              0.3,
        ),
      ),
    );
  }

  for (let i = 0; i < 12; i++) {
    const lon =
      Math.random() *
      Math.PI *
      2;

    const startLat =
      (Math.random() - 0.5) *
      Math.PI *
      0.8;

    const arcLen =
      0.3 +
      Math.random() *
        0.8;

    const pts: THREE.Vector3[] =
      [];

    const segs = 40;

    for (
      let j = 0;
      j <= segs;
      j++
    ) {
      const lat =
        startLat +
        (j / segs) *
          arcLen;

      pts.push(
        new THREE.Vector3(
          R2 *
            Math.cos(lat) *
            Math.cos(lon),
          R2 *
            Math.sin(lat),
          R2 *
            Math.cos(lat) *
            Math.sin(lon),
        ),
      );
    }

    shell2.add(
      new THREE.Line(
        new THREE.BufferGeometry()
          .setFromPoints(pts),
        lineMat(
          C_DIM,
          0.15 +
            Math.random() *
              0.2,
        ),
      ),
    );
  }

  orbGroup.add(shell2);

  // * ═══════════════════════════════════════════════
  // * LAYER 4 — INNER CORE
  // * ═══════════════════════════════════════════════
  const innerCore = new THREE.Group();
  const R3 = 0.9;

  for (let s = 0; s < 8; s++) {
    const pts: THREE.Vector3[] =
      [];

    const turns =
      3 +
      Math.random() *
        2;

    const segs = 300;

    const phase =
      (s / 8) *
      Math.PI *
      2;

    for (
      let i = 0;
      i <= segs;
      i++
    ) {
      const t =
        i / segs;

      const lat =
        t * Math.PI -
        Math.PI / 2;

      const lon =
        t *
          turns *
          Math.PI *
          2 +
        phase;

      pts.push(
        new THREE.Vector3(
          R3 *
            Math.cos(lat) *
            Math.cos(lon),
          R3 *
            Math.sin(lat),
          R3 *
            Math.cos(lat) *
            Math.sin(lon),
        ),
      );
    }

    innerCore.add(
      new THREE.Line(
        new THREE.BufferGeometry()
          .setFromPoints(pts),
        lineMat(
          C_BRIGHT,
          0.3 +
            Math.random() *
              0.2,
        ),
      ),
    );
  }

  for (let i = -6; i <= 6; i++) {
    const lat =
      (i / 6) *
      (Math.PI / 2) *
      0.9;

    innerCore.add(
      new THREE.Line(
        latRing(
          R3,
          lat,
          80,
        ),
        lineMat(
          C_DIM,
          0.2,
        ),
      ),
    );
  }

  for (let i = 0; i < 12; i++) {
    const lon =
      (i / 12) *
      Math.PI *
      2;

    innerCore.add(
      new THREE.Line(
        meridian(
          R3,
          lon,
          80,
        ),
        lineMat(
          C_DIM,
          0.15,
        ),
      ),
    );
  }

  orbGroup.add(innerCore);

  // * ═══════════════════════════════════════════════
  // * LAYER 5 — HOT CENTRAL CORE
  // * ═══════════════════════════════════════════════
  const coreR = 0.25;

  const icoGeo =
    new THREE.IcosahedronGeometry(
      coreR,
      1,
    );

  const icoEdges =
    new THREE.EdgesGeometry(
      icoGeo,
    );

  const icoWireMat =
    lineMat(
      C_HOT,
      0.9,
    );

  const icoWire =
    new THREE.LineSegments(
      icoEdges,
      icoWireMat,
    );

  orbGroup.add(icoWire);

  const coreSphereMat =
    basicGlowMat(
      C_HOT,
      0.15,
    );

  const coreSphere =
    new THREE.Mesh(
      new THREE.SphereGeometry(
        0.15,
        16,
        16,
      ),
      coreSphereMat,
    );

  orbGroup.add(coreSphere);

  const glowSphereMat =
    basicGlowMat(
      C_MID,
      0.04,
    );

  const glowSphere =
    new THREE.Mesh(
      new THREE.SphereGeometry(
        0.5,
        16,
        16,
      ),
      glowSphereMat,
    );

  orbGroup.add(glowSphere);

  // * ═══════════════════════════════════════════════
  // * ULTRON ENERGY ORBITALS
  // * ═══════════════════════════════════════════════
  const energyOrbitals: THREE.Line[] =
    [];

  function createEnergyOrbital(
    radius: number,
    tiltX: number,
    tiltZ: number,
    opacity: number,
  ): void {
    const pts: THREE.Vector3[] =
      [];

    const segments = 180;

    for (
      let i = 0;
      i <= segments;
      i++
    ) {
      const a =
        (i / segments) *
        Math.PI *
        2;

      const x =
        radius *
        Math.cos(a);

      const y =
        Math.sin(a * 3) *
        0.08;

      const z =
        radius *
        Math.sin(a);

      pts.push(
        new THREE.Vector3(
          x,
          y,
          z,
        ),
      );
    }

    const line =
      new THREE.Line(
        new THREE.BufferGeometry()
          .setFromPoints(pts),
        lineMat(
          C_BRIGHT,
          opacity,
        ),
      );

    line.rotation.x = tiltX;
    line.rotation.z = tiltZ;

    energyOrbitals.push(line);
    orbGroup.add(line);
  }

  createEnergyOrbital(
    2.35,
    0.15,
    0.0,
    0.22,
  );

  createEnergyOrbital(
    2.55,
    -0.35,
    0.45,
    0.16,
  );

  createEnergyOrbital(
    2.75,
    0.55,
    -0.30,
    0.13,
  );

  createEnergyOrbital(
    3.05,
    -0.15,
    0.75,
    0.10,
  );

  createEnergyOrbital(
    3.35,
    0.30,
    -0.65,
    0.08,
  );

  // * ═══════════════════════════════════════════════
  // * CENTRAL ENERGY BEAM
  // * ═══════════════════════════════════════════════
  const beamGeometry =
    new THREE.CylinderGeometry(
      0.018,
      0.018,
      5.2,
      12,
      1,
      true,
    );

  const beamMaterial =
    basicGlowMat(
      C_BRIGHT,
      0.18,
    );

  const energyBeam =
    new THREE.Mesh(
      beamGeometry,
      beamMaterial,
    );

  orbGroup.add(energyBeam);

  // * ═══════════════════════════════════════════════
  // * CODE TEXT
  // * ═══════════════════════════════════════════════
  const codeSnippets = [
    "sys.init()",
    "0xFF3A",
    "malloc()",
    ">> SCAN",
    "void*",
    "ACK",
    "SYNC OK",
    "ptr_ref",
    "exec()",
    "hash256",
    "::bind",
    "core.0",
    "01101001",
    "10110100",
    ">>> RDY",
    "HEAP 4K",
    "TCP/SYN",
    "mutex.lk",
    "IRQ 0x7",
    "DMA xfer",
    "REG EAX",
    "FAULT 0",
    "kernel.d",
    "pipe |>",
    "chmod +x",
    "fork()",
    "SIGTERM",
    "eth0: UP",
    "AES-256",
    "RSA 4096",
    "TLS 1.3",
    "HTTP/2",
    "latency",
    "200 OK",
    "PATCH /",
    "fn main",
    "use std",
    "impl Orb",
    "async {}",
    "spawn()",
    "arc::new",
    ".unwrap",
  ];

  function makeTextSprite(
    text: string,
    size = 0.08,
  ): THREE.Sprite {
    const canvas =
      document.createElement(
        "canvas",
      );

    canvas.width = 256;
    canvas.height = 32;

    const ctx =
      canvas.getContext("2d")!;

    ctx.font =
      "bold 14px Courier New";

    // * White texture + SpriteMaterial color allows
    // * the complete text field to follow ULTRON color.
    ctx.fillStyle =
      "rgba(255,255,255,0.85)";

    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    ctx.fillText(
      text,
      128,
      16,
    );

    const texture =
      new THREE.CanvasTexture(
        canvas,
      );

    texture.minFilter =
      THREE.LinearFilter;

    const material =
      new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity:
          0.35 +
          Math.random() *
            0.55,
        blending:
          THREE.AdditiveBlending,
        depthWrite: false,
        color:
          colorForRole(
            ultronBaseColor,
            "bright",
          ),
      });

    registerColorMaterial(
      material,
      "bright",
    );

    const sprite =
      new THREE.Sprite(
        material,
      );

    sprite.scale.set(
      size * 5,
      size * 0.7,
      1,
    );

    return sprite;
  }

  function scatterText(
    count: number,
    sizeFn: () => number,
    rFn: () => number,
    speedScale: [number, number],
  ): THREE.Group {
    const group =
      new THREE.Group();

    for (
      let i = 0;
      i < count;
      i++
    ) {
      const sprite =
        makeTextSprite(
          codeSnippets[
            Math.floor(
              Math.random() *
                codeSnippets.length,
            )
          ],
          sizeFn(),
        );

      const phi =
        Math.acos(
          2 * Math.random() -
            1,
        );

      const theta =
        Math.random() *
        Math.PI *
        2;

      const r = rFn();

      sprite.position.set(
        r *
          Math.sin(phi) *
          Math.cos(theta),
        r * Math.cos(phi),
        r *
          Math.sin(phi) *
          Math.sin(theta),
      );

      sprite.userData = {
        phi,
        theta,
        r,
        speed:
          (speedScale[0] +
            Math.random() *
              speedScale[1]) *
          (Math.random() > 0.5
            ? 1
            : -1),
      } satisfies SpriteDrift;

      group.add(sprite);
    }

    return group;
  }

  const textOuter =
    scatterText(
      1200,
      () =>
        0.04 +
        Math.random() *
          0.04,
      () =>
        R1 +
        0.03 +
        Math.random() *
          0.08,
      [0.0002, 0.0008],
    );

  orbGroup.add(textOuter);

  const textInner =
    scatterText(
      100,
      () =>
        0.03 +
        Math.random() *
          0.03,
      () =>
        R3 + 0.02,
      [0.0005, 0.001],
    );

  orbGroup.add(textInner);

  const textAmbient =
    scatterText(
      400,
      () => 0.03,
      () =>
        R3 +
        0.2 +
        Math.random() *
          (R1 -
            R3 -
            0.3),
      [0.0003, 0.0006],
    );

  orbGroup.add(textAmbient);

  // * ═══════════════════════════════════════════════
  // * ORBITING DEBRIS / TECH FRAGMENTS
  // * ═══════════════════════════════════════════════
  const debrisGeos = [
    new THREE.IcosahedronGeometry(
      0.012,
      0,
    ),
    new THREE.IcosahedronGeometry(
      0.02,
      0,
    ),
    new THREE.IcosahedronGeometry(
      0.03,
      1,
    ),
    new THREE.IcosahedronGeometry(
      0.008,
      0,
    ),
    new THREE.TetrahedronGeometry(
      0.015,
      0,
    ),
    new THREE.OctahedronGeometry(
      0.018,
      0,
    ),
  ];

  const debris: THREE.Mesh[] =
    [];

  for (
    let i = 0;
    i < 250;
    i++
  ) {
    const geo =
      debrisGeos[
        Math.floor(
          Math.random() *
            debrisGeos.length,
        )
      ];

    const role =
      Math.random() > 0.7
        ? "bright"
        : "mid";

    const material =
      basicGlowMat(
        colorForRole(
          ultronBaseColor,
          role,
        ).getHex(),
        0.3 +
          Math.random() *
            0.6,
      );

    registerColorMaterial(
      material,
      role,
    );

    const mesh =
      new THREE.Mesh(
        geo,
        material,
      );

    const orbitR =
      1.2 +
      Math.random() *
        4.0;

    const speed =
      (0.08 +
        Math.random() *
          0.6) *
      (Math.random() > 0.5
        ? 1
        : -1);

    const tiltX =
      (Math.random() - 0.5) *
      Math.PI *
      0.9;

    const tiltZ =
      (Math.random() - 0.5) *
      Math.PI *
      0.5;

    const phase =
      Math.random() *
      Math.PI *
      2;

    mesh.userData = {
      orbitR,
      speed,
      tiltX,
      tiltZ,
      phase,
    } satisfies DebrisOrbit;

    debris.push(mesh);
    orbGroup.add(mesh);

    // * Some fragments get a subtle energy trail.
    if (Math.random() > 0.85) {
      const trailPts: THREE.Vector3[] =
        [];

      for (
        let j = 0;
        j <= 15;
        j++
      ) {
        const a =
          -(j / 15) *
          0.3;

        trailPts.push(
          new THREE.Vector3(
            orbitR *
              Math.cos(
                a + phase,
              ),
            orbitR *
              0.08 *
              Math.sin(
                a * 3,
              ),
            orbitR *
              Math.sin(
                a + phase,
              ),
          ),
        );
      }

      const trail =
        new THREE.Line(
          new THREE.BufferGeometry()
            .setFromPoints(
              trailPts,
            ),
          lineMat(
            C_FAINT,
            0.08,
          ),
        );

      mesh.add(trail);
    }
  }

  // * ═══════════════════════════════════════════════
  // * DUST PARTICLES
  // * ═══════════════════════════════════════════════
  const dustCount = 2000;
  const dustPos =
    new Float32Array(
      dustCount * 3,
    );

  for (
    let i = 0;
    i < dustCount;
    i++
  ) {
    const rr =
      0.5 +
      Math.pow(
        Math.random(),
        0.6,
      ) *
        7;

    const theta =
      Math.random() *
      Math.PI *
      2;

    const phi =
      Math.acos(
        2 * Math.random() -
          1,
      );

    dustPos[i * 3] =
      rr *
      Math.sin(phi) *
      Math.cos(theta);

    dustPos[i * 3 + 1] =
      rr *
      Math.cos(phi);

    dustPos[i * 3 + 2] =
      rr *
      Math.sin(phi) *
      Math.sin(theta);
  }

  const dustGeo =
    new THREE.BufferGeometry();

  dustGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(
      dustPos,
      3,
    ),
  );

  const dotCanvas =
    document.createElement(
      "canvas",
    );

  dotCanvas.width =
    dotCanvas.height = 64;

  const dotCtx =
    dotCanvas.getContext("2d")!;

  const dotGradient =
    dotCtx.createRadialGradient(
      32,
      32,
      0,
      32,
      32,
      32,
    );

  dotGradient.addColorStop(
    0,
    "rgba(255,255,255,1)",
  );

  dotGradient.addColorStop(
    0.2,
    "rgba(255,255,255,0.6)",
  );

  dotGradient.addColorStop(
    0.5,
    "rgba(255,255,255,0.15)",
  );

  dotGradient.addColorStop(
    1,
    "rgba(255,255,255,0)",
  );

  dotCtx.fillStyle =
    dotGradient;

  dotCtx.fillRect(
    0,
    0,
    64,
    64,
  );

  const dustMat =
    new THREE.PointsMaterial({
      map: new THREE.CanvasTexture(
        dotCanvas,
      ),
      size: 0.04,
      transparent: true,
      opacity: 0.5,
      blending:
        THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
      color:
        colorForRole(
          ultronBaseColor,
          "bright",
        ),
    });

  registerColorMaterial(
    dustMat,
    "bright",
  );

  const dustPoints =
    new THREE.Points(
      dustGeo,
      dustMat,
    );

  orbGroup.add(dustPoints);

  // * ═══════════════════════════════════════════════
  // * SCANNING RINGS
  // * ═══════════════════════════════════════════════
  function makeScanRing(
    radius: number,
    thickness = 0.015,
  ): THREE.Mesh {
    const geo =
      new THREE.RingGeometry(
        radius - thickness,
        radius + thickness,
        120,
      );

    const material =
      basicGlowMat(
        C_BRIGHT,
        0,
      );

    const mesh =
      new THREE.Mesh(
        geo,
        material,
      );

    mesh.rotation.x =
      Math.PI / 2;

    return mesh;
  }

  const scanRing1 =
    makeScanRing(
      R1,
      0.01,
    );

  const scanRing2 =
    makeScanRing(
      R1 * 0.7,
      0.008,
    );

  orbGroup.add(
    scanRing1,
    scanRing2,
  );

  // * ═══════════════════════════════════════════════
  // * HEXAGONAL NODES
  // * ═══════════════════════════════════════════════
  for (let i = 0; i < 15; i++) {
    const phi =
      Math.acos(
        2 * Math.random() -
          1,
      );

    const theta =
      Math.random() *
      Math.PI *
      2;

    const r =
      R1 + 0.02;

    const hexGeo =
      new THREE.CircleGeometry(
        0.03 +
          Math.random() *
            0.02,
        6,
      );

    const hexEdges =
      new THREE.EdgesGeometry(
        hexGeo,
      );

    const hex =
      new THREE.LineSegments(
        hexEdges,
        lineMat(
          C_MID,
          0.5,
        ),
      );

    hex.position.set(
      r *
        Math.sin(phi) *
        Math.cos(theta),
      r * Math.cos(phi),
      r *
        Math.sin(phi) *
        Math.sin(theta),
    );

    hex.lookAt(0, 0, 0);

    outerShell.add(hex);
  }

  // * ═══════════════════════════════════════════════
  // * ENERGY ARCS
  // * ═══════════════════════════════════════════════
  const energyArcs: THREE.Line[] =
    [];

  function createEnergyArc(
    radius: number,
    start: number,
    length: number,
    y: number,
    opacity: number,
  ): void {
    const pts: THREE.Vector3[] =
      [];

    const segments = 80;

    for (
      let i = 0;
      i <= segments;
      i++
    ) {
      const a =
        start +
        (i / segments) *
          length;

      const wave =
        Math.sin(
          i * 0.65,
        ) *
        0.018;

      pts.push(
        new THREE.Vector3(
          (radius + wave) *
            Math.cos(a),
          y +
            Math.sin(
              i * 0.45,
            ) *
              0.025,
          (radius + wave) *
            Math.sin(a),
        ),
      );
    }

    const arc =
      new THREE.Line(
        new THREE.BufferGeometry()
          .setFromPoints(pts),
        lineMat(
          C_BRIGHT,
          opacity,
        ),
      );

    energyArcs.push(arc);
    orbGroup.add(arc);
  }

  for (let i = 0; i < 10; i++) {
    createEnergyArc(
      2.05 +
        Math.random() *
          0.9,
      Math.random() *
        Math.PI *
        2,
      0.45 +
        Math.random() *
          1.0,
      (Math.random() -
        0.5) *
        2.2,
      0.08 +
        Math.random() *
          0.16,
    );
  }

  // * ═══════════════════════════════════════════════
  // * COLOR CONTROL
  // * ═══════════════════════════════════════════════
  function setUltronColor(
    color: string | number,
  ): void {
    ultronBaseColor.set(
      color,
    );

    colorMaterials.forEach(
      (role, material) => {
        const materialColor =
          (
            material as THREE.Material & {
              color?: THREE.Color;
            }
          ).color;

        if (materialColor) {
          materialColor.copy(
            colorForRole(
              ultronBaseColor,
              role,
            ),
          );
        }
      },
    );

    chromaticPass.uniforms.uColor.value =
      ultronBaseColor.clone();
  }

  // * Apply the default red ULTRON palette.
  setUltronColor(
    0xff2020,
  );

  // * ═══════════════════════════════════════════════
  // * GESTURE / PROGRAMMATIC CAMERA CONTROL
  // * ═══════════════════════════════════════════════
  const sphericalScratch =
    new THREE.Spherical();

  const offsetScratch =
    new THREE.Vector3();

  function rotateBy(
    deltaTheta: number,
    deltaPhi: number,
  ): void {
    offsetScratch
      .copy(camera.position)
      .sub(controls.target);

    sphericalScratch.setFromVector3(
      offsetScratch,
    );

    sphericalScratch.theta -=
      deltaTheta;

    sphericalScratch.phi =
      THREE.MathUtils.clamp(
        sphericalScratch.phi -
          deltaPhi,
        0.05,
        Math.PI - 0.05,
      );

    sphericalScratch.makeSafe();

    offsetScratch.setFromSpherical(
      sphericalScratch,
    );

    camera.position.copy(
      controls.target,
    ).add(
      offsetScratch,
    );

    camera.lookAt(
      controls.target,
    );
  }

  function zoomBy(
    factor: number,
  ): void {
    offsetScratch
      .copy(camera.position)
      .sub(controls.target);

    const dist =
      THREE.MathUtils.clamp(
        offsetScratch.length() *
          factor,
        MIN_DISTANCE,
        MAX_DISTANCE,
      );

    offsetScratch.setLength(
      dist,
    );

    camera.position.copy(
      controls.target,
    ).add(
      offsetScratch,
    );
  }

  function resetView(): void {
    camera.position.copy(
      HOME_POSITION,
    );

    controls.target.set(
      0,
      0,
      0,
    );

    camera.lookAt(
      controls.target,
    );

    controls.update();
  }

  // * ═══════════════════════════════════════════════
  // * ANIMATION
  // * ═══════════════════════════════════════════════
  const clock =
    new THREE.Clock();

  let flickerTimer = 0;
  let rafId = 0;
  let disposed = false;

  function animate(): void {
    if (disposed) return;

    rafId =
      requestAnimationFrame(
        animate,
      );

    const t =
      clock.getElapsedTime();

    // * Outer shell.
    outerShell.rotation.y +=
      0.0015;

    outerShell.rotation.x =
      Math.sin(
        t * 0.08,
      ) * 0.05;

    // * Surface panels.
    panelGroup.rotation.y +=
      0.0018;

    panelGroup.rotation.x =
      Math.sin(
        t * 0.08 + 0.5,
      ) * 0.04;

    // * Secondary shell.
    shell2.rotation.y -=
      0.001;

    shell2.rotation.z =
      Math.sin(
        t * 0.12,
      ) * 0.03;

    // * Energy orbitals.
    energyOrbitals.forEach(
      (
        orbital,
        index,
      ) => {
        orbital.rotation.y +=
          0.0015 +
          index * 0.00035;

        orbital.rotation.x +=
          Math.sin(
            t * 0.25 +
              index,
          ) *
          0.00008;
      },
    );

    // * Energy arcs slowly rotate around the system.
    energyArcs.forEach(
      (
        arc,
        index,
      ) => {
        arc.rotation.y +=
          0.0012 +
          index * 0.00012;

        const material =
          arc.material as THREE.LineBasicMaterial;

        material.opacity =
          (0.08 +
            Math.pow(
              Math.max(
                0,
                Math.sin(
                  t * 1.2 +
                    index,
                ),
              ),
              6,
            ) *
              0.20);
      },
    );

    // * Central beam pulse.
    const beamPulse =
      0.10 +
      Math.pow(
        Math.max(
          0,
          Math.sin(
            t * 1.7,
          ),
        ),
        5,
      ) *
        0.35;

    beamMaterial.opacity =
      beamPulse;

    const beamScale =
      0.7 +
      Math.sin(
        t * 2.0,
      ) *
        0.15;

    energyBeam.scale.x =
      beamScale;

    energyBeam.scale.z =
      beamScale;

    // * Inner core.
    innerCore.rotation.y -=
      0.005;

    innerCore.rotation.z +=
      0.002;

    innerCore.rotation.x =
      Math.cos(
        t * 0.1,
      ) * 0.08;

    // * Central wireframe.
    icoWire.rotation.x +=
      0.008;

    icoWire.rotation.y +=
      0.012;

    // * Core pulse.
    const wave1 =
      Math.sin(
        t * 1.2,
      );

    const wave3 =
      Math.pow(
        Math.max(
          0,
          Math.sin(
            t * 0.4,
          ),
        ),
        5,
      );

    const wave4 =
      Math.pow(
        Math.max(
          0,
          Math.sin(
            t * 0.7 + 2,
          ),
        ),
        8,
      );

    const fadeOut =
      Math.pow(
        Math.max(
          0,
          Math.sin(
            t * 0.25,
          ),
        ),
        3,
      );

    const surge =
      wave3 * 1.5 +
      wave4 * 2.0;

    const coreScale =
      1 +
      surge +
      Math.sin(
        t * 5,
      ) *
        0.05;

    coreSphere.scale.setScalar(
      coreScale,
    );

    const coreOpacity =
      Math.max(
        0,
        (
          0.08 +
          wave1 * 0.05 +
          surge * 0.2
        ) *
          (1 -
            fadeOut *
              0.95),
      );

    coreSphereMat.opacity =
      Math.min(
        0.6,
        coreOpacity,
      );

    glowSphere.scale.setScalar(
      1 +
        surge * 0.8,
    );

    glowSphereMat.opacity =
      Math.max(
        0,
        (
          0.03 +
          surge * 0.08
        ) *
          (1 -
            fadeOut *
              0.9),
      );

    icoWire.scale.setScalar(
      1 +
        surge * 0.6,
    );

    icoWireMat.opacity =
      Math.min(
        1,
        0.5 +
          surge * 0.4,
      );

    // * Orbiting debris.
    debris.forEach(
      (debrisMesh) => {
        const u =
          debrisMesh.userData as DebrisOrbit;

        const a =
          t * u.speed +
          u.phase;

        debrisMesh.position.set(
          u.orbitR *
            Math.cos(a) *
            Math.cos(
              u.tiltX,
            ),
          u.orbitR *
              Math.sin(
                u.tiltX,
              ) *
              Math.sin(
                a * 0.8,
              ) +
            Math.sin(
              a * 0.3 +
                u.tiltZ,
            ) *
              0.2,
          u.orbitR *
            Math.sin(a) *
            Math.cos(
              u.tiltZ,
            ),
        );

        debrisMesh.rotation.x +=
          0.015;

        debrisMesh.rotation.z +=
          0.01;
      },
    );

    // * Floating code drift.
    const driftGroups: [
      THREE.Group,
      number,
    ][] = [
      [textOuter, 1],
      [textInner, 2],
      [textAmbient, 1.2],
    ];

    for (const [
      group,
      multiplier,
    ] of driftGroups) {
      group.children.forEach(
        (child) => {
          const sprite =
            child as THREE.Sprite;

          const u =
            sprite.userData as SpriteDrift;

          u.theta +=
            u.speed *
            multiplier;

          sprite.position.set(
            u.r *
              Math.sin(
                u.phi,
              ) *
              Math.cos(
                u.theta,
              ),
            u.r *
              Math.cos(
                u.phi,
              ),
            u.r *
              Math.sin(
                u.phi,
              ) *
              Math.sin(
                u.theta,
              ),
          );
        },
      );
    }

    // * Scanning rings.
    const scanY1 =
      Math.sin(
        t * 0.4,
      ) * R1;

    scanRing1.position.y =
      scanY1;

    const scanS1 =
      Math.sqrt(
        Math.max(
          0,
          R1 * R1 -
            scanY1 *
              scanY1,
        ),
      ) / R1;

    scanRing1.scale.set(
      scanS1,
      scanS1,
      1,
    );

    (
      scanRing1.material as THREE.MeshBasicMaterial
    ).opacity =
      0.2 * scanS1;

    const scanY2 =
      Math.sin(
        t * 0.6 + 2,
      ) * R3;

    scanRing2.position.y =
      scanY2;

    const scanS2 =
      Math.sqrt(
        Math.max(
          0,
          R3 * R3 -
            scanY2 *
              scanY2,
        ),
      ) / R3;

    scanRing2.scale.set(
      scanS2,
      scanS2,
      1,
    );

    (
      scanRing2.material as THREE.MeshBasicMaterial
    ).opacity =
      0.15 * scanS2;

    // * Dust rotation.
    dustPoints.rotation.y +=
      0.0002;

    // * Random panel flicker.
    flickerTimer +=
      0.016;

    if (
      flickerTimer >
      0.1
    ) {
      flickerTimer = 0;

      panelGroup.children.forEach(
        (panel) => {
          if (
            Math.random() >
            0.95
          ) {
            panel.visible =
              !panel.visible;
          }
        },
      );
    }

    // * Bloom pulse.
    bloom.strength =
      1.6 +
      Math.sin(
        t * 0.8,
      ) *
        0.3;

    chromaticPass.uniforms.uTime.value =
      t;

    controls.update();
    composer.render();
  }

  animate();

  // * ═══════════════════════════════════════════════
  // * RESIZE
  // * ═══════════════════════════════════════════════
  function onResize(): void {
    const w =
      Math.max(
        1,
        container.clientWidth,
      );

    const h =
      Math.max(
        1,
        container.clientHeight,
      );

    camera.aspect =
      w / h;

    camera.updateProjectionMatrix();

    renderer.setSize(
      w,
      h,
    );

    composer.setSize(
      w,
      h,
    );
  }

  window.addEventListener(
    "resize",
    onResize,
  );

  // * ═══════════════════════════════════════════════
  // * CLEANUP
  // * ═══════════════════════════════════════════════
  function dispose(): void {
    disposed = true;

    cancelAnimationFrame(
      rafId,
    );

    window.removeEventListener(
      "resize",
      onResize,
    );

    controls.dispose();

    scene.traverse(
      (obj) => {
        const object =
          obj as THREE.Mesh;

        if (object.geometry) {
          object.geometry.dispose();
        }

        const materials =
          Array.isArray(
            object.material,
          )
            ? object.material
            : object.material
              ? [object.material]
              : [];

        for (
          const material of materials
        ) {
          const anyMaterial =
            material as THREE.Material & {
              map?: THREE.Texture;
              alphaMap?: THREE.Texture;
            };

          anyMaterial.map?.dispose();
          anyMaterial.alphaMap?.dispose();
          material.dispose();
        }
      },
    );

    composer.dispose();
    renderer.dispose();
    renderer.domElement.remove();
  }

  return {
    rotateBy,
    setUltronColor,
    zoomBy,
    zoomIn: () =>
      zoomBy(0.65),
    zoomOut: () =>
      zoomBy(1.55),
    resetView,
    dispose,
  };
}
