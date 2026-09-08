"use client";

import { useEffect, useRef, useState } from "react";
import { countUp, scaleIn, continuousRotate } from "@/animations/index";
import { prefersReducedMotion } from "@/lib/utils";

interface AttendanceVortexProps {
  percentage: number;
  label?: string;
  size?: number;
  subtitle?: string;
}

/**
 * AttendVortex — circular attendance visualization.
 * Implemented with HTML/CSS/SVG + Anime.js.
 * Isolated so it can be swapped for AttendanceVortex3D (Three.js) later.
 */
export default function AttendanceVortex({
  percentage,
  label = "Attendance",
  size = 240,
  subtitle,
}: AttendanceVortexProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<SVGSVGElement>(null);
  const outerRingRef = useRef<SVGCircleElement>(null);
  const particleRef1 = useRef<HTMLDivElement>(null);
  const particleRef2 = useRef<HTMLDivElement>(null);
  const numberRef = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(prefersReducedMotion() ? percentage : 0);

  const clamped = Math.max(0, Math.min(100, percentage));
  const radius = 90;
  const circumference = 2 * Math.PI * radius;

  function animateOrbit(el: HTMLDivElement, keyframe: string, duration: number) {
    if (prefersReducedMotion()) return;
    el.animate(
      [{ transform: "rotate(0deg) translateX(0px) rotate(0deg)" }, { transform: keyframe }],
      { duration, iterations: Infinity, easing: "linear" }
    );
  }

  useEffect(() => {
    scaleIn(containerRef.current, { duration: 900 });
  }, []);

  useEffect(() => {
    if (ringRef.current) {
      continuousRotate(ringRef.current, { duration: 26000 });
    }
    if (particleRef1.current) {
      animateOrbit(particleRef1.current, "rotate(0deg) translateX(120px) rotate(0deg)", 12000);
    }
    if (particleRef2.current) {
      animateOrbit(particleRef2.current, "rotate(360deg) translateX(135px) rotate(-360deg)", 18000);
    }
  }, []);

  useEffect(() => {
    const draw = () => {
      const offset = circumference - (clamped / 100) * circumference;
      if (outerRingRef.current) {
        outerRingRef.current.style.strokeDashoffset = String(offset);
      }
    };
    draw();
    countUp(0, clamped, (v) => {
      setDisplay(v);
      draw();
    }, { duration: 1400, decimals: 1 });
  }, [clamped, circumference]);

  return (
    <div
      ref={containerRef}
      className="relative flex items-center justify-center"
      style={{ width: size, height: size, opacity: 0 }}
      role="img"
      aria-label={`${label}: ${percentage.toFixed(1)} percent`}
    >
      {/* Orbiting particles */}
      <div ref={particleRef1} className="absolute inset-0">
        <div className="absolute h-2 w-2 rounded-full bg-[var(--primary-2)] shadow-[0_0_8px_var(--primary-2)]" style={{ left: -4, top: "50%" }} />
      </div>
      <div ref={particleRef2} className="absolute inset-0">
        <div className="absolute h-1.5 w-1.5 rounded-full bg-[var(--primary)] shadow-[0_0_6px_var(--primary)]" style={{ left: "calc(50% - 4px)", top: -4 }} />
      </div>

      {/* SVG rings */}
      <svg className="absolute inset-0" viewBox="0 0 200 200" fill="none">
        <circle
          cx="100"
          cy="100"
          r={radius}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="10"
        />
        <circle
          ref={outerRingRef}
          cx="100"
          cy="100"
          r={radius}
          stroke="url(#vortexGrad)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          transform="rotate(-90 100 100)"
        />
        <defs>
          <linearGradient id="vortexGrad" x1="0" y1="0" x2="200" y2="200">
            <stop offset="0%" stopColor="#4bd8ff" />
            <stop offset="100%" stopColor="#7c6aff" />
          </linearGradient>
        </defs>
      </svg>

      {/* Decorative dashed outer ring */}
      <svg
        ref={ringRef}
        className="absolute inset-0"
        viewBox="0 0 200 200"
        fill="none"
        aria-hidden="true"
      >
        <circle
          cx="100"
          cy="100"
          r="97"
          stroke="rgba(124,106,255,0.25)"
          strokeWidth="1"
          strokeDasharray="2 6"
        />
      </svg>

      {/* Extra inner visual line */}
      <div
        className="absolute rounded-full border border-[rgba(255,255,255,0.06)]"
        style={{ width: size * 0.62, height: size * 0.62 }}
      />

      {/* Center content */}
      <div className="relative z-10 flex flex-col items-center text-center">
        <span className="text-4xl font-bold tracking-tight sm:text-5xl">
          <span ref={numberRef}>{display.toFixed(1)}</span>
          <span className="text-2xl text-[var(--text-muted)]">%</span>
        </span>
        <span className="mt-1 text-xs font-medium uppercase tracking-widest text-[var(--text-faint)]">
          {label}
        </span>
        {subtitle && (
          <span className="mt-0.5 text-xs text-[var(--text-faint)]">{subtitle}</span>
        )}
      </div>
    </div>
  );
}
