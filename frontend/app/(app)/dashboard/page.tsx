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
import { cx } from "@/lib/utils";
import type {
  DashboardSummary,
  DashboardSessionRow,
  AttentionStudentRow,
  AttentionClassRow,
  AttentionSubjectRow,
} from "@/types/report";

const EMPTY: DashboardSummary = {
  totals: { students: 0, classes: 0, subjects: 0 },
  today: { date: "", present: 0, absent: 0, late: 0, excused: 0, records: 0 },
  overall_percentage: 0,
  recent_sessions: [],
  attention: { students: [], classes: [], subjects: [] },
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardSummary>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMock, setUsingMock] = useState(false);
  const statRef = useRef<HTMLDivElement>(null);
  const todayRef = useRef<HTMLDivElement>(null);
  const sessRef = useRef<HTMLDivElement>(null);
  const attentionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const summary = await api.getDashboard();
        if (!cancelled) {
          setData(summary);
          setUsingMock(false);
          setLoading(false);
        }
        return;
      } catch {
        // Fall back to composing a same-shape summary from individual
        // endpoints so the dashboard still works if /reports/dashboard is
        // not deployed yet.
      }

      const [studentsRes, classesRes, subjectsRes, dailyRes, monthlyRes] =
        await Promise.allSettled([
          api.getStudents({ limit: 1 }),
          api.getClasses({ limit: 1 }),
          api.getSubjects({ limit: 1 }),
          api.getDailyReport({}),
          api.getMonthlyReport({}),
        ]);

      const anyFulfilled = [studentsRes, classesRes, subjectsRes, dailyRes, monthlyRes].some(
        (r) => r.status === "fulfilled"
      );
      if (!anyFulfilled && !cancelled) {
        const firstErr =
          studentsRes.status === "rejected"
            ? studentsRes.reason
            : dailyRes.status === "rejected"
              ? dailyRes.reason
              : null;
        setError((firstErr as ApiError)?.message || "Unable to load dashboard.");
        setUsingMock(true);
        setLoading(false);
        return;
      }

      const daily = dailyRes.status === "fulfilled" ? dailyRes.value : null;
      const monthly = monthlyRes.status === "fulfilled" ? monthlyRes.value : null;
      const summaries = monthly?.student_summaries ?? [];
      const overallPct = summaries.length
        ? summaries.reduce((s, x) => s + (x.attendance_percentage || 0), 0) / summaries.length
        : 0;

      if (!cancelled) {
        setData({
          totals: {
            students: studentsRes.status === "fulfilled" ? studentsRes.value.total : 0,
            classes: classesRes.status === "fulfilled" ? classesRes.value.total : 0,
            subjects: subjectsRes.status === "fulfilled" ? subjectsRes.value.total : 0,
          },
          today: {
            date: daily?.date ?? "",
            present: daily?.total_present ?? 0,
            absent: daily?.total_absent ?? 0,
            late: daily?.total_late ?? 0,
            excused: daily?.total_excused ?? 0,
            records: daily?.total_records ?? 0,
          },
          overall_percentage: Math.round(overallPct * 100) / 100,
          recent_sessions: (daily?.sessions ?? []).map((s) => ({
            session_id: s.id,
            class_id: s.class_id,
            subject_id: s.subject_id,
            class_name: "Course",
            subject_name: "Session",
            date: s.date,
            start_time: s.start_time ?? "",
          })),
          attention: { students: [], classes: [], subjects: [] },
        });
        setUsingMock(false);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Entrance animations (skipped automatically when reduced motion is on).
  useEffect(() => {
    if (!loading) {
      if (statRef.current) {
        const els = Array.from(statRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
        staggerIn(els, { duration: 500, stagger: 80 });
      }
      if (todayRef.current) animateIn(todayRef.current, { duration: 500, delay: 200 });
      if (sessRef.current) {
        animateIn(sessRef.current, { duration: 500, delay: 250 });
        const rows = Array.from(sessRef.current.querySelectorAll<HTMLElement>("[data-session]"));
        if (rows.length) staggerIn(rows, { duration: 420, stagger: 90, from: "first" });
      }
      if (attentionRef.current) animateIn(attentionRef.current, { duration: 500, delay: 300 });
    }
  }, [loading, data.recent_sessions.length]);

  const firstName = user?.name?.split(" ")[0] ?? "";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const dateLabel = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <PageContainer
      title={`${greeting}${firstName ? `, ${firstName}` : ""}`}
      subtitle={
        usingMock
          ? "Dashboard · showing sample data (backend unavailable)"
          : "Here's your attendance overview"
      }
      animateKey={`dash-${data.overall_percentage}`}
    >
      {loading ? (
        <Loading message="Loading dashboard..." />
      ) : (
        <div className="space-y-6">
          {/* Quick actions */}
          <div className="flex flex-wrap items-center gap-3">
            <QuickAction href="/attendance" primary>
              Take Attendance
            </QuickAction>
            <QuickAction href="/students">Add Student</QuickAction>
            <QuickAction href="/classes">Create Subject</QuickAction>
            <QuickAction href="/reports">View Reports</QuickAction>
            <span className="ml-auto hidden text-sm text-[var(--text-muted)] sm:block">
              {dateLabel}
            </span>
          </div>

          {/* Stat tiles */}
          <div ref={statRef} className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatTile label="Students" value={data.totals.students} accent="var(--primary-2)" delay={50} />
            <StatTile label="Classes" value={data.totals.classes} accent="var(--primary)" delay={130} />
            <StatTile label="Subjects" value={data.totals.subjects} accent="var(--info)" delay={210} />
            <StatTile
              label="Today's Attendance"
              value={todayPct(data.today)}
              suffix="%"
              accent="var(--success)"
              delay={290}
            />
          </div>

          {/* Vortex hero + Today's attendance */}
          <div className="grid gap-6 lg:grid-cols-12">
            <Card
              variant="glass-strong"
              className="flex flex-col items-center justify-center gap-3 p-6 lg:col-span-5"
            >
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
                Overall Attendance
              </h2>
              <AttendanceVortex
                percentage={data.overall_percentage}
                label="Attendance"
                subtitle={
                  data.totals.students > 0
                    ? `Across ${data.totals.students} students`
                    : "No data yet"
                }
                size={250}
              />
            </Card>

            <div ref={todayRef} className="glass rounded-2xl p-6 opacity-0 lg:col-span-7">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
                  Today&apos;s Attendance
                </h2>
                <span className="text-xs text-[var(--text-faint)]">{dateLabel}</span>
              </div>
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:gap-10">
                <TodayRing pct={todayPct(data.today)} />
                <div className="grid flex-1 grid-cols-2 gap-3">
                  <TodayCount label="Present" value={data.today.present} tone="var(--success)" />
                  <TodayCount label="Absent" value={data.today.absent} tone="var(--danger)" />
                  <TodayCount label="Late" value={data.today.late} tone="var(--warning)" />
                  <TodayCount label="Excused" value={data.today.excused} tone="var(--info)" />
                </div>
              </div>
              {data.today.records === 0 && (
                <p className="mt-5 text-center text-sm text-[var(--text-muted)]">
                  No attendance recorded yet today.
                </p>
              )}
            </div>
          </div>

          {/* Recent sessions */}
          <div ref={sessRef} className="glass rounded-2xl p-6 opacity-0">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
                Recent Attendance Sessions
              </h2>
              <Link href="/attendance">
                <Button size="sm">View all</Button>
              </Link>
            </div>
            {data.recent_sessions.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">
                No attendance sessions recorded yet.
              </p>
            ) : (
              <div className="space-y-2">
                {data.recent_sessions.map((s) => (
                  <SessionRow key={s.session_id} session={s} />
                ))}
              </div>
            )}
          </div>

          {/* Attention required */}
          <div ref={attentionRef} className="glass rounded-2xl p-6 opacity-0">
            <h2 className="mb-1 text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
              Attention Required
            </h2>
            <p className="mb-4 text-xs text-[var(--text-muted)]">
              Below 75% attendance — automatically detected from live data
            </p>
            <div className="grid gap-6 md:grid-cols-3">
              <AttentionColumn
                title="Students"
                count={data.attention.students.length}
                empty="All students above 75%"
              >
                {data.attention.students.map((s) => (
                  <StudentRow key={s.student_id} student={s} />
                ))}
              </AttentionColumn>
              <AttentionColumn
                title="Classes"
                count={data.attention.classes.length}
                empty="All classes above 75%"
              >
                {data.attention.classes.map((c) => (
                  <ClassRow key={c.class_id} row={c} />
                ))}
              </AttentionColumn>
              <AttentionColumn
                title="Subjects"
                count={data.attention.subjects.length}
                empty="All subjects above 75%"
              >
                {data.attention.subjects.map((s) => (
                  <ClassRow key={s.subject_id} row={s} />
                ))}
              </AttentionColumn>
            </div>
            {(data.attention.students.length + data.attention.classes.length + data.attention.subjects.length) >
              0 && (
              <Link href="/students">
                <Button size="sm" className="mt-5">
                  Review
                </Button>
              </Link>
            )}
          </div>

          {/* AI */}
          <div className="relative overflow-hidden rounded-2xl border border-[rgba(124,106,255,0.35)] bg-[linear-gradient(120deg,rgba(124,106,255,0.16),rgba(87,168,255,0.10))] p-6">
            <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-lg leading-none text-[var(--primary-2)]">✦</span>
                  <h2 className="text-base font-semibold">Ask AttendVortex AI</h2>
                </div>
                <p className="max-w-md text-sm text-[var(--text-muted)]">
                  &quot;Which students are below 75%?&quot;
                </p>
              </div>
              <Link href="/ai">
                <Button>Open AI Assistant</Button>
              </Link>
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
              <button className="btn-ghost" onClick={() => window.location.reload()}>
                Retry
              </button>
            }
          />
        </div>
      )}
    </PageContainer>
  );
}

