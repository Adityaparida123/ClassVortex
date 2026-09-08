"use client";

import { HTMLAttributes, ReactNode, forwardRef } from "react";
import { cx } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: "glass" | "glass-strong" | "plain";
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, variant = "glass", className, ...rest }, ref) => {
    const base =
      variant === "glass-strong"
        ? "glass-strong"
        : variant === "plain"
        ? "rounded-2xl border border-[var(--border)] bg-[var(--surface)]"
        : "glass";
    return (
      <div ref={ref} className={cx(base, className)} {...rest}>
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export default Card;
