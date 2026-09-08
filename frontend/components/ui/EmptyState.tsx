"use client";

import { ReactNode } from "react";
import { cx } from "@/lib/utils";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({
  icon,
  title,
  message,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cx(
        "flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--border-strong)] bg-[rgba(255,255,255,0.02)] px-6 py-12 text-center",
        className
      )}
    >
      {icon && <div className="text-4xl opacity-70">{icon}</div>}
      <h3 className="text-lg font-semibold text-[var(--text)]">{title}</h3>
      {message && <p className="max-w-sm text-sm text-[var(--text-muted)]">{message}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
