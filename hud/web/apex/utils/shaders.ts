export const HUMAN_VERTEX_SHADER = `
  attribute float aWeight;
  attribute float aKind;        // 0 front · 1 back shell · 3 boiler mote · 5 interior head dust
  attribute float aSize;        // dot scale (2 = coarse halo particles); patch scales with it
  attribute vec4 aBoil;         // (nx*amp, ny*amp, phase, rate) — outward normal length = amplitude
  attribute vec4 aBright;       // raw brightness per state (guard + role thresholds)
  attribute vec4 aBucket;       // palette bucket per state — ROLE derivation (vein/fire)
  attribute float aNx;          // revolve-normal x (head lighting; 0 = flat/unshaded)

  uniform float uYaw, uPitch, uBreathe, uBreathY, uBackK, uVein, uSize, uPixelRatio;
  uniform float uBoilT, uVeinT, uWaveT, uBoilAmp, uPivotY;
  uniform float uStateA, uStateB, uBloomR;   // blend: A everywhere, B inside the growing face halo
  uniform float uStrongMix, uEnergy, uRim;
  uniform float uEffectsOff;
  uniform float uAsmP;
  uniform vec2 uAttn;
  uniform vec4 uClick;          // x,y = click origin (rest space) · z = light strength · w = age s
  uniform vec3 uPalCyan, uPalPale;

  varying vec2 vUv;
  varying vec3 vTint;
  varying float vAlpha, vMixK, vFlat, vPatch;

  float rawOf(vec4 b, float s) {
    float base = s < 0.5 ? b.x : (s < 1.5 ? b.y : b.z);
    return s > 1.5 ? mix(b.z, b.w, uStrongMix) : base;
  }
  float bucketOf(vec4 u2, float s) {
    float base = s < 0.5 ? u2.x : (s < 1.5 ? u2.y : u2.z);
    return (s > 1.5 && uStrongMix > 0.5) ? u2.w : base;
  }

  void main() {
    vec3 p = position;
    float py = (1.0 - position.y) * 0.5;    // plate-space y (0 top .. 1 bottom)
    bool front = aKind < 0.5;
    bool back  = aKind > 0.5 && aKind < 1.5;
    bool boil  = aKind > 2.5 && aKind < 3.5;
    bool dust  = aKind > 4.5;

    // Tile address: this particle's REST location in the plate
    vUv = vec2((position.x + 1.0) * 0.5, (1.0 - position.y) * 0.5);

    // Tear cover: tiles on the turning head grow with the turn so stroke rows never gap
    float turnK = smoothstep(0.05, 0.45, abs(uYaw) + abs(uPitch)) * aWeight * (1.0 - uEffectsOff);
    float cover = 1.0 + turnK * 0.9;
    vPatch = aSize * cover;
    vTint = vec3(1.0);
    vAlpha = 1.0;
    vFlat = 0.0;

    // Flat spray sheet fades slightly at extreme turns
    if (front && abs(position.z) < 0.012 && aWeight > 0.25) {
      vAlpha *= 1.0 - turnK * 0.9;
    }

    // ── STATE BLEND MASK — rest-space radial from the face core (0.0, 0.14)
    float dFace = distance(position.xy, vec2(0.0, 0.14));
    vMixK = 1.0 - smoothstep(uBloomR - 0.52, uBloomR + 0.208, dFace);
    float bucketNow = vMixK < 0.5 ? bucketOf(aBucket, uStateA) : bucketOf(aBucket, uStateB);
    float rawNow = mix(rawOf(aBright, uStateA), rawOf(aBright, uStateB), vMixK);

    // Halo boundary subtle brighten ring
    if (uBloomR < 5.0 && uEffectsOff < 0.5) {
      float ringM = 1.0 - smoothstep(0.0, 0.30, abs(dFace - uBloomR));
      vTint *= 1.0 + 0.20 * ringM;
    }

    // ── EDGE BOIL — outward escape-and-return along silhouette normals
    if (boil) {
      if (uEffectsOff > 0.5) {
        vAlpha = 0.0;
      } else {
        float cyc = aBoil.z + uBoilT * aBoil.w;
        float exc = sin(3.14159265 * fract(cyc));
        vec2 nrm = aBoil.xy;
        vec2 tang = vec2(-nrm.y, nrm.x);
        float wob = sin(cyc * 25.7) * 0.18;
        p.xy += (nrm * exc + tang * (wob * exc)) * uBoilAmp;
        vAlpha = (0.14 + 0.52 * exc) * (1.0 - turnK * 0.55);
        vFlat = 1.0;
        vTint = (aBucket.x > 0.5 ? uPalPale : uPalCyan) * 0.78;
      }
    }
    if (dust) {
      vFlat = 1.0;
      vTint = (aBucket.x > 0.5 ? uPalPale : uPalCyan) * 0.12;
    }

    if (uEffectsOff < 0.5) {
      // ── Click / Shockwave residual matter lean
      vec2 toP = uClick.xy - position.xy;
      float dP = length(toP);
      if (uClick.z > 0.001) {
        p.xy += (toP / max(dP, 0.0001)) * uClick.z * exp(-dP * dP * 6.0) * 0.01;
      }

      // Whole-body subtle counter-lean
      float bodyYaw = uYaw * 0.09;
      float cb = cos(bodyYaw), sb = sin(bodyYaw);
      p = vec3(p.x * cb + p.z * sb, p.y, -p.x * sb + p.z * cb);

      // Head turnover about the silhouette-derived neck pivot
      if (aWeight > 0.001) {
        vec3 h = p - vec3(0.0, uPivotY, 0.04);
        float cy = cos(uYaw), sy = sin(uYaw);
        float cp = cos(uPitch), sp = sin(uPitch);
        vec3 r = vec3(h.x * cy + h.z * sy, h.y, -h.x * sy + h.z * cy);
        r = vec3(r.x, r.y * cp - r.z * sp, r.y * sp + r.z * cp);
        p += (r - h) * aWeight;
      }

      // BREATHING — chest expansion anchored low in the chest; head barely moves
      p.y += uBreathY * (1.0 - aWeight) * smoothstep(-1.0, -0.55, position.y);
      p *= uBreathe;

      // ── SPEAKING WAVE — 110-strip horizontal face contour wave
      float spkA = (uStateA > 1.5) ? 1.0 : 0.0;
      float spkB = (uStateB > 1.5) ? 1.0 : 0.0;
      float spkMix = mix(spkA, spkB, vMixK);
      if (spkMix > 0.001) {
        float band = exp(-pow((py - 0.43) / 0.155, 2.0));
        float wv = sin(uWaveT * 9.2 + py * 50.6) * sin(uWaveT * 3.7 + py * 20.9);
        p.x += wv * uEnergy * band * spkMix * 0.034;
      }

      // ── DERIVED ROLES — golden neck/chest filaments & core pulse
      if (front && bucketNow > 1.5) {
        if (py > 0.56 && rawNow > 0.33) {
          float yn = clamp((position.y + 1.0) * 0.62, 0.0, 1.0);
          float phv = yn + abs(position.x) * 0.35;
          float dW = abs(fract(phv - uVeinT + 0.5) - 0.5);
          float pulse = smoothstep(0.22, 0.0, dW);
          float near = 1.0 + 0.9 * (1.0 - smoothstep(0.0, 0.22, distance(p.xy, uAttn)));
          vTint *= uVein * (1.0 + 0.5 * pulse) * near;
        } else if (py <= 0.56) {
          vTint *= 0.95 + 0.09 * sin(6.2831853 * (uVeinT * 0.5 + position.y));
        }
      }

      // ── TURNED HEAD SHADING & SILHOUETTE RIM HIGHLIGHTS
      float effK = smoothstep(0.06, 0.30, abs(uYaw) + abs(uPitch) * 1.2) * aWeight;
      if (effK > 0.001 && !boil && !dust) {
        float nnx = aNx;
        float nnz = sqrt(max(0.0, 1.0 - nnx * nnx));
        if (back) nnz = -nnz;
        float sy2 = sin(uYaw), cy2 = cos(uYaw);
        float nvz = -nnx * sy2 + nnz * cy2;
        float facing = 0.08 + 0.92 * smoothstep(-0.05, 0.45, nvz);
        vTint *= mix(1.0, facing, effK);
        float rim = 1.0 - smoothstep(0.04, 0.30, abs(nvz));
        vTint *= 1.0 + rim * effK * uRim;
        float zn = clamp(p.z * 1.6, -1.0, 1.0);
        vTint *= mix(1.0, 0.72 + 0.28 * smoothstep(-0.6, 0.6, zn), effK);
      }

      // ── EXPANDING LIGHT PULSE / SHOCKWAVE ACROSS HUMANOID
      if (uClick.z > 0.001) {
        float wf = 1.0 - smoothstep(0.0, 0.34, abs(dP - 2.6 * uClick.w));
        float isVein = (front && bucketNow > 1.5 && py > 0.56) ? 1.0 : 0.0;
        vTint *= 1.0 + wf * uClick.z * mix(0.9, 2.4, isVein);
      }
    }

    // Occlusion gates for back shell and interior volume dust
    if (back) { vAlpha *= uBackK * (1.0 - uEffectsOff); vTint *= 0.5; }
    if (dust) vAlpha *= uBackK * (1.0 - uEffectsOff) * (0.55 + 0.45 * clamp(position.z + 0.5, 0.0, 1.0));

    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
    gl_PointSize = uSize * uPixelRatio * aSize * cover;
  }
`;

export const HUMAN_FRAGMENT_SHADER = `
  uniform sampler2D uTexA, uTexB, uTexS;
  uniform float uStrongA, uStrongB, uPulseA, uPulseB, uPatchUV, uDotSharp;
  varying vec2 vUv;
  varying vec3 vTint;
  varying float vAlpha, vMixK, vFlat, vPatch;

  void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    if (r > 0.5) discard;
    float aDot = smoothstep(0.5, uDotSharp, r);
    vec3 c;
    if (vFlat > 0.5) {
      c = vTint;
    } else {
      vec2 tile = vUv + (gl_PointCoord - vec2(0.5)) * (uPatchUV * vPatch);
      vec3 cA = mix(texture2D(uTexA, tile).rgb, texture2D(uTexS, tile).rgb, uStrongA) * uPulseA;
      vec3 cB = mix(texture2D(uTexB, tile).rgb, texture2D(uTexS, tile).rgb, uStrongB) * uPulseB;
      c = mix(cA, cB, vMixK) * vTint;
      if (max(c.r, max(c.g, c.b)) < 0.0025) discard;
    }
    float a = aDot * vAlpha;
    if (a < 0.004) discard;
    gl_FragColor = vec4(c, a);
    #include <colorspace_fragment>
  }
`;

export const CLUSTER_VERTEX_SHADER = `
  attribute vec2 aOff;
  attribute float aPh, aSp, aSz, aBr;
  uniform float uT, uStr, uSizeK, uPixelRatio;
  varying float vA;
  varying vec3 vC;

  void main() {
    float cyc = aPh * 0.159155 + uT * aSp * 0.22;
    float exc = sin(3.14159265 * fract(cyc));
    vec2 dir = aOff / max(length(aOff), 0.0005);
    vec2 tang = vec2(-dir.y, dir.x);
    float wob = sin(cyc * 25.7) * 0.18;
    float amp = 0.02 + 0.05 * fract(aPh * 7.0);
    vec2 pos2 = aOff + (dir * exc + tang * (wob * exc)) * amp;
    vec3 p = vec3(pos2, 0.0) + vec3(0.0, -0.88, 0.45);
    vA = uStr * (0.25 + 0.75 * exc) * (aBr > 0.5 ? 1.2 : 0.75);
    vC = aBr > 0.5 ? vec3(0.68, 0.96, 1.0) : vec3(0.0097, 0.724, 1.0);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
    gl_PointSize = max(1.0, aSz * uSizeK * uPixelRatio);
  }
`;

export const CLUSTER_FRAGMENT_SHADER = `
  varying float vA;
  varying vec3 vC;
  void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    if (r > 0.5) discard;
    gl_FragColor = vec4(vC * vA, 1.0);
    #include <colorspace_fragment>
  }
`;

export const BACKDROP_VERTEX_SHADER = `
  attribute vec2 aUv;
  attribute vec3 aCol;
  attribute float aPh, aRate, aBase, aTw, aSz;
  uniform float uT, uPixelRatio, uSizeK, uRest, uPulse;
  uniform vec4 uMap;                 // image-uv -> NDC: xy = scale, zw = offset
  uniform vec4 uWave;                // SHOCKWAVE: xy = origin (NDC), z = radius, w = strength
  uniform vec2 uWaveK;               // x = aspect (vw/vh), y = ring half-thickness
  varying vec3 vC;

  void main() {
    float tw = 0.5 + 0.5 * sin(uT * aRate + aPh * 6.2831853);
    float wander = step(0.75, aTw) * smoothstep(0.66, 1.0, tw) * uPulse;
    float breath = step(0.25, aTw) * (1.0 - step(0.75, aTw)) * (0.1 + 0.9 * tw) * 1.1;
    float pulse = wander + breath;
    float glow = aBase * (uRest + pulse);
    vC = min(aCol * (1.0 + 0.45 * smoothstep(0.5, 1.0, pulse)), vec3(1.0)) * glow;
    vec2 ndc = vec2(aUv.x * uMap.x + uMap.z, aUv.y * uMap.y + uMap.w);
    if (uWave.w > 0.001) {
      float wd = length(vec2((ndc.x - uWave.x) * uWaveK.x, ndc.y - uWave.y));
      float wf = 1.0 - smoothstep(0.0, uWaveK.y, abs(wd - uWave.z));
      vC *= 1.0 + wf * uWave.w * 3.2;
    }
    gl_Position = vec4(ndc, 0.0, 1.0);
    gl_PointSize = max(1.0, aSz * uSizeK * uPixelRatio * (1.0 + 0.35 * pulse));
  }
`;

export const BACKDROP_FRAGMENT_SHADER = `
  varying vec3 vC;
  void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    if (r > 0.5) discard;
    float a = smoothstep(0.5, 0.1, r);
    gl_FragColor = vec4(vC * a, 1.0);
    #include <colorspace_fragment>
  }
`;
