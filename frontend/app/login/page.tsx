"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { TAGLINE } from "@/lib/constants";
import { animateIn } from "@/animations/index";
import Icon from "@/components/ui/Icon";

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth(false);
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const logoRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    animateIn(logoRef.current, { duration: 600, delay: 100 });
    animateIn(formRef.current, { duration: 600, delay: 250 });
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid-bg relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Background vortex */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/2 h-[40rem] w-[40rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(124,106,255,0.14),transparent_60%)]" />
        <svg
          className="absolute left-1/2 top-1/2 h-[36rem] w-[36rem] -translate-x-1/2 -translate-y-1/2 animate-spin-slow text-[var(--primary)]/20"
          viewBox="0 0 500 500"
          fill="none"
          stroke="currentColor"
          aria-hidden="true"
        >
          <circle cx="250" cy="250" r="220" strokeWidth="1" strokeDasharray="3 6" />
          <circle cx="250" cy="250" r="160" strokeWidth="1" strokeDasharray="1 8" />
        </svg>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div ref={logoRef} className="mb-10 flex flex-col items-center text-center" style={{ opacity: 0 }}>
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[rgba(124,106,255,0.15)] text-[var(--primary)]">
            <Icon name="vortex" size={38} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            Attend<span className="text-gradient">Vortex</span>
          </h1>
          <p className="mt-2 text-sm text-[var(--text-muted)]">{TAGLINE}</p>
        </div>

        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className="glass-strong p-7 shadow-2xl"
          style={{ opacity: 0 }}
        >
          <h2 className="mb-1 text-lg font-semibold">Welcome back</h2>
          <p className="mb-6 text-sm text-[var(--text-muted)]">Sign in to continue</p>

          {error && (
            <div
              className="mb-4 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]"
              role="alert"
            >
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-base mb-4"
            placeholder="you@example.com"
            required
          />

          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-base mb-6"
            placeholder="••••••••"
            required
          />

          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <p className="mt-4 text-center text-xs text-[var(--text-faint)]">
            Attendance · Intelligence · In Motion
          </p>
        </form>
      </div>
    </div>
  );
}
