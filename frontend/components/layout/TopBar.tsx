"use client";

import Icon from "@/components/ui/Icon";

export default function TopBar() {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--border)] bg-[rgba(10,10,20,0.6)] px-4 py-3 backdrop-blur-xl lg:hidden">
      <div className="flex items-center gap-2">
        <Icon name="vortex" size={22} className="text-[var(--primary)]" />
        <span className="text-base font-bold">
          Attend<span className="text-gradient">Vortex</span>
        </span>
      </div>
      <span className="text-xs text-[var(--text-faint)]">v1.0</span>
    </header>
  );
}
