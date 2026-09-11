"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { prefersReducedMotion } from "@/lib/utils";
import { makeGlowTexture } from "@/lib/three/glowTexture";

export interface Vortex3DTheme {
  status: string;
  solid: string;
  glow: string;
  particle: string;
}

export function vortex3DState(pct: number): Vortex3DTheme {
  if (pct >= 85) {
    return { status: "Healthy", solid: "#34d399", glow: "#34d399", particle: "#4bd8ff" };
  }
  if (pct >= 75) {
    return { status: "Monitor", solid: "#fbbf24", glow: "#fbbf24", particle: "#fbbf24" };
  }
  return { status: "Needs Attention", solid: "#fb7185", glow: "#fb7185", particle: "#fb7185" };
}

export interface AttendanceVortex3DProps {
  percentage: number;
  size?: number;
  onError?: () => void;
}

function isMobile(): boolean {
  if (typeof window === "undefined") return false;
  return window.innerWidth < 768;
}

/**
 * Real 3D AttendVortex built with Three.js.
 * Isolated so its scene, camera, renderer, geometries, materials, particles,
 * animation loop, resize handling and cleanup all live inside this component.
 *
 * Decorative/informational — the attendance percentage and status are always
 * rendered as HTML text by the parent, never only in WebGL.
 */
export default function AttendanceVortex3D({
  percentage,
  size = 240,
  onError,
}: AttendanceVortex3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sizeRef = useRef(size);
  const pctRef = useRef(percentage);

  // Keep refs in sync without restarting Three on every render.
  useEffect(() => {
    sizeRef.current = size;
  }, [size]);
  useEffect(() => {
    pctRef.current = percentage;
  }, [percentage]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const reduced = prefersReducedMotion();
    const mobile = isMobile();

    // Particle count scaled down on mobile.
    const ORBIT_PARTICLES = mobile ? 350 : 750;
    const FLOW_PARTICLES = mobile ? 220 : 550;

    // ---- Renderer ----
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: !mobile,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      onError?.();
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.5 : 2));
    renderer.setSize(sizeRef.current, sizeRef.current);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    // ---- Scene & Camera ----
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      sizeRef.current / sizeRef.current,
      0.1,
      100
    );
    camera.position.set(0, 0, 7);
    camera.lookAt(0, 0, 0);

    const theme = vortex3DState(pctRef.current);

    // ---- Central orb ----
    const orbGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const orbMat = new THREE.MeshBasicMaterial({ color: theme.solid, transparent: true, opacity: 0.9 });
    const orb = new THREE.Mesh(orbGeo, orbMat);
    scene.add(orb);

    // Glow halo (billboard-ish additive sprite).
    const glowTex = makeGlowTexture();
    const glowMat = new THREE.SpriteMaterial({
      map: glowTex,
      color: theme.glow,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const glow = new THREE.Sprite(glowMat);
    glow.scale.set(2.6, 2.6, 1);
    scene.add(glow);

    // ---- Orbital rings (tilted for a 3D feel) ----
    const rings: THREE.Mesh[] = [];
    const ringSizes = [1.7, 2.25, 2.8];
    const ringSpeeds = [0.25, -0.16, 0.11];
    const ringTilts = [
      [Math.PI / 2, 0, 0],
      [Math.PI / 2.4, 0.4, 0],
      [Math.PI / 1.8, -0.5, 0.3],
    ];
    ringSizes.forEach((r, i) => {
      const g = new THREE.RingGeometry(r - 0.03, r + 0.005, 64);
      const m = new THREE.MeshBasicMaterial({
        color: theme.particle,
        transparent: true,
        opacity: 0.22 + i * 0.06,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      const mesh = new THREE.Mesh(g, m);
      mesh.rotation.set(ringTilts[i][0], ringTilts[i][1], ringTilts[i][2]);
      scene.add(mesh);
      rings.push(mesh);
    });

    // ---- Orbiting particles (around rings) ----
    const orbitParticles = buildOrbitParticles(ORBIT_PARTICLES, reduced ? 0.4 : 1);
    scene.add(orbitParticles.mesh);

    // ---- Flowing particles (vortex stream into center) ----
    const flowParticles = buildFlowParticles(FLOW_PARTICLES, reduced ? 0.3 : 1);
    scene.add(flowParticles.mesh);

    // ---- Resize handling ----
    const onResize = () => {
      const s = sizeRef.current;
      renderer.setSize(s, s);
      camera.aspect = 1;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    // ---- Animation loop ----
    let rafId = 0;
    let running = true;
    const timer = new THREE.Timer();

    // Persistent color targets (avoid per-frame allocations).
    const orbTarget = new THREE.Color(theme.solid);
    const glowTarget = new THREE.Color(theme.glow);
    const particleTarget = new THREE.Color(theme.particle);
    let lastStateKey = theme.status;

    const tick = () => {
      if (!running) return;
      rafId = requestAnimationFrame(tick);
      timer.update();
      const t = timer.getElapsed();
      const animScale = reduced ? 0.15 : 1;

      // Rotate main vortex slowly.
      scene.rotation.y = t * 0.15 * animScale;

      // Orb pulse.
      const pulse = 1 + Math.sin(t * 2) * 0.04;
      orb.scale.setScalar(pulse);
      glow.scale.setScalar(2.6 + Math.sin(t * 1.6) * 0.15);

      // Rings rotate independently.
      rings.forEach((ring, i) => {
        ring.rotation.z += ringSpeeds[i] * 0.01 * animScale;
      });

      // Orbit particles.
      updateOrbitParticles(orbitParticles, t, reduced);

      // Flow particles spiral inward.
      updateFlowParticles(flowParticles, t, reduced);

      // React to attendance state: only update targets when the state changes.
      const currentTheme = vortex3DState(pctRef.current);
      if (currentTheme.status !== lastStateKey) {
        lastStateKey = currentTheme.status;
        orbTarget.set(currentTheme.solid);
        glowTarget.set(currentTheme.glow);
        particleTarget.set(currentTheme.particle);
      }
      // Particle intensity weakens when attendance drops (not just color).
      const intensity =
        currentTheme.status === "Healthy" ? 0.9
        : currentTheme.status === "Monitor" ? 0.72
        : 0.55;
      orbitParticles.mesh.material.opacity +=
        (intensity - orbitParticles.mesh.material.opacity) * 0.04;
      flowParticles.mesh.material.opacity +=
        (intensity - 0.2 - flowParticles.mesh.material.opacity) * 0.04;

      // Lerp orb/glow/rings toward the theme color (cheap, no new materials).
      lerpColor(orbMat.color, orbTarget, 0.05);
      glowMat.color.lerp(glowTarget, 0.05);
      rings.forEach((ring) => {
        (ring.material as THREE.MeshBasicMaterial).color.lerp(particleTarget, 0.05);
      });

      renderer.render(scene, camera);
    };
    tick();

    // ---- Cleanup ----
    return () => {
      running = false;
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", onResize);

      scene.remove(orb, glow, orbitParticles.mesh, flowParticles.mesh);
      rings.forEach((r) => scene.remove(r));

      orbGeo.dispose();
      orbMat.dispose();
      glowMat.map?.dispose();
      glowMat.dispose();
      rings.forEach((r) => (r.material as THREE.Material).dispose());
      rings.forEach((r) => (r.geometry as THREE.BufferGeometry).dispose());

      orbitParticles.geometry.dispose();
      (orbitParticles.mesh.material as THREE.Material).dispose();
      flowParticles.geometry.dispose();
      (flowParticles.mesh.material as THREE.Material).dispose();

      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      ref={mountRef}
      style={{ width: size, height: size }}
      className="pointer-events-none relative"
      aria-hidden="true"
    />
  );
}

/* ───────────────────────── helpers ───────────────────────── */

function buildOrbitParticles(count: number, speedScale: number) {
  const positions = new Float32Array(count * 3);
  const radiuses = new Float32Array(count);
  const angles = new Float32Array(count);
  const speeds = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const r = 1.8 + Math.random() * 1.6;
    const a = Math.random() * Math.PI * 2;
    const elevation = (Math.random() - 0.5) * 1.4;
    radiuses[i] = r;
    angles[i] = a;
    speeds[i] = (0.4 + Math.random() * 1.2) * speedScale;
    positions[i * 3] = Math.cos(a) * r;
    positions[i * 3 + 1] = elevation;
    positions[i * 3 + 2] = Math.sin(a) * r;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: "#7c6aff",
    size: 0.045,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  });

  const mesh = new THREE.Points(geometry, material);
  return { mesh, geometry, radiuses, angles, speeds };
}

function updateOrbitParticles(
  p: ReturnType<typeof buildOrbitParticles>,
  t: number,
  reduced: boolean
) {
  const pos = p.geometry.attributes.position.array as Float32Array;
  const scale = reduced ? 0.15 : 1;
  for (let i = 0; i < p.radiuses.length; i++) {
    const a = p.angles[i] + t * p.speeds[i] * scale;
    const r = p.radiuses[i];
    pos[i * 3] = Math.cos(a) * r;
    pos[i * 3 + 1] = p.radiuses[i] > 3 ? Math.sin(t * 0.6) * 0.6 : Math.sin(t * 1.2) * 0.4;
    pos[i * 3 + 2] = Math.sin(a) * r;
  }
  p.geometry.attributes.position.needsUpdate = true;
}

function buildFlowParticles(count: number, speedScale: number) {
  const positions = new Float32Array(count * 3);
  const radii = new Float32Array(count);
  const theta = new Float32Array(count);
  const speed = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    radii[i] = 1 + Math.random() * 2.4;
    theta[i] = Math.random() * Math.PI * 2;
    speed[i] = (0.6 + Math.random() * 1.0) * speedScale;
    positions[i * 3] = Math.cos(theta[i]) * radii[i];
    positions[i * 3 + 1] = (Math.random() - 0.5) * 1.2;
    positions[i * 3 + 2] = Math.sin(theta[i]) * radii[i];
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: "#4bd8ff",
    size: 0.05,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  });

  const mesh = new THREE.Points(geometry, material);
  return { mesh, geometry, radii, theta, speed };
}

function updateFlowParticles(
  p: ReturnType<typeof buildFlowParticles>,
  t: number,
  reduced: boolean
) {
  const pos = p.geometry.attributes.position.array as Float32Array;
  const scale = reduced ? 0.12 : 1;
  for (let i = 0; i < p.radii.length; i++) {
    // Modulo phase keeps particles recycling correctly even at large t.
    const cycle = p.radii[i] / (0.12 * p.speed[i] * scale);
    const phase = (t % cycle) * 0.12 * p.speed[i] * scale;
    const r = p.radii[i] - phase;
    const a = p.theta[i] + t * 1.4 * scale;
    pos[i * 3] = Math.cos(a) * r;
    pos[i * 3 + 1] = Math.sin(t * 0.8 + a) * 0.2;
    pos[i * 3 + 2] = Math.sin(a) * r;
  }
  p.geometry.attributes.position.needsUpdate = true;
}

function lerpColor(color: THREE.Color, target: THREE.Color, alpha: number) {
  color.lerp(target, alpha);
}