function todayPct(t: DashboardSummary["today"]): number {
  if (!t.records) return 0;
  return Math.round((t.present / t.records) * 10000) / 100;
}

function QuickAction({
  href,
  children,
  primary,
}: {
  href: string;
  children: React.ReactNode;
  primary?: boolean;
}) {
  return (
    <Link href={href}>
      <Button size="sm" variant={primary ? "primary" : "ghost"}>
        {children}
      </Button>
    </Link>
  );
}

function StatTile({
  label,
  value,
  suffix = "",
  accent,
  delay,
}: {
  label: string;
  value: number;
  suffix?: string;
  accent: string;
  delay: number;
}) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cardIn(ref.current, { duration: 500, delay });
    numberCountUp(0, value, setDisplay, { duration: 900 });
  }, [value, delay]);

  return (
    <div ref={ref} data-stagger className="glass rounded-2xl p-4 opacity-0">
      <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-[var(--text-faint)]">
        {label}
      </span>
      <p className="text-2xl font-bold text-[var(--text)]">
        <span style={{ color: accent }}>{display}</span>
        {suffix && <span className="ml-0.5 text-lg text-[var(--text-muted)]">{suffix}</span>}
      </p>
    </div>
  );
}

function TodayRing({ pct }: { pct: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;
  const tone = pct >= 85 ? "var(--success)" : pct >= 75 ? "var(--warning)" : "var(--danger)";

  return (
    <div className="relative flex flex-col items-center" style={{ width: 108, height: 108 }}>
      <svg className="absolute inset-0" viewBox="0 0 108 108" fill="none" aria-hidden="true">
        <circle cx="54" cy="54" r={radius} stroke="rgba(255,255,255,0.08)" strokeWidth="9" />
        <circle
          cx="54"
          cy="54"
          r={radius}
          stroke={tone}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 54 54)"
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-[var(--text)]">{pct}%</span>
        <span className="text-[10px] uppercase tracking-wider text-[var(--text-faint)]">
          Present
        </span>
      </div>
    </div>
  );
}

function TodayCount({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-4 py-3">
      <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-[var(--text-faint)]">
        {label}
      </span>
      <span className="text-xl font-bold" style={{ color: tone }}>
        {value}
      </span>
    </div>
  );
}

function SessionRow({ session }: { session: DashboardSessionRow }) {
  return (
    <div
      data-session
      className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-4 py-3 opacity-0"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(124,106,255,0.15)] text-[var(--primary-2)]">
          <span className="text-xs font-bold">{session.start_time?.slice(0, 2) || session.date?.slice(5)}</span>
        </div>
        <div>
          <div className="text-sm font-medium">
            {session.class_name}
            <span className="text-[var(--text-faint)]"> · {session.subject_name}</span>
          </div>
          <div className="text-xs text-[var(--text-muted)]">
            {session.date}
            {session.start_time ? ` · ${session.start_time}` : ""}
          </div>
        </div>
      </div>
      <span className="text-xs text-[var(--text-faint)]">{session.start_time}</span>
    </div>
  );
}

function AttentionColumn({
  title,
  count,
  empty,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          {title}
        </h3>
        <span className="rounded-full bg-[rgba(251,191,36,0.14)] px-2 py-0.5 text-[10px] font-semibold text-[var(--warning)]">
          {count}
        </span>
      </div>
      {count === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">{empty}</p>
      ) : (
        <div className="space-y-1.5">{children}</div>
      )}
    </div>
  );
}

function pctTone(pct: number): string {
  if (pct >= 75) return "var(--success)";
  if (pct >= 60) return "var(--warning)";
  return "var(--danger)";
}

function StudentRow({ student }: { student: AttentionStudentRow }) {
  return (
    <div
      className={cx(
        "flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2",
        "bg-[rgba(251,113,133,0.06)]"
      )}
    >
      <div className="min-w-0">
        <div className="truncate text-sm font-medium text-[var(--text)]">{student.name}</div>
        <div className="truncate text-xs text-[var(--text-faint)]">{student.roll_number}</div>
      </div>
      <span className="ml-3 shrink-0 text-sm font-bold" style={{ color: pctTone(student.attendance_percentage) }}>
        {student.attendance_percentage}%
      </span>
    </div>
  );
}

function ClassRow({ row }: { row: AttentionClassRow | AttentionSubjectRow }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[rgba(251,191,36,0.06)] px-3 py-2">
      <span className="truncate text-sm font-medium text-[var(--text)]">{row.name}</span>
      <span className="ml-3 shrink-0 text-sm font-bold" style={{ color: pctTone(row.attendance_percentage) }}>
        {row.attendance_percentage}%
      </span>
    </div>
  );
}