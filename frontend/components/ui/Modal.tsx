"use client";

import { ReactNode, useEffect, useRef } from "react";
import { animate } from "animejs";
import { cx, prefersReducedMotion } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function Modal({ open, onClose, title, children, className }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && panelRef.current && overlayRef.current && !prefersReducedMotion()) {
      animate(overlayRef.current, { opacity: [0, 1], duration: 200, ease: "outQuad" });
      animate(panelRef.current, {
        opacity: [0, 1],
        translateY: [24, 0],
        scale: [0.96, 1],
        duration: 280,
        ease: "outBack",
      });
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      style={{ opacity: 0 }}
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title ?? "Dialog"}
        className={cx(
          "glass-strong w-full max-w-lg rounded-2xl p-6 shadow-2xl",
          className
        )}
        style={{ opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button
              onClick={onClose}
              aria-label="Close"
              className="btn-ghost !px-2 !py-1"
            >
              ✕
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
