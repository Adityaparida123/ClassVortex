"use client";

import { useRef } from "react";
import { animate } from "animejs";
import type { AttendanceStatus } from "@/types/attendance";
import { ATTENDANCE_STATUSES } from "@/lib/constants";
import { cx, prefersReducedMotion } from "@/lib/utils";

interface AttendanceRowProps {
  rollNumber: string;
  name: string;
  selected: AttendanceStatus;
  onSelect: (status: AttendanceStatus) => void;
  index: number;
}

const DOT: Record<AttendanceStatus, string> = {
  present: "var(--success)",
  absent: "var(--danger)",
  late: "var(--warning)",
  excused: "var(--info)",
};

export default function AttendanceRow({
  rollNumber,
  name,
  selected,
  onSelect,
  index,
}: AttendanceRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLSpanElement>(null);
  const reduced = prefersReducedMotion();

  const handleSelect = (status: AttendanceStatus) => {
    onSelect(status);
    if (reduced) return;
    if (rowRef.current) {
      // Short status-change pulse; small enough to stay fast.
      animate(rowRef.current, {
        backgroundColor: [`${DOT[status]}1f`, "rgba(255,255,255,0.02)"],
        scale: [1, 1.01, 1],
        duration: 320,
        ease: "outQuad",
      });
    }
    if (dotRef.current) {
      // Pop the status dot to confirm selection instantly.
      animate(dotRef.current, {
        scale: [1, 1.8, 1],
        duration: 260,
        ease: "outBack",
      });
    }
  };

  return (
    <div
      ref={rowRef}
      className="grid grid-cols-[auto_1fr] items-center gap-3 rounded-xl border border-[var(--border)] bg-[rgba(255,255,255,0.02)] px-3 py-2.5 sm:grid-cols-[60px_1fr_auto]"
      style={{
        animationDelay: `${index * 30}ms`,
      }}
    >
      <span className="hidden w-14 font-mono text-xs text-[var(--text-faint)] sm:block">
        {rollNumber}
      </span>
      <div className="flex min-w-0 items-center gap-3">
        <span
          ref={dotRef}
          className="h-2.5 w-2.5 shrink-0 rounded-full"
          style={{
            background: DOT[selected],
            boxShadow: `0 0 8px ${DOT[selected]}`,
            transform: "scale(1)",
          }}
        />
        <span className="truncate text-sm font-medium text-[var(--text)]">{name}</span>
      </div>

      <div className="flex items-center gap-1" role="group" aria-label={`Mark ${name} attendance`}>
        {ATTENDANCE_STATUSES.map((s) => {
          const active = selected === s.value;
          return (
            <button
              key={s.value}
              type="button"
              onClick={() => handleSelect(s.value)}
              aria-pressed={active}
              title={s.label}
              className={cx(
                "flex h-8 min-w-[2rem] items-center justify-center gap-0.5 rounded-lg border px-1.5 text-xs font-medium transition-all",
                active
                  ? "border-transparent text-white"
                  : "border-[var(--border-strong)] text-[var(--text-faint)] hover:bg-[rgba(255,255,255,0.06)]"
              )}
              style={active ? { background: s.color, boxShadow: `0 0 12px ${s.color}66` } : undefined}
            >
              {active && (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="m5 13 4 4L19 7" />
                </svg>
              )}
              {s.label.slice(0, 1)}
              <span className="ml-0.5 hidden sm:inline">{s.label.slice(1)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
