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

  const handleSelect = (status: AttendanceStatus) => {
    onSelect(status);
    if (!prefersReducedMotion() && rowRef.current) {
      animate(rowRef.current, {
        backgroundColor: [`${DOT[status]}22`, "rgba(255,255,255,0.02)"],
        duration: 400,
        ease: "outQuad",
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
          className="h-2 w-2 shrink-0 rounded-full"
          style={{ background: DOT[selected], boxShadow: `0 0 8px ${DOT[selected]}` }}
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
                "flex h-8 min-w-[2rem] items-center justify-center rounded-lg border px-1.5 text-xs font-medium transition-all",
                active
                  ? "border-transparent text-white"
                  : "border-[var(--border-strong)] text-[var(--text-faint)] hover:bg-[rgba(255,255,255,0.06)]"
              )}
              style={active ? { background: s.color } : undefined}
            >
              {s.label.slice(0, 1)}
              <span className="ml-1 hidden sm:inline">{s.label.slice(1)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
