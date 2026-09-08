"use client";

import { ReactNode, useEffect, useRef } from "react";
import { cx } from "@/lib/utils";
import { pageEntrance } from "@/animations/pageAnimations";

interface PageContainerProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
  animateKey?: string;
}

export default function PageContainer({
  children,
  title,
  subtitle,
  actions,
  className,
  animateKey,
}: PageContainerProps) {
  const headerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (headerRef.current) {
      pageEntrance(headerRef.current, { duration: 450, delay: 60 });
    }
  }, [animateKey]);

  return (
    <div className={cx("w-full", className)}>
      {(title || actions) && (
        <div ref={headerRef} className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            {title && (
              <h1 className="text-2xl font-bold tracking-tight text-[var(--text)] sm:text-3xl">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="mt-1 text-sm text-[var(--text-muted)]">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
