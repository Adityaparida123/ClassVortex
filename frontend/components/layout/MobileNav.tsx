"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import Icon from "@/components/ui/Icon";
import { cx } from "@/lib/utils";

export default function MobileNav() {
  const pathname = usePathname();

  // Show only the core items on mobile to keep the bottom bar compact
  const items = NAV_ITEMS.slice(0, 5);

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-[var(--border)] bg-[rgba(10,10,20,0.85)] px-2 py-2 backdrop-blur-xl lg:hidden"
      aria-label="Mobile navigation"
    >
      {items.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cx(
              "flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[10px] transition-colors",
              active
                ? "text-[var(--primary-2)]"
                : "text-[var(--text-faint)] hover:text-[var(--text-muted)]"
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon name={item.icon} size={20} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
