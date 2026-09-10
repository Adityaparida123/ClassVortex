"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";
import PageContainer from "@/components/layout/PageContainer";
import AttendanceVortex from "@/components/dashboard/AttendanceVortex";
import { staggerIn, animateIn } from "@/animations/index";
import { cardIn } from "@/animations/cardAnimations";
import { numberCountUp } from "@/animations/numberAnimations";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Loading from "@/components/ui/Loading";
import EmptyState from "@/components/ui/EmptyState";
import { todayISO } from "@/lib/utils";
import type { StudentSummaryRow } from "@/types/report";
interface DashboardData {
  totalStudents: number;
  totalClasses: number;
  presentToday: number;
  absentToday: number;
  totalToday: number;
  overallPct: number;
  todaysSessions: {
    class_id: string;
    subject_id: string;
    date: string;
    start_time: string;
  }[];
}

const EMPTY: DashboardData = {
  totalStudents: 0,
  totalClasses: 0,
  presentToday: 0,
  absentToday: 0,
  totalToday: 0,
  overallPct: 0,
  todaysSessions: [],
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMock, setUsingMock] = useState(false);
  const cardsRef = useRef<HTMLDivElement>(null);
  const todayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);

      const [studentsRes, classesRes, dailyRes] = await Promise.allSettled([
        api.getStudents({ limit: 1 }),
        api.getClasses({ limit: 1 }),
        api.getDailyReport({ date: todayISO() }),
      ]);

      const students = studentsRes.status === "fulfilled" ? studentsRes.value : null;
      const classes = classesRes.status === "fulfilled" ? classesRes.value : null;
      const daily = dailyRes.status === "fulfilled" ? dailyRes.value : null;

      const anyFulfilled = students || classes || daily;
      if (!anyFulfilled && !cancelled) {
        const firstErr =
          studentsRes.status === "rejected"
            ? studentsRes.reason
            : classesRes.status === "rejected"
              ? classesRes.reason
              : dailyRes.status === "rejected"
                ? dailyRes.reason
                : null;
        setError(
          (firstErr as ApiError)?.message || "Unable to load dashboard."
        );
        setUsingMock(true);
        setLoading(false);
        return;
      }

      let overallPct = 0;
      try {
        const monthly = await api.getMonthlyReport({});
        const summaries = monthly.student_summaries ?? [];
        if (summaries.length) {
          overallPct =
            summaries.reduce(
              (s: number, x: StudentSummaryRow) => s + (x.attendance_percentage || 0),
              0,
            ) / summaries.length;
        }
      } catch {
        overallPct = 0;
      }

      if (cancelled) return;
      setData({
        totalStudents: students?.total ?? 0,
        totalClasses: classes?.total ?? 0,
        presentToday: daily?.total_present ?? 0,
        absentToday: daily?.total_absent ?? 0,
        totalToday: daily?.total_records ?? 0,
        overallPct,
        todaysSessions: daily?.sessions ?? [],
      });
      setUsingMock(false);
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!loading && cardsRef.current) {
      const els = Array.from(cardsRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
      staggerIn(els, { duration: 500, stagger: 80 });
    }
  }, [loading]);

  // Animate today's panel in, and its sessions sequentially.
  useEffect(() => {
    if (!loading && todayRef.current) {
      animateIn(todayRef.current, { duration: 500, delay: 250 });
      const sess = Array.from(todayRef.current.querySelectorAll<HTMLElement>("[data-session]"));
      if (sess.length) staggerIn(sess, { duration: 420, stagger: 90, from: "first" });
    }
  }, [loading, data.todaysSessions.length]);

  const firstName = user?.name?.split(" ")[0] ?? "";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const statCards = [
    { label: "Students", value: data.totalStudents, icon: "👥", accent: "var(--primary)" },
    { label: "Courses", value: data.totalClasses, icon: "🗂️", accent: "var(--primary-2)" },
    { label: "Present Today", value: data.presentToday, icon: "✅", accent: "var(--success)" },
    { label: "Absent Today", value: data.absentToday, icon: "🚫", accent: "var(--danger)" },
  ];

  return (
    <PageContainer
      title={`${greeting}${firstName ? `, ${firstName}` : ""}`}
      subtitle={usingMock ? "Dashboard · showing sample data (backend unavailable)" : "Here's today's attendance snapshot"}
      animateKey={`dash-${data.overallPct}`}
    >
      {loading ? (
        <Loading message="Loading dashboard..." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Vortex */}
          <Card className="flex flex-col items-center justify-center p-6 lg:col-span-1" variant="glass-strong">
            <AttendanceVortex
              percentage={data.overallPct}
              label="Attendance"
              subtitle={`${data.totalToday} records today`}
              size={230}
            />
          </Card>

          {/* Stats */}
          <div ref={cardsRef} className="lg:col-span-2">
            <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {statCards.map((s, i) => (
                <StatTile key={s.label} {...s} delay={100 + i * 80} />
              ))}
            </div>

            <div ref={todayRef} className="glass rounded-2xl p-5 opacity-0">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
                  Today&apos;s Sessions
                </h2>
                <Link href="/attendance">
                  <Button size="sm">Take Attendance</Button>
                </Link>
              </div>
              {data.todaysSessions.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  No attendance sessions recorded today.
                </p>
              ) : (
                <div className="space-y-2">
                  {data.todaysSessions.map((s, i) => (
                    <div
                      key={`${s.class_id}-${i}`}
                      data-session
                      className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-4 py-3 opacity-0"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-lg bg-[rgba(124,106,255,0.15)] text-[var(--primary-2)] flex items-center justify-center text-sm font-bold">
                          {s.start_time?.slice(0, 2)}
                        </div>
                        <div>
                          <div className="text-sm font-medium">Course session</div>
                          <div className="text-xs text-[var(--text-muted)]">{s.date}</div>
                        </div>
                      </div>
                      <span className="text-xs text-[var(--text-faint)]">{s.start_time}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {error && !loading && (
        <div className="mt-6">
          <EmptyState
            title="Unable to load dashboard"
            message={error}
            action={
              <button
                className="btn-ghost"
                onClick={() => window.location.reload()}
              >
                Retry
              </button>
            }
          />
        </div>
      )}
    </PageContainer>
  );
}

function StatTile({
  label,
  value,
  icon,
  accent,
  delay,
}: {
  label: string;
  value: number;
  icon: string;
  accent: string;
  delay: number;
}) {
  const [display, setDisplay] = useState(0);
  const numRef = useRef<HTMLSpanElement>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cardIn(ref.current, { duration: 500, delay });
    numberCountUp(0, value, setDisplay, { duration: 900 });
  }, [value, delay]);

  return (
    <div
      ref={ref}
      data-stagger
      className="glass rounded-2xl p-4 opacity-0"
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-faint)]">
          {label}
        </span>
        <span style={{ color: accent }}>{icon}</span>
      </div>
      <p className="text-2xl font-bold text-[var(--text)]">
        <span ref={numRef}>{display}</span>
      </p>
    </div>
  );
}
