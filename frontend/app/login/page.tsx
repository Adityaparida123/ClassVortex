"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { TAGLINE, DEMO_ACCOUNT } from "@/lib/constants";
import { animateIn, continuousRotate } from "@/animations/index";
import { prefersReducedMotion } from "@/lib/utils";
import Icon from "@/components/ui/Icon";

type CopyTarget = "email" | "password" | null;

export default function LoginPage() {
  const { login, register, isAuthenticated } = useAuth(false);
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("teacher");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<CopyTarget>(null);

  const logoRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const bgRingRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    const reduced = prefersReducedMotion();
    animateIn(logoRef.current, { duration: 600, delay: 100 });
    animateIn(formRef.current, { duration: 600, delay: 250 });
    if (bgRingRef.current && !reduced) {
      continuousRotate(bgRingRef.current, { duration: 48000 });
    }
  }, []);

  useEffect(() => {
    if (!copied) return;
    const t = window.setTimeout(() => setCopied(null), 1500);
    return () => window.clearTimeout(t);
  }, [copied]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await register(name, email, password, role);
      } else {
        await login(email, password);
      }
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message || `${mode === "register" ? "Registration" : "Login"} failed. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (target: Exclude<CopyTarget, null>) => {
    const value = target === "email" ? DEMO_ACCOUNT.email : DEMO_ACCOUNT.password;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        const ta = document.createElement("textarea");
        ta.value = value;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      setCopied(target);
    } catch {
      setCopied(null);
    }
  };

  const toggleMode = () => {
    setError(null);
    setCopied(null);
    setMode((prev) => (prev === "signin" ? "register" : "signin"));
  };

  return (
    <div className="grid-bg relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
      {/* Background vortex */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/2 h-[44rem] w-[44rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(124,106,255,0.14),transparent_60%)]" />
        <svg
          ref={bgRingRef}
          className="absolute left-1/2 top-1/2 h-[42rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 text-[var(--primary)]/20"
          viewBox="0 0 500 500"
          fill="none"
          stroke="currentColor"
          aria-hidden="true"
        >
          <circle cx="250" cy="250" r="220" strokeWidth="1" strokeDasharray="3 6" />
          <circle cx="250" cy="250" r="160" strokeWidth="1" strokeDasharray="1 8" />
          <circle cx="250" cy="250" r="100" strokeWidth="1" strokeDasharray="6 10" />
        </svg>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div ref={logoRef} className="mb-8 flex flex-col items-center text-center" style={{ opacity: 0 }}>
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
          <div className="mb-6 flex rounded-xl bg-[rgba(255,255,255,0.04)] p-1">
            <button
              type="button"
              onClick={() => { setMode("signin"); setError(null); setCopied(null); }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all ${
                mode === "signin"
                  ? "bg-[var(--primary)] text-white shadow-md"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode("register"); setError(null); setCopied(null); }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all ${
                mode === "register"
                  ? "bg-[var(--primary)] text-white shadow-md"
                  : "text-[var(--text-muted)] hover:text-[var(--text)]"
              }`}
            >
              Create Account
            </button>
          </div>

          <h2 className="mb-1 text-lg font-semibold">
            {mode === "register" ? "Create your account" : "Welcome back"}
          </h2>
          <p className="mb-6 text-sm text-[var(--text-muted)]">
            {mode === "register" ? "Join AttendVortex to manage attendance" : "Sign in to continue"}
          </p>

          {error && (
            <div
              className="mb-4 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]"
              role="alert"
            >
              {error}
            </div>
          )}

          {mode === "register" && (
            <>
              <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="name">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-base mb-4"
                placeholder="Dr. Sarah Jenkins"
                required
              />
            </>
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
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-base mb-4"
            placeholder="••••••••"
            required
          />

          {mode === "register" && (
            <>
              <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="role">
                Account Role
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="input-base mb-6"
              >
                <option value="teacher">Teacher</option>
                <option value="admin">Administrator</option>
              </select>
            </>
          )}

          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                {mode === "register" ? "Creating account..." : "Signing in..."}
              </span>
            ) : mode === "register" ? (
              "Create Account"
            ) : (
              "Sign In"
            )}
          </button>

          {mode === "signin" && (
            <>
              <div className="my-5 flex items-center gap-3">
                <div className="h-px flex-1 bg-[var(--border)]" />
                <span className="text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--text-faint)]">
                  Public Demo
                </span>
                <div className="h-px flex-1 bg-[var(--border)]" />
              </div>

              <div className="rounded-xl border border-[var(--border)] bg-[rgba(124,106,255,0.05)] p-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--primary-2)]">
                  Demo Account
                </h3>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  Use these credentials to explore the AttendVortex demo.
                </p>

                {/* Email row */}
                <div className="mt-3.5">
                  <div className="mb-1 flex items-center justify-between">
                    <label className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-faint)]">
                      Email
                    </label>
                  </div>
                  <div className="flex items-stretch gap-2">
                    <div className="flex min-w-0 flex-1 items-center rounded-lg border border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-3 py-2">
                      <span className="truncate text-sm font-mono text-[var(--text)]">
                        {DEMO_ACCOUNT.email}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy("email")}
                      className="btn-ghost shrink-0 px-3 py-2 text-xs"
                      aria-label="Copy demo email"
                    >
                      {copied === "email" ? (
                        <span className="flex items-center gap-1 text-[var(--success)]">
                          <Icon name="check" size={14} />
                          Copied
                        </span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <Icon name="copy" size={14} />
                          Copy Email
                        </span>
                      )}
                    </button>
                  </div>
                </div>

                {/* Password row */}
                <div className="mt-3">
                  <div className="mb-1 flex items-center justify-between">
                    <label className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-faint)]">
                      Password
                    </label>
                  </div>
                  <div className="flex items-stretch gap-2">
                    <div className="flex min-w-0 flex-1 items-center rounded-lg border border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-3 py-2">
                      <span className="truncate text-sm font-mono tracking-tight text-[var(--text)]">
                        {DEMO_ACCOUNT.password}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy("password")}
                      className="btn-ghost shrink-0 px-3 py-2 text-xs"
                      aria-label="Copy demo password"
                    >
                      {copied === "password" ? (
                        <span className="flex items-center gap-1 text-[var(--success)]">
                          <Icon name="check" size={14} />
                          Copied
                        </span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <Icon name="copy" size={14} />
                          Copy Password
                        </span>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-xs text-[var(--primary)] hover:underline"
            >
              {mode === "register"
                ? "Already have an account? Sign in"
                : "Don't have an account? Create an account"}
            </button>
          </div>

          <p className="mt-4 text-center text-xs text-[var(--text-faint)]">
            Attendance · Intelligence · In Motion
          </p>
        </form>
      </div>
    </div>
  );
}
