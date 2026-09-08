"use client";

import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";
import { cx } from "@/lib/utils";
import { pulsePress } from "@/animations/index";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  animate?: boolean;
  children: ReactNode;
}

const sizes: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", size = "md", animate = true, className, onPointerDown, children, ...rest },
    ref
  ) => {
    const base =
      variant === "primary"
        ? "btn-primary"
        : variant === "danger"
        ? "btn-danger"
        : "btn-ghost";

    const handlePress = (e: React.PointerEvent<HTMLButtonElement>) => {
      if (animate && e.currentTarget) {
        pulsePress(e.currentTarget);
      }
      onPointerDown?.(e);
    };

    return (
      <button
        ref={ref}
        onPointerDown={handlePress}
        className={cx(base, sizes[size], className)}
        {...rest}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
