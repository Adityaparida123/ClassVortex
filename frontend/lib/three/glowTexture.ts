import * as THREE from "three";

/**
 * Shared radial-gradient glow texture used by Three.js sprites
 * (AttendanceVortex3D orb halo and the global VortexBackground).
 */
export function makeGlowTexture(size = 128): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    // Extremely unlikely on a canvas-backed environment; produce a 1x1 white
    // texture so callers never crash.
    const tex = new THREE.CanvasTexture(canvas);
    return tex;
  }
  const c = size / 2;
  const grad = ctx.createRadialGradient(c, c, 0, c, c, c);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.35, "rgba(255,255,255,0.55)");
  grad.addColorStop(0.7, "rgba(255,255,255,0.15)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}