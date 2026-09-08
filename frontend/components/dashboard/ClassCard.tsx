"use client";

import { useEffect, useRef, useState } from "react";
import Card from "@/components/ui/Card";
import { formatTime, prefersReducedMotion } from "@/lib/utils";
import { cardIn, hoverLift } from "@/animations/cardAnimations";

interface ClassCardProps {
  name: string;
  time?: string;
  subjectName?: string;
  present?: number;
  total?: number;
  onTake?: () => void;
  delay?: number;
}

export default function ClassCard({
  name,
  time,
  subjectName,
  present,
  total,
  onTake,
  delay = 0,
}: ClassCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);
  const pct = total ? Math.round((present ?? 0) / total * 100) : null;
  const accent = pct === null ? "var(--primary)" : pct >= 75 ? "var(--success)" : "var(--warning)";

  useEffect(() => {
    cardIn(ref.current, { duration: 500, delay });
  }, [delay]);

  useEffect(() => {
    if (hovered && ref.current) hoverLift(ref.current, { on: true });
    else if (ref.current) hoverLift(ref.current, { on: false });
  }, [hovered]);

  return (
    <Card
      ref={ref}
      className="group flex items-center justify-between gap-3 rounded-2xl px-4 py-3 opacity-0 will-change-transform"
      variant="glass"
    >
      <div
        className="flex items-center gap-3"
        onPointerEnter={() => !prefersReducedMotion() && setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-lg font-bold text-[var(--bg)]"
          style={{ background: `linear-gradient(135deg, var(--primary-2), var(--primary))` }}
        >
          {name.slice(0, 1)}
        </div>
        <div>
          <div className="font-semibold text-[var(--text)]">{name}</div>
          <div className="text-xs text-[var(--text-muted)]">
            {subjectName && <span>{subjectName} · </span>}
            {time ? formatTime(time) : ""}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {pct !== null && (
          <div className="text-right">
            <div className="text-sm font-bold" style={{ color: accent }}>
              {pct}%
            </div>
            <div className="text-xs text-[var(--text-faint)]">
              {present}/{total}
            </div>
          </div>
        )}
        {onTake && (
          <button onClick={onTake} className="btn-ghost !px-3 !py-1.5 !text-xs opacity-0 transition-opacity group-hover:opacity-100">
            Take Attendance
          </button>
        )}
      </div>
    </Card>
  );
}
