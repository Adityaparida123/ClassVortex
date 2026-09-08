"use client";

import { useRef, useEffect, useState } from "react";
import { animate } from "animejs";
import { cx, clampPercent, prefersReducedMotion } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  className?: string;
  height?: number;
}

export default function ProgressBar({
  value,
  max = 100,
  color = "var(--primary)",
  className,
  height = 8,
}: ProgressBarProps) {
  const fillRef = useRef<HTMLDivElement>(null);
  const [display, setDisplay] = useState(prefersReducedMotion() ? clampPercent((value / max) * 100) : 0);

  useEffect(() => {
    const target = clampPercent((value / max) * 100);
    if (!fillRef.current) return;
    if (prefersReducedMotion()) {
      setDisplay(target);
      return;
    }
    animate(fillRef.current, {
      width: [`${display}%`, `${target}%`],
      duration: 700,
      ease: "outCubic",
    });
    setDisplay(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, max]);

  return (
    <div
      className={cx("w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.08)]", className)}
      style={{ height }}
      role="progressbar"
      aria-valuenow={Math.round(clampPercent((value / max) * 100))}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        ref={fillRef}
        className="h-full rounded-full transition-[background]"
        style={{ width: `${display}%`, background: `linear-gradient(90deg, ${color}, ${color}cc)` }}
      />
    </div>
  );
}
