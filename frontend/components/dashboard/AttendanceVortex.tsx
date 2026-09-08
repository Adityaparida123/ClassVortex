"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { AttendanceVortex3DProps } from "./AttendanceVortex3D";
import { countUp, scaleIn } from "@/animations/index";
import { prefersReducedMotion, cx } from "@/lib/utils";

interface AttendanceVortexProps {
  percentage: number;
  label?: string;
  size?: number;
  subtitle?: string;
}

type VortexState = "high" | "warning" | "low";

function getVortexState(pct: number): VortexState {
  if (pct >= 85) return "high";
  if (pct >= 75) return "warning";
  return "low";
}

const STATE_THEME: Record<
  VortexState,
  { accent: string; ring: string; status: string; solid: string; soft: string }
> = {
  high: {
    accent: "var(--success)",
    ring: "rgba(52,211,153,0.35)",
    status: "Healthy",
    solid: "#34d399",
    soft: "rgba(52,211,153,0.12)",
  },
  warning: {
    accent: "var(--warning)",
    ring: "rgba(251,191,36,0.35)",
    status: "Monitor",
    solid: "#fbbf24",
    soft: "rgba(251,191,36,0.12)",
  },
  low: {
    accent: "var(--danger)",
    ring: "rgba(251,113,133,0.4)",
    status: "Needs Attention",
    solid: "#fb7185",
    soft: "rgba(251,113,133,0.14)",
  },
};

// WebGL 3D vortex, loaded only on the client. The 2D SVG version is the
// fallback if WebGL is unavailable or initialization throws.
const AttendanceVortex3D = dynamic<AttendanceVortex3DProps>(
  () => import("./AttendanceVortex3D").then((m) => m.default),
  { ssr: false, loading: () => null }
);

function detectWebGL(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    return !!gl;
  } catch {
    return false;
  }
}

/**
 * AttendVortex — attendance visualization wrapper.
 * Renders the Three.js 3D vortex when WebGL is available, otherwise falls
 * back to the 2D SVG/HTML vortex. The percentage/status are always rendered
 * as accessible HTML text, never only in WebGL.
 */
export default function AttendanceVortex({
  percentage,
  label = "Attendance",
  size = 240,
  subtitle,
}: AttendanceVortexProps) {
  const [webgl, setWebgl] = useState<boolean | null>(null);
  const [webglError, setWebglError] = useState(false);

  useEffect(() => {
    setWebgl(detectWebGL());
    if (webglError) setWebglError(false);
  }, [webglError]);

  const use3D = webgl === true && !webglError;

  const clamped = Math.max(0, Math.min(100, percentage));
  const state = getVortexState(clamped);
  const theme = STATE_THEME[state];

  const display = useDisplayNumber(clamped);

  return (
    <div
      className="relative flex flex-col items-center justify-center"
      style={{ width: size, height: "auto" }}
      role="img"
      aria-label={`${label}: ${percentage.toFixed(1)} percent — ${theme.status}`}
    >
      <div className="relative" style={{ width: size, height: size }}>
        {webgl === null ? (
          <FallbackVortex percentage={percentage} theme={theme} />
        ) : use3D ? (
          <AttendanceVortex3D
            percentage={percentage}
            size={size}
            onError={() => setWebglError(true)}
          />
        ) : (
          <FallbackVortex percentage={percentage} theme={theme} />
        )}
      </div>

      {/* Always-visible HTML text for accessibility/status. Positioned over
          the center of the visualization. */}
      <div
        className="pointer-events-none absolute z-10 flex flex-col items-center text-center"
        style={{ top: 0, left: 0, right: 0, margin: "auto", height: size, justifyContent: "center" }}
      >
        <span className="text-4xl font-bold tracking-tight sm:text-5xl drop-shadow-[0_0_18px_rgba(0,0,0,0.6)]">
          <span>{display.toFixed(1)}</span>
          <span className="text-2xl text-[var(--text-muted)]">%</span>
        </span>
        <span
          className={cx(
            "mt-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
            "bg-black/30 backdrop-blur-sm"
          )}
          style={{ color: theme.solid, borderColor: theme.ring }}
        >
          {theme.status}
        </span>
        <span className="mt-1.5 text-xs font-medium uppercase tracking-widest text-[var(--text-muted)]">
          {label}
        </span>
        {subtitle && (
          <span className="mt-0.5 text-xs text-[var(--text-faint)]">{subtitle}</span>
        )}
      </div>
    </div>
  );
}

