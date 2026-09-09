"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PageContainer from "@/components/layout/PageContainer";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Loading from "@/components/ui/Loading";
import EmptyState from "@/components/ui/EmptyState";
import ExportButtons from "@/components/reports/ExportButtons";
import { api, ApiError } from "@/lib/api";
import type { ClassItem } from "@/types/class";
import type { DailyReport, MonthlyReport } from "@/types/report";
import { todayISO, currentMonthISO, formatDate } from "@/lib/utils";
import { staggerIn } from "@/animations/index";

type ReportType = "daily" | "monthly";

export default function ReportsPage() {
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [classId, setClassId] = useState("");
  const [type, setType] = useState<ReportType>("daily");
  const [date, setDate] = useState(todayISO());
  const [month, setMonth] = useState(currentMonthISO());
  const [daily, setDaily] = useState<DailyReport | null>(null);
  const [monthly, setMonthly] = useState<MonthlyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [studentNames, setStudentNames] = useState<Record<string, string>>({});
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getClasses({ limit: 100 }).then((r) => {
      const items = r.items ?? [];
      setClasses(items);
      if (items[0]) setClassId(items[0].id);
    }).catch(() => {});
    api.getStudents({ limit: 100 }).then((r) => {
      const map: Record<string, string> = {};
      (r.items ?? []).forEach((st) => {
        map[st.id] = `${st.name} (${st.roll_number})`;
      });
      setStudentNames(map);
    }).catch(() => {});
  }, []);

  const studentName = (id: string) => studentNames[id] ?? id;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (type === "daily") {
        const d = await api.getDailyReport({ class_id: classId || undefined, date });
        setDaily(d);
      } else {
        const m = await api.getMonthlyReport({ class_id: classId || undefined, month });
        setMonthly(m);
      }
    } catch (e) {
      const err = e as ApiError;
      setError(err.message || "Unable to load report.");
    } finally {
      setLoading(false);
    }
  }, [type, classId, date, month]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!loading && gridRef.current) {
      const els = Array.from(gridRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
      staggerIn(els, { duration: 400, stagger: 60 });
    }
  }, [loading, type, daily, monthly]);

  const pct =
    daily && daily.total_records > 0
      ? Math.round((daily.total_present / daily.total_records) * 100)
      : 0;

  const avgPct = monthly && monthly.student_summaries?.length
    ? Math.round(
        monthly.student_summaries.reduce((s, x) => s + (x.attendance_percentage || 0), 0) /
          monthly.student_summaries.length
      )
    : 0;

  return (
    <PageContainer
      title="Reports"
      subtitle="Daily and monthly attendance reporting"
      animateKey={`reports-${type}`}
    >
      <Card className="mb-6 flex flex-col gap-4 p-4 lg:flex-row lg:items-end" variant="glass">
        <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-[var(--text-muted)]">Report Type</span>
            <div className="flex gap-2">
              <button
                className={type === "daily" ? "btn-primary !px-4 !py-2" : "btn-ghost !px-4 !py-2"}
                onClick={() => setType("daily")}
              >
                Daily
              </button>
              <button
                className={type === "monthly" ? "btn-primary !px-4 !py-2" : "btn-ghost !px-4 !py-2"}
                onClick={() => setType("monthly")}
              >
                Monthly
              </button>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]" htmlFor="rep-class">Course</label>
            <select id="rep-class" className="input-base" value={classId} onChange={(e) => setClassId(e.target.value)}>
              <option value="">All Courses</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>{c.name} · {c.section}</option>
              ))}
            </select>
          </div>
          {type === "daily" ? (
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]" htmlFor="rep-date">Date</label>
              <input id="rep-date" type="date" className="input-base" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
          ) : (
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]" htmlFor="rep-month">Month</label>
              <input id="rep-month" type="month" className="input-base" value={month} onChange={(e) => setMonth(e.target.value)} />
            </div>
          )}
          <ExportButtons
            classId={classId || undefined}
            fromDate={type === "daily" ? date : `${month}-01`}
            toDate={type === "daily" ? date : undefined}
          />
        </div>
      </Card>

      {loading ? (
        <Loading message="Loading report..." />
      ) : error ? (
        <EmptyState title="Unable to load report" message={error} />
      ) : type === "daily" && daily ? (
        <div ref={gridRef} className="grid gap-4 sm:grid-cols-2">
          <Card data-stagger className="opacity-0 p-5" variant="glass">
            <p className="text-xs uppercase tracking-wider text-[var(--text-faint)]">Date</p>
            <p className="mt-1 text-lg font-semibold">{formatDate(daily.date)}</p>
            <div className="mt-3">
              <p className="text-xs text-[var(--text-muted)]">Present</p>
              <p className="text-2xl font-bold text-[var(--success)]">{daily.total_present}</p>
            </div>
            <div className="mt-3">
              <p className="text-xs text-[var(--text-muted)]">Absent</p>
              <p className="text-2xl font-bold text-[var(--danger)]">{daily.total_absent}</p>
            </div>
            <div className="mt-3">
              <p className="text-xs text-[var(--text-muted)]">Total Records</p>
              <p className="text-2xl font-bold">{daily.total_records}</p>
            </div>
          </Card>
          <Card data-stagger className="flex flex-col justify-center opacity-0 p-5" variant="glass">
            <p className="text-xs uppercase tracking-wider text-[var(--text-faint)]">Attendance Rate</p>
            <p className="mt-2 text-5xl font-bold text-gradient">{pct}%</p>
            <p className="mt-2 text-sm text-[var(--text-muted)]">{daily.sessions?.length ?? 0} sessions on this day</p>
          </Card>
        </div>
      ) : type === "monthly" && monthly ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <Card data-stagger className="opacity-0 p-5" variant="glass">
              <p className="text-xs uppercase tracking-wider text-[var(--text-faint)]">Month</p>
              <p className="mt-1 text-lg font-semibold">{formatDate(`${monthly.month}-01`)}</p>
            </Card>
            <Card data-stagger className="opacity-0 p-5" variant="glass">
              <p className="text-xs uppercase tracking-wider text-[var(--text-faint)]">Sessions</p>
              <p className="mt-1 text-2xl font-bold">{monthly.total_sessions}</p>
            </Card>
            <Card data-stagger className="opacity-0 p-5" variant="glass">
              <p className="text-xs uppercase tracking-wider text-[var(--text-faint)]">Avg. Attendance</p>
              <p className="mt-1 text-2xl font-bold text-gradient">{avgPct}%</p>
            </Card>
          </div>

          <div ref={gridRef} className="overflow-hidden rounded-2xl border border-[var(--border)]">
            <div className="hidden grid-cols-[1fr_80px_80px_80px_80px_90px] gap-2 border-b border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)] sm:grid">
              <span>Student</span>
              <span>Present</span>
              <span>Absent</span>
              <span>Late</span>
              <span>Excused</span>
              <span>%</span>
            </div>
            {monthly.student_summaries?.length === 0 ? (
              <div className="p-6 text-center text-sm text-[var(--text-muted)]">No data for this month.</div>
            ) : (
              <div className="divide-y divide-[var(--border)]">
                {(monthly.student_summaries ?? []).map((s) => (
                  <div key={s.student_id} data-stagger className="grid grid-cols-[1fr_auto] items-center gap-2 px-4 py-2.5 text-sm opacity-0 sm:grid-cols-[1fr_80px_80px_80px_80px_90px]">
                    <span>{studentName(s.student_id)}</span>
                    <span className="text-[var(--success)]">{s.present}</span>
                    <span className="text-[var(--danger)]">{s.absent}</span>
                    <span className="text-[var(--warning)]">{s.late}</span>
                    <span className="text-[var(--info)]">{s.excused}</span>
                    <Badge variant={s.attendance_percentage >= 75 ? "success" : "warning"}>
                      {s.attendance_percentage}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </PageContainer>
  );
}
