"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import Icon from "@/components/ui/Icon";
import { cx } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth(false);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-[var(--border)] bg-[rgba(10,10,20,0.6)] backdrop-blur-xl lg:flex">
      <Link href="/dashboard" className="flex items-center gap-3 px-6 py-5">
        <div className="text-[var(--primary)]">
          <Icon name="vortex" size={30} />
        </div>
        <div>
          <div className="text-lg font-bold leading-none">
            Attend<span className="text-gradient">Vortex</span>
          </div>
          <div className="mt-0.5 text-[10px] uppercase tracking-widest text-[var(--text-faint)]">
            Attendance Intelligence
          </div>
        </div>
      </Link>

      <nav className="mt-4 flex-1 space-y-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-[rgba(124,106,255,0.16)] text-[var(--primary-2)]"
                  : "text-[var(--text-muted)] hover:bg-[rgba(255,255,255,0.05)] hover:text-[var(--text)]"
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon name={item.icon} size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[rgba(124,106,255,0.2)] text-sm font-semibold text-[var(--primary-2)]">
            {(user?.name || "?").slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium">{user?.name || "User"}</div>
            <div className="truncate text-xs text-[var(--text-faint)]">{user?.email}</div>
          </div>
          <button
            onClick={logout}
            className="text-[var(--text-faint)] transition-colors hover:text-[var(--danger)]"
            aria-label="Log out"
            title="Log out"
          >
            <Icon name="logout" size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}
