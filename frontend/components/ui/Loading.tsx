"use client";

import { cx } from "@/lib/utils";

interface LoadingProps {
  message?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export default function Loading({
  message = "Loading...",
  className,
  size = "md",
}: LoadingProps) {
  const dim =
    size === "sm" ? "h-6 w-6" : size === "lg" ? "h-12 w-12" : "h-8 w-8";
  return (
    <div
      className={cx("flex flex-col items-center justify-center gap-3 py-10 text-[var(--text-muted)]", className)}
      role="status"
      aria-live="polite"
    >
      <div className="relative">
        <div className={cx(dim, "rounded-full border-2 border-[var(--primary)] border-t-transparent animate-spin")} />
        <div className={cx(dim, "absolute inset-0 rounded-full border-2 border-[var(--primary-2)]/40 border-b-transparent animate-spin-slow")} />
      </div>
      <p className="text-sm">{message}</p>
    </div>
  );
}
