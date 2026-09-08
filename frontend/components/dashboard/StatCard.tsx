"use client";

import { useEffect, useRef, useState } from "react";
import { numberCountUp } from "@/animations/numberAnimations";
import { cardIn, hoverLift } from "@/animations/cardAnimations";
import { prefersReducedMotion } from "@/lib/utils";
import Card from "@/components/ui/Card";

interface StatCardProps {
  label: string;
  value: number;
  suffix?: string;
  icon?: string;
  accent?: string;
  decimals?: boolean;
  delay?: number;
  enableHover?: boolean;
}

export default function StatCard({
  label,
  value,
  suffix = "",
  icon,
  accent = "var(--primary)",
  decimals = false,
  delay = 0,
  enableHover = true,
}: StatCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const numRef = useRef<HTMLSpanElement>(null);
  const [hovered, setHovered] = useState(false);

  useEffect(() => {
    cardIn(ref.current, { duration: 500, delay });
    numberCountUp(0, value, (v) => {
      if (numRef.current) {
        numRef.current.textContent = decimals ? v.toFixed(1) : String(v);
      }
    }, { duration: 1000, decimals: decimals ? 1 : 0 });
  }, [value, decimals, delay]);

  // Subtle hover depth (desktop only via fine pointer).
  useEffect(() => {
    if (enableHover && hovered && ref.current) {
      hoverLift(ref.current, { on: true });
    } else if (enableHover && ref.current) {
      hoverLift(ref.current, { on: false });
    }
  }, [hovered, enableHover]);

  return (
    <Card
      ref={ref}
      className="glass p-4 opacity-0 transition-shadow duration-200 will-change-transform"
      variant="glass"
    >
      <div
        className="flex items-start justify-between"
        onPointerEnter={() => !prefersReducedMotion() && setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--text-faint)]">
            {label}
          </p>
          <p className="mt-1.5 text-3xl font-bold text-[var(--text)]">
            <span ref={numRef}>0</span>
            <span className="ml-1 text-sm text-[var(--text-muted)]">{suffix}</span>
          </p>
        </div>
        {icon && (
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg"
            style={{ background: `${accent}22`, color: accent }}
          >
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
