import { ReactNode } from "react";
import { cx } from "@/lib/utils";

type BadgeVariant = "success" | "danger" | "warning" | "info" | "neutral" | "primary";

const variants: Record<BadgeVariant, string> = {
  success: "bg-[rgba(52,211,153,0.15)] text-[var(--success)] border-[rgba(52,211,153,0.3)]",
  danger: "bg-[rgba(251,113,133,0.15)] text-[var(--danger)] border-[rgba(251,113,133,0.3)]",
  warning: "bg-[rgba(251,191,36,0.15)] text-[var(--warning)] border-[rgba(251,191,36,0.3)]",
  info: "bg-[rgba(56,189,248,0.15)] text-[var(--info)] border-[rgba(56,189,248,0.3)]",
  neutral: "bg-[rgba(255,255,255,0.06)] text-[var(--text-muted)] border-[var(--border-strong)]",
  primary: "bg-[rgba(124,106,255,0.15)] text-[var(--primary-2)] border-[rgba(124,106,255,0.3)]",
};

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export default function Badge({ children, variant = "neutral", className }: BadgeProps) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
