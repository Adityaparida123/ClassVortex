import { animate, stagger } from "animejs";
import { prefersReducedMotion } from "@/lib/utils";

const DEFAULTS = {
  duration: 500,
  ease: "outCubic" as const,
};

function shouldReduce(): boolean {
  return prefersReducedMotion();
}

/**
 * Fade + rise entrance for an element.
 */
type AnimTarget = HTMLElement | SVGElement | null;

export function animateIn(
  el: AnimTarget,
  opts: { duration?: number; delay?: number } = {}
): void {
  if (!el) return;
  if (shouldReduce()) {
    el.style.opacity = "1";
    el.style.transform = "none";
    return;
  }
  animate(el, {
    opacity: [0, 1],
    translateY: [16, 0],
    duration: opts.duration ?? DEFAULTS.duration,
    delay: opts.delay ?? 0,
    ease: DEFAULTS.ease,
  });
}

/**
 * Stagger multiple elements.
 */
export function staggerIn(
  els: (AnimTarget | undefined)[],
  opts: { duration?: number; stagger?: number; from?: "first" | "center" | "last" } = {}
): void {
  const targets = (els.filter(Boolean) as (HTMLElement | SVGElement)[]).map((el) => el as HTMLElement & SVGElement);
  if (targets.length === 0) return;
  if (shouldReduce()) {
    targets.forEach((el) => {
      el.style.opacity = "1";
      el.style.transform = "none";
    });
    return;
  }
  animate(targets, {
    opacity: [0, 1],
    translateY: [20, 0],
    delay: stagger(opts.stagger ?? 70, {
      from: opts.from ?? "first",
      start: 0,
    }),
    duration: opts.duration ?? DEFAULTS.duration,
    ease: DEFAULTS.ease,
  });
}

/**
 * Animate a numeric value on a JS object using onUpdate.
 */
export function countUp(
  from: number,
  to: number,
  onUpdate: (value: number) => void,
  opts: { duration?: number; decimals?: number } = {}
): void {
  if (shouldReduce()) {
    onUpdate(to);
    return;
  }
  const obj = { value: from };
  animate(obj, {
    value: to,
    duration: opts.duration ?? 1200,
    ease: "outQuart" as const,
    onUpdate: () => {
      const v = Number(obj.value);
      onUpdate(opts.decimals ? Number(v.toFixed(opts.decimals)) : Math.round(v));
    },
  });
}

/**
 * Scale an element into view (used for the vortex).
 */
export function scaleIn(
  el: AnimTarget,
  opts: { duration?: number; from?: number } = {}
): void {
  if (!el) return;
  if (shouldReduce()) {
    el.style.opacity = "1";
    el.style.transform = "none";
    el.style.scale = "1";
    return;
  }
  animate(el, {
    opacity: [0, 1],
    scale: [opts.from ?? 0.6, 1],
    duration: opts.duration ?? 900,
    ease: "outBack" as const,
  });
}

/**
 * Simple pulse / attention before resetting.
 */
export function pulsePress(el: AnimTarget): void {
  if (!el || shouldReduce()) return;
  animate(el, {
    scale: [1, 0.96, 1],
    duration: 250,
    ease: "outQuad" as const,
  });
}

/**
 * Continuous slow rotation (vortex outer ring).
 */
export function continuousRotate(
  el: AnimTarget,
  opts: { duration?: number } = {}
): void {
  if (!el || shouldReduce()) return;
  animate(el, {
    rotate: [0, 360],
    duration: opts.duration ?? 24000,
    loop: true,
    ease: "linear" as const,
  });
}

/**
 * Subtle hover lift + shadow for cards. Only meaningful on devices
 * that support hover (fine pointer). Safe to ignore elsewhere.
 */
export function hoverLift(
  el: AnimTarget,
  opts: { on: boolean; distance?: number; duration?: number } = { on: true }
): void {
  if (!el || shouldReduce()) return;
  const { on, distance = 6, duration = 220 } = opts;
  animate(el, {
    translateY: on ? [-distance, 0][0] ?? 0 : 0,
    scale: on ? 1.015 : 1,
    duration,
    ease: on ? ("outQuad" as const) : ("outCubic" as const),
    ...(on ? { boxShadow: "0 16px 32px -16px rgba(0,0,0,0.5)" } : {}),
  });
}

/**
 * Quick success "flash" for confirmations (marking, saving).
 * A short scale + fade pulse.
 */
export function successPop(
  el: AnimTarget,
  opts: { color?: string; duration?: number } = {}
): void {
  if (!el || shouldReduce()) return;
  const { color = "rgba(52,211,153,0.18)", duration = 500 } = opts;
  animate(el, {
    backgroundColor: [color, "rgba(255,255,255,0.02)"],
    scale: [1, 1.02, 1],
    duration,
    ease: "outQuad" as const,
  });
}

/**
 * Nudge an element to draw attention (e.g. when a value drops).
 */
export function attentionNudge(
  el: AnimTarget,
  opts: { angle?: number; duration?: number } = {}
): void {
  if (!el || shouldReduce()) return;
  const { angle = 2.5, duration = 420 } = opts;
  animate(el, {
    rotate: [-angle, angle, -angle / 2, angle / 2, 0],
    duration,
    ease: "outCubic" as const,
  });
}
