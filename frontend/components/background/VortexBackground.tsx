"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { prefersReducedMotion } from "@/lib/utils";
import { makeGlowTexture } from "@/lib/three/glowTexture";

/**
 * Global animated background: a slow, breathing 3D vortex rendered in the
 * attractor-plane in front of the camera.
 *
 * - Decorative only: pointer-events none, aria-hidden, mounted behind the app.
 * - Delta-time animation driven by THREE.Timer (no THREE.Clock, no frame counts).
 * - Device-aware particle counts and pixel ratio.
 * - Respects prefers-reduced-motion with a static, subtle frame.
 * - Falls back to a lightweight CSS gradient when WebGL is unavailable.
 * - Fully cleaned up on unmount (loop, listener, geometry, material, renderer).
 */

type Tier = "mobile" | "tablet" | "desktop";

interface TierConfig {
  total: number;
  emit: number;
  maxRadius: number;
  pixelRatio: number;
}

const TIER_CONFIG: Record<Tier, TierConfig> = {
  mobile: { total: 380, emit: 60, maxRadius: 6.0, pixelRatio: 1.5 },
  tablet: { total: 850, emit: 130, maxRadius: 8.0, pixelRatio: 1.75 },
  desktop: { total: 1500, emit: 220, maxRadius: 9.5, pixelRatio: 2 },
};

const TILT = 0.34;
const GROUP_SPIN = 0.035;
const INNER_GLOW = "#7c6aff";
const OUTER_GLOW = "#4bd8ff";

function getTier(): Tier {
  if (typeof window === "undefined") return "desktop";
  const w = window.innerWidth;
  if (w < 640) return "mobile";
  if (w < 1024) return "tablet";
  return "desktop";
}

/** Lightweight CSS fallback shown only when WebGL cannot be created. */
function CSSFallback() {
  return (
    <div
      role="presentation"
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <div
        className="absolute left-1/2 top-1/2 h-[42rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-40"
        style={{
          background:
            "conic-gradient(from 90deg at 50% 50%, rgba(124,106,255,0.14), rgba(75,216,255,0.06), rgba(124,106,255,0.18), rgba(124,106,255,0.05), rgba(124,106,255,0.14))",
          filter: "blur(60px)",
        }}
      />
    </div>
  );
}

