"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import PageContainer from "@/components/layout/PageContainer";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Loading from "@/components/ui/Loading";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import Modal from "@/components/ui/Modal";
import AttendanceRow from "@/components/attendance/AttendanceRow";
import SubjectForm from "@/components/attendance/SubjectForm";
import ClassForm from "@/components/classes/ClassForm";
import { api, ApiError } from "@/lib/api";
import { useAttendance } from "@/hooks/useAttendance";
import { useAuth } from "@/hooks/useAuth";
import type { Student } from "@/types/student";
import type { ClassItem, ClassCreate, ClassUpdate, Subject, SubjectCreate } from "@/types/class";
import type { AttendanceSession } from "@/types/attendance";
import { todayISO, formatDate } from "@/lib/utils";
import { ATTENDANCE_STATUSES } from "@/lib/constants";
import { staggerIn, successPop } from "@/animations/index";
type Step = "setup" | "marking";

export default function AttendancePage() {
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [step, setStep] = useState<Step>("setup");
  const [setupError, setSetupError] = useState<string | null>(null);
  const [showSubjectForm, setShowSubjectForm] = useState(false);
  const [showClassForm, setShowClassForm] = useState(false);
  const [classNameOrigin, setClassNameOrigin] = useState<"main" | "subject">("main");
  const [pendingClassId, setPendingClassId] = useState("");
  const [createFeedback, setCreateFeedback] = useState<string | null>(null);
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [confirmDeleteSession, setConfirmDeleteSession] = useState<AttendanceSession | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const saveRef = useRef<HTMLDivElement>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  const {
    session,
    records,
    counts,
    saving,
    success,
    error,
    createSession,
    seedRecords,
    setStatus,
    markAll,
    save,
    reset,
  } = useAttendance();

  const loadSessions = useCallback(() => {
    setSessionsLoading(true);
    api.getSessions({ limit: 50 })
      .then((r) => setSessions(r.items ?? []))
      .catch(() => setSessions([]))
      .finally(() => setSessionsLoading(false));
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    api.getClasses({ limit: 100 }).then((r) => {
      setClasses(r.items ?? []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    api.getSubjects({ limit: 100 }).then((r) => {
      const items = r.items ?? [];
      setSubjects(items);
      if (items[0]) setSubjectId(items[0].id);
    }).catch(() => setSubjects([]));
  }, []);

  const selectedSubject = subjects.find((s) => s.id === subjectId) ?? null;
  const classId = selectedSubject?.class_id ?? "";

  const handleCreateSubject = async (data: SubjectCreate) => {
    const subj = await api.createSubject(data);
    const next = [...subjects, subj];
    setSubjects(next);
    setSubjectId(subj.id);
    setCreateFeedback(`Subject "${subj.name}" created.`);
  };

  const handleCreateClass = async (data: ClassCreate | ClassUpdate) => {
    const created = await api.createClass(data as ClassCreate);
    const res = await api.getClasses({ limit: 100 });
    setClasses(res.items ?? []);
    setPendingClassId(created.id);
    setShowClassForm(false);
    if (classNameOrigin === "subject") {
      setShowSubjectForm(true);
    }
    setClassNameOrigin("main");
  };

  const handleOpenClassCreate = (origin: "main" | "subject" = "main") => {
    setClassNameOrigin(origin);
    setPendingClassId("");
    setShowSubjectForm(false);
    setShowClassForm(true);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDeleteSession) return;
    setDeleteError(null);
    setDeletingSessionId(confirmDeleteSession.id);
    try {
      await api.deleteAttendanceSession(confirmDeleteSession.id);
      setSessions((prev) => prev.filter((s) => s.id !== confirmDeleteSession.id));
      setDeleteSuccess("Attendance session deleted successfully.");
      setConfirmDeleteSession(null);
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 401) {
        setDeleteError("Your session has expired. Please sign in again.");
      } else if (err.status === 403) {
        setDeleteError("This attendance session does not belong to your account.");
      } else if (err.status === 404) {
        setDeleteError("Attendance session not found.");
      } else if (err.status >= 500) {
        setDeleteError("Unable to delete attendance session. Please try again.");
      } else {
        setDeleteError(err.message || "Unable to delete attendance session. Please try again.");
      }
    } finally {
      setDeletingSessionId(null);
    }
  };

  const startSession = async () => {
    if (!classId || !subjectId) {
      setSetupError("Please select a subject.");
      return;
    }
    setSetupError(null);
    try {
      await createSession({
        class_id: classId,
        subject_id: subjectId,
        date: todayISO(),
        start_time: "09:00",
      });
      loadSessions();
      const res = await api.getStudents({ class_id: classId, limit: 100 });
      setStudents(res.items ?? []);
      seedRecords((res.items ?? []).map((st) => st.id));
      setStep("marking");
    } catch (e) {
      const err = e as ApiError;
      setSetupError(err.message || "Failed to create attendance session.");
    }
  };

  useEffect(() => {
    if (step === "marking" && listRef.current) {
      const els = Array.from(listRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
      staggerIn(els, { duration: 300, stagger: 35 });
    }
  }, [step, records.length]);

  useEffect(() => {
    if (success && saveRef.current) {
      successPop(saveRef.current);
    }
  }, [success]);

  useEffect(() => {
    if (createFeedback && feedbackRef.current) {
      successPop(feedbackRef.current, { color: "rgba(52,211,153,0.18)" });
    }
  }, [createFeedback]);

  useEffect(() => {
    if (deleteSuccess) {
      const t = setTimeout(() => setDeleteSuccess(null), 4000);
      return () => clearTimeout(t);
    }
  }, [deleteSuccess]);

  const handleReset = () => {
    reset();
    setStep("setup");
    setStudents([]);
    loadSessions();
  };

  const subjectName = subjects.find((s) => s.id === subjectId)?.name ?? "";
  const className = classes.find((c) => c.id === classId)?.name ?? "";

  return (
    <PageContainer
      title="Attendance"
      subtitle={step === "marking" ? `${className} · ${formatDate()} · ${subjectName || "Subject"}` : "Create a session to mark attendance"}
      animateKey={`att-${step}`}
    >
      {step === "setup" ? (
        <div className="mx-auto max-w-xl space-y-6">
          <Card className="p-6" variant="glass-strong">
            <h2 className="mb-1 text-lg font-semibold">New Attendance Session</h2>
            <p className="mb-6 text-sm text-[var(--text-muted)]">Select a subject to begin.</p>

            {setupError && (
              <div className="mb-4 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
                {setupError}
              </div>
            )}

            {createFeedback && (
              <div ref={feedbackRef} className="mb-4 rounded-xl border border-[rgba(52,211,153,0.3)] bg-[rgba(52,211,153,0.1)] px-4 py-3 text-sm text-[var(--success)]" role="status">
                {createFeedback}
              </div>
            )}

            <div className="mb-4">
              <div className="mb-1 flex items-center justify-between gap-2">
                <label className="block text-sm font-medium text-[var(--text-muted)]" htmlFor="att-subject">Subject</label>
                <Button variant="ghost" size="sm" className="!px-2.5 !py-1 !text-xs" onClick={() => setShowSubjectForm(true)}>
                  <Icon name="plus" size={14} /> Create Subject
                </Button>
              </div>
              <select id="att-subject" className="input-base" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
                {subjects.length === 0 && <option value="">No subjects available</option>}
                {subjects.length > 0 && !subjectId && <option value="">Select subject</option>}
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.code})</option>
                ))}
              </select>
            </div>

            {classes.length === 0 && (
              <Button variant="ghost" className="w-full" onClick={() => handleOpenClassCreate("main")}>
                <Icon name="plus" size={16} /> Create Course
              </Button>
            )}

            <Button className="mt-6 w-full" size="lg" onClick={startSession} disabled={!subjectId}>
              Start Attendance
            </Button>
          </Card>

          {deleteSuccess && (
            <div className="rounded-xl border border-[rgba(52,211,153,0.3)] bg-[rgba(52,211,153,0.1)] px-4 py-3 text-sm text-[var(--success)]" role="status">
              {deleteSuccess}
            </div>
          )}

          <Card className="p-6" variant="glass-strong">
            <h2 className="mb-1 text-lg font-semibold">Session History</h2>
            <p className="mb-4 text-sm text-[var(--text-muted)]">Previously created attendance sessions.</p>

            {sessionsLoading ? (
              <Loading message="Loading sessions..." />
            ) : sessions.length === 0 ? (
              <p className="py-4 text-center text-sm text-[var(--text-muted)]">No attendance sessions yet.</p>
            ) : (
              <div className="space-y-2">
                {sessions.map((s) => {
                  const subj = subjects.find((sub) => sub.id === s.subject_id);
                  const cls = classes.find((c) => c.id === s.class_id);
                  return (
                    <div
                      key={s.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--border)] px-4 py-3"
                    >
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{subj?.name || "Subject"}</span>
                          {cls && <span className="text-sm text-[var(--text-muted)]">— {cls.name}</span>}
                        </div>
                        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
                          {formatDate(s.date)} · {s.start_time}
                        </p>
                      </div>
                      <Button
                        variant="danger"
                        size="sm"
                        disabled={deletingSessionId === s.id}
                        onClick={() => {
                          setDeleteError(null);
                          setConfirmDeleteSession(s);
                        }}
                      >
                        {deletingSessionId === s.id ? "Deleting..." : "Delete"}
                      </Button>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      ) : session ? (
        <div className="space-y-4">
          <Card className="flex flex-wrap items-center justify-between gap-4 p-4" variant="glass">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold">{subjectName || "Session"}</h2>
                <Badge variant="info">{formatDate()}</Badge>
              </div>
              <p className="mt-0.5 text-sm text-[var(--text-muted)]">{className} · {students.length} students</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => markAll("present")}>Mark All Present</Button>
              <Button variant="ghost" size="sm" onClick={handleReset}>Cancel</Button>
            </div>
          </Card>

          <div ref={listRef} className="space-y-2">
            {records.map((r, i) => {
              const st = students.find((s) => s.id === r.student_id);
              if (!st) return null;
              return (
                <div key={r.key} data-stagger>
                  <AttendanceRow
                    rollNumber={st.roll_number}
                    name={st.name}
                    selected={r.status}
                    onSelect={(status) => setStatus(r.key, status)}
                    index={i}
                  />
                </div>
              );
            })}
          </div>

          <Card className="p-4" variant="glass">
            <AttendanceSummary counts={counts} />
            {error && (
              <div className="mt-3 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
                {error}
              </div>
            )}
            {success && !error && (
              <div ref={saveRef} className="mt-3 rounded-xl border border-[rgba(52,211,153,0.3)] bg-[rgba(52,211,153,0.1)] px-4 py-3 text-sm text-[var(--success)]" role="status">
                Attendance saved successfully!
              </div>
            )}
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Button className="flex-1" size="lg" onClick={save} disabled={saving || records.length === 0}>
                {saving ? "Saving..." : "Save Attendance"}
              </Button>
              <Button variant="ghost" onClick={handleReset}>New Session</Button>
            </div>
          </Card>
        </div>
      ) : (
        <Loading message="Preparing session..." />
      )}

      <SubjectForm
        open={showSubjectForm}
        onClose={() => {
          setShowSubjectForm(false);
          setPendingClassId("");
        }}
        classes={classes}
        teacherId={user?.id ?? ""}
        defaultClassId={pendingClassId}
        onCreateClass={() => handleOpenClassCreate("subject")}
        onSubmit={handleCreateSubject}
      />

      <ClassForm
        open={showClassForm}
        onClose={() => setShowClassForm(false)}
        onSubmit={handleCreateClass}
      />

      <Modal
        open={!!confirmDeleteSession}
        onClose={() => {
          setConfirmDeleteSession(null);
          setDeleteError(null);
        }}
        title="Delete Attendance Session"
      >
        <p className="mb-2 text-sm text-[var(--text-muted)]">
          Are you sure you want to delete this attendance session?
        </p>
        <p className="mb-4 text-sm text-[var(--text-muted)]">
          This will permanently delete the session and all attendance records associated with it.
        </p>

        {deleteError && (
          <div className="mb-4 rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
            {deleteError}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Button
            variant="ghost"
            onClick={() => {
              setConfirmDeleteSession(null);
              setDeleteError(null);
            }}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={deletingSessionId === confirmDeleteSession?.id}
            onClick={handleConfirmDelete}
          >
            {deletingSessionId === confirmDeleteSession?.id ? "Deleting..." : "Delete Session"}
          </Button>
        </div>
      </Modal>
    </PageContainer>
  );
}

function AttendanceSummary({ counts }: { counts: Record<string, number> }) {
  const total = counts.total || 1;
  const pct = Math.round((counts.present / total) * 100);
  return (
    <div>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-faint)]">
          Summary
        </h3>
        <Badge variant="primary">{pct}% present</Badge>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {ATTENDANCE_STATUSES.map((s) => (
          <div key={s.value} className="flex items-center gap-2 rounded-xl border border-[var(--border)] px-3 py-2 text-sm">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            <span className="text-[var(--text-muted)]">{s.label}</span>
            <span className="ml-auto font-bold">{counts[s.value] ?? 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