function useDisplayNumber(clamped: number): number {
  const reduced = prefersReducedMotion();
  const [display, setDisplay] = useState(reduced ? clamped : 0);
  useEffect(() => {
    if (reduced) {
      setDisplay(clamped);
      return;
    }
    countUp(0, clamped, setDisplay, { duration: 1400, decimals: 1 });
  }, [clamped, reduced]);
  return display;
}

/* ───────────── 2D SVG fallback (kept from the original) ─────────── */

function FallbackVortex({
  percentage,
  theme,
}: {
  percentage: number;
  theme: (typeof STATE_THEME)[VortexState];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<SVGSVGElement>(null);
  const outerRingRef = useRef<SVGCircleElement>(null);
  const p1 = useRef<HTMLDivElement>(null);
  const p2 = useRef<HTMLDivElement>(null);

  const clamped = Math.max(0, Math.min(100, percentage));
  const radius = 90;
  const circumference = 2 * Math.PI * radius;
  const radialStops = Array.from({ length: 24 }, (_, i) => i);

  useEffect(() => {
    scaleIn(containerRef.current, { duration: 900 });
    const draw = () => {
      const offset = circumference - (clamped / 100) * circumference;
      if (outerRingRef.current) {
        outerRingRef.current.style.strokeDashoffset = String(offset);
      }
    };
    draw();
  }, [clamped, circumference]);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    let raf1 = 0;
    let raf2 = 0;
    let angle1 = 0;
    let angle2 = 120;
    const loop1 = () => {
      raf1 = requestAnimationFrame(loop1);
      if (p1.current) p1.current.style.transform = `rotate(${(angle1 += 0.06)}deg) translateX(120px)`;
    };
    const loop2 = () => {
      raf2 = requestAnimationFrame(loop2);
      if (p2.current) p2.current.style.transform = `rotate(${(angle2 += 0.04)}deg) translateX(128px)`;
    };
    raf1 = requestAnimationFrame(loop1);
    raf2 = requestAnimationFrame(loop2);
    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 flex items-center justify-center"
      style={{ opacity: 0 }}
    >
      <div ref={p1} className="absolute inset-0">
        <div className="absolute h-2 w-2 rounded-full bg-[var(--primary-2)] shadow-[0_0_8px_var(--primary-2)]" style={{ left: -4, top: "50%" }} />
      </div>
      <div ref={p2} className="absolute inset-0">
        <div className="absolute h-1.5 w-1.5 rounded-full bg-[var(--primary)] shadow-[0_0_6px_var(--primary)]" style={{ left: "calc(50% - 4px)", top: -4 }} />
      </div>

      <svg className="absolute inset-0" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        {radialStops.map((stop) => (
          <line
            key={stop}
            x1="100"
            y1="12"
            x2="100"
            y2={stop % 3 === 0 ? "20" : "16"}
            stroke={stop % 3 === 0 ? "rgba(124,106,255,0.5)" : "rgba(255,255,255,0.18)"}
            strokeWidth="1"
            transform={`rotate(${(stop / 24) * 360} 100 100)`}
          />
        ))}
      </svg>

      <svg className="absolute inset-0" viewBox="0 0 200 200" fill="none">
        <circle cx="100" cy="100" r={radius} stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <circle
          ref={outerRingRef}
          cx="100"
          cy="100"
          r={radius}
          stroke={theme.ring}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          transform="rotate(-90 100 100)"
        />
      </svg>

      <svg className="absolute inset-0" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <circle cx="100" cy="100" r={radius - 16} stroke={theme.accent} strokeWidth="2" strokeDasharray="4 10" strokeLinecap="round" opacity="0.5" />
      </svg>

      <svg ref={ringRef} className="absolute inset-0" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <circle cx="100" cy="100" r="97" stroke="rgba(124,106,255,0.22)" strokeWidth="1" strokeDasharray="2 6" />
      </svg>
    </div>
  );
}