export default function VortexBackground() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [webglFailed, setWebglFailed] = useState(false);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const reduced = prefersReducedMotion();
    const config = TIER_CONFIG[getTier()];

    // ---- Renderer ----
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: false,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setWebglFailed(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, config.pixelRatio));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    // ---- Scene & camera ----
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 13);
    camera.lookAt(0, 0, 0);

    const world = new THREE.Group();
    world.rotation.x = TILT;
    scene.add(world);

    // ---- Central glow ----
    const glowTex = makeGlowTexture();
    const glowMat = new THREE.SpriteMaterial({
      map: glowTex,
      color: INNER_GLOW,
      transparent: true,
      opacity: reduced ? 0.4 : 0.55,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const glow = new THREE.Sprite(glowMat);
    glow.scale.setScalar(9);
    world.add(glow);

    // ---- Structural rings (faint arcs of the vortex shell) ----
    const rings: THREE.Mesh[] = [];
    const ringDefs = [
      { r: 3.4, width: 0.05, opacity: 0.1, speed: 0.1, color: INNER_GLOW },
      { r: 5.6, width: 0.03, opacity: 0.06, speed: -0.06, color: OUTER_GLOW },
    ];
    ringDefs.forEach((def) => {
      const geo = new THREE.RingGeometry(def.r - def.width, def.r + def.width, 96);
      const mat = new THREE.MeshBasicMaterial({
        color: def.color,
        transparent: true,
        opacity: def.opacity,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      const mesh = new THREE.Mesh(geo, mat);
      world.add(mesh);
      rings.push(mesh);
    });

    // ---- Particle system (single draw call, shader-driven points) ----
    const N = config.total;
    const emitCount = config.emit;
    const spiralCount = N - emitCount;

    const positions = new Float32Array(N * 3);
    const colors = new Float32Array(N * 3);
    const sizes = new Float32Array(N);
    const alphas = new Float32Array(N);

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));
    geometry.setAttribute("aAlpha", new THREE.BufferAttribute(alphas, 1));

    const PALETTE = [
      new THREE.Color("#7c6aff"),
      new THREE.Color("#8b7cff"),
      new THREE.Color("#a78bfa"),
      new THREE.Color("#5b4dff"),
      new THREE.Color("#4bd8ff"),
      new THREE.Color("#ffffff"),
    ];

    const spiral = {
      angle: new Float32Array(spiralCount),
      radius: new Float32Array(spiralCount),
      angSpeed: new Float32Array(spiralCount),
      inwardSpeed: new Float32Array(spiralCount),
      depth: new Float32Array(spiralCount),
      shimmer: new Float32Array(spiralCount),
      baseAlpha: new Float32Array(spiralCount),
    };

    const maxR = config.maxRadius;

    for (let i = 0; i < spiralCount; i++) {
      const r0 = maxR * Math.sqrt(Math.random());
      spiral.angle[i] = Math.random() * Math.PI * 2;
      spiral.radius[i] = r0;
      spiral.angSpeed[i] = (0.16 + Math.random() * 0.5) * (Math.random() < 0.82 ? 1 : -1);
      spiral.inwardSpeed[i] = 0.35 + Math.random() * 0.4;
      spiral.depth[i] = (Math.random() - 0.5) * 1.4;
      spiral.shimmer[i] = Math.random() * Math.PI * 2;
      spiral.baseAlpha[i] = 0.4 + Math.random() * 0.5;

      positions[i * 3] = Math.cos(spiral.angle[i]) * r0;
      positions[i * 3 + 1] = Math.sin(spiral.angle[i]) * r0;
      positions[i * 3 + 2] = spiral.depth[i];

      const c = PALETTE[Math.floor(Math.random() * PALETTE.length)];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
      sizes[i] = reduced ? 0.4 : 0.28 + Math.random() * 0.75;
      alphas[i] = spiral.baseAlpha[i];
    }

    const emitState = {
      angle: new Float32Array(emitCount),
      radius: new Float32Array(emitCount),
      tangential: new Float32Array(emitCount),
      outward: new Float32Array(emitCount),
      sizeBase: new Float32Array(emitCount),
      nextTime: new Float32Array(emitCount),
      active: new Uint8Array(emitCount),
      baseAlpha: new Float32Array(emitCount),
    };

    for (let i = 0; i < emitCount; i++) {
      const j = spiralCount + i;
      const c = Math.random() < 0.7 ? PALETTE[0] : PALETTE[4];
      colors[j * 3] = c.r;
      colors[j * 3 + 1] = c.g;
      colors[j * 3 + 2] = c.b;
      emitState.sizeBase[i] = 0.6 + Math.random() * 0.8;
      emitState.baseAlpha[i] = 0.5 + Math.random() * 0.4;
      emitState.nextTime[i] = Math.random() * 4;
      positions[j * 3] = 0;
      positions[j * 3 + 1] = 0;
      positions[j * 3 + 2] = 0;
      sizes[j] = emitState.sizeBase[i];
      alphas[j] = 0;
    }

    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexShader: /* glsl */ `
        attribute float aSize;
        attribute float aAlpha;
        attribute vec3 aColor;
        uniform float uPixelRatio;
        varying float vAlpha;
        varying vec3 vColor;
        void main() {
          vColor = aColor;
          vAlpha = aAlpha;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * uPixelRatio * (180.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: /* glsl */ `
        varying float vAlpha;
        varying vec3 vColor;
        void main() {
          if (vAlpha <= 0.004) discard;
          vec2 uv = gl_PointCoord - vec2(0.5);
          float d = length(uv);
          float glow = smoothstep(0.5, 0.0, d);
          gl_FragColor = vec4(vColor * glow, glow * vAlpha);
        }
      `,
      uniforms: {
        uPixelRatio: { value: Math.min(window.devicePixelRatio, config.pixelRatio) },
      },
    });

    const points = new THREE.Points(geometry, material);
    world.add(points);

    // ---- Resize (rebuild when the device tier changes, else just scale) ----
    let currentTier = getTier();
    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();

      const tier = getTier();
      if (tier !== currentTier) {
        currentTier = tier;
        rebuild();
      }
    };
    window.addEventListener("resize", onResize);

    // Rebuild the particle system/camera for the new tier.
    function rebuild() {
      const next = TIER_CONFIG[currentTier];
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, next.pixelRatio));
      material.uniforms.uPixelRatio.value = Math.min(window.devicePixelRatio, next.pixelRatio);
      const scaleRatio = next.maxRadius / config.maxRadius;
      if (scaleRatio !== 1) {
        spiral.radius.forEach((_, idx) => {
          spiral.radius[idx] *= scaleRatio;
        });
        emitState.radius.forEach((_, idx) => {
          emitState.radius[idx] *= scaleRatio;
        });
      }
    }

    // ---- Animation loop (delta-time via THREE.Timer) ----
    let rafId = 0;
    let running = true;
    let simTime = 0;
    const timer = new THREE.Timer();

    const onContextLost = (e: Event) => {
      e.preventDefault();
      running = false;
      cancelAnimationFrame(rafId);
    };
    renderer.domElement.addEventListener("webglcontextlost", onContextLost);

    const tick = () => {
      if (!running) return;
      rafId = requestAnimationFrame(tick);
      timer.update();
      const dt = Math.min(timer.getDelta(), 0.05);
      simTime += dt;

      const spin = GROUP_SPIN * dt;
      world.rotation.z += spin;

      const alphaArr = geometry.attributes.aAlpha.array as Float32Array;
      const posArr = geometry.attributes.position.array as Float32Array;
      const sizeArr = geometry.attributes.aSize.array as Float32Array;

      // Spiral stream: orbit inward, recycle at the center.
      const s = spiral;
      for (let i = 0; i < spiralCount; i++) {
        let r = s.radius[i] - s.inwardSpeed[i] * dt;
        if (r <= 0.25) {
          r = maxR * Math.sqrt(Math.random());
          s.angle[i] = Math.random() * Math.PI * 2;
          s.depth[i] = (Math.random() - 0.5) * 1.4;
        }
        s.radius[i] = r;
        const a = s.angle[i] + (s.angSpeed[i] + GROUP_SPIN) * dt;
        s.angle[i] = a;
        const evolveArc = r / maxR;
        posArr[i * 3] = Math.cos(a) * r;
        posArr[i * 3 + 1] = Math.sin(a) * r;
        posArr[i * 3 + 2] = s.depth[i] + Math.sin(a * 2 + s.shimmer[i]) * 0.18;
        alphaArr[i] =
          s.baseAlpha[i] * (0.72 + 0.28 * Math.min(1, evolveArc)) *
          (0.8 + 0.2 * Math.sin(simTime * 0.8 + s.shimmer[i]));
      }

      // Emission stream: outward sparkles that fade at the rim.
      for (let i = 0; i < emitCount; i++) {
        const j = spiralCount + i;
        if (!emitState.active[i]) {
          if (simTime >= emitState.nextTime[i]) {
            emitState.active[i] = 1;
            emitState.radius[i] = 0.15;
            emitState.angle[i] = Math.random() * Math.PI * 2;
            posArr[j * 3] = Math.cos(emitState.angle[i]) * 0.15;
            posArr[j * 3 + 1] = Math.sin(emitState.angle[i]) * 0.15;
            posArr[j * 3 + 2] = 0;
          } else {
            alphaArr[j] = 0;
          }
          continue;
        }
        const r = emitState.radius[i] + emitState.outward[i] * dt;
        const a = emitState.angle[i] + emitState.tangential[i] * dt;
        emitState.angle[i] = a;
        if (r >= maxR) {
          emitState.active[i] = 0;
          emitState.radius[i] = 0;
          emitState.outward[i] = 0.22 + Math.random() * 0.28;
          emitState.tangential[i] = (Math.random() < 0.5 ? -1 : 1) * (0.14 + Math.random() * 0.4);
          emitState.nextTime[i] = simTime + 4 + Math.random() * 6;
          alphaArr[j] = 0;
          continue;
        }
        emitState.radius[i] = r;
        const progress = r / maxR;
        posArr[j * 3] = Math.cos(a) * r;
        posArr[j * 3 + 1] = Math.sin(a) * r;
        posArr[j * 3 + 2] = 0;
        alphaArr[j] = emitState.baseAlpha[i] * Math.pow(1 - progress, 0.55);
        sizeArr[j] = emitState.sizeBase[i] * (1 - progress * 0.45);
      }

      geometry.attributes.position.needsUpdate = true;
      geometry.attributes.aAlpha.needsUpdate = true;
      geometry.attributes.aSize.needsUpdate = true;

      // Breathing glow + ring drift.
      const breath = 0.5 + 0.5 * Math.sin(simTime * 0.7);
      glow.scale.setScalar(8.6 + breath * 1.1);
      glowMat.opacity = reduced ? 0.4 : 0.42 + 0.12 * breath;
      rings.forEach((ring, i) => {
        ring.rotation.z += ringDefs[i].speed * dt;
      });

      renderer.render(scene, camera);
    };

    if (reduced) {
      // Static frame: paint once, no animation loop.
      world.rotation.z = 0.4;
      glow.scale.setScalar(9);
      geometry.attributes.position.needsUpdate = true;
      geometry.attributes.aAlpha.needsUpdate = true;
      geometry.attributes.aSize.needsUpdate = true;
      renderer.render(scene, camera);
    } else {
      tick();
    }

    // ---- Cleanup ----
    return () => {
      running = false;
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", onResize);
      renderer.domElement.removeEventListener("webglcontextlost", onContextLost);

      scene.remove(points, glow, world);
      rings.forEach((r) => {
        r.geometry.dispose();
        (r.material as THREE.Material).dispose();
      });

      geometry.dispose();
      material.dispose();
      glowTex.dispose();
      glowMat.dispose();

      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  if (webglFailed) {
    return <CSSFallback />;
  }

  return (
    <div
      ref={mountRef}
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      aria-hidden="true"
      role="presentation"
    />
  );
}