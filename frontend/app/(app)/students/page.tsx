"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import PageContainer from "@/components/layout/PageContainer";
import Button from "@/components/ui/Button";
import Loading from "@/components/ui/Loading";
import EmptyState from "@/components/ui/EmptyState";
import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import StudentForm from "@/components/students/StudentForm";
import ImportSheetsModal from "@/components/students/ImportSheetsModal";
import { api, ApiError } from "@/lib/api";
import { useStudents } from "@/hooks/useStudents";
import type { Student, StudentCreate, StudentUpdate, ImportPreview } from "@/types/student";
import type { ClassItem } from "@/types/class";
import { staggerIn } from "@/animations/index";

export default function StudentsPage() {
  const { students, total, loading, error, addStudent, editStudent, removeStudent } =
    useStudents();
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Student | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Student | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [pcts, setPcts] = useState<Record<string, number>>({});
  const listRef = useRef<HTMLDivElement>(null);
  const [showImport, setShowImport] = useState(false);
  const [importState, setImportState] = useState<{
    url: string;
    spreadsheetId: string;
    spreadsheetTitle: string;
    sheetName: string;
    autoDetected: boolean;
    columnMapping: { name: string | null; registration_number: string | null; email: string | null };
    headers: string[];
    preview: ImportPreview[];
    summary: { total: number; ready: number; duplicates: number; invalid: number };
    loading: boolean;
    error: string | null;
    importLoading: boolean;
    result: { imported: number; skipped_duplicates: number; invalid: number; details: { row: number; reason: string }[] } | null;
  }>({
    url: "",
    spreadsheetId: "",
    spreadsheetTitle: "",
    sheetName: "",
    autoDetected: false,
    columnMapping: { name: null, registration_number: null, email: null },
    headers: [],
    preview: [],
    summary: { total: 0, ready: 0, duplicates: 0, invalid: 0 },
    loading: false,
    error: null,
    importLoading: false,
    result: null,
  });

  useEffect(() => {
    api.getClasses({ limit: 100 }).then((r) => setClasses(r.items ?? [])).catch(() => {});
    setImportState((prev: any) => ({
      ...prev,
      columnMapping: { name: null, registration_number: null, email: null },
      preview: [],
      summary: { total: 0, ready: 0, duplicates: 0, invalid: 0 },
    }));
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return students;
    const q = search.toLowerCase();
    return students.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.roll_number.toLowerCase().includes(q) ||
        s.email?.toLowerCase().includes(q)
    );
  }, [students, search]);

  useEffect(() => {
    setPcts({});
    const ids = students.slice(0, 40).map((s) => s.id);
    if (ids.length === 0) return;
    Promise.all(ids.map((id) => api.getStudentSummary(id)))
      .then((res) => {
        const map: Record<string, number> = {};
        res.forEach((r, i) => {
          map[ids[i]] = r?.attendance_percentage ?? 0;
        });
        setPcts(map);
      })
      .catch(() => {});
  }, [students]);

  useEffect(() => {
    if (!loading && listRef.current) {
      const els = Array.from(listRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
      staggerIn(els, { duration: 400, stagger: 40 });
    }
  }, [filtered.length, loading]);

  const handleAdd = async (data: StudentCreate | StudentUpdate) => {
    await addStudent(data as StudentCreate);
  };

  const handleEdit = async (data: StudentCreate | StudentUpdate, id?: string) => {
    if (id) await editStudent(id, data as StudentUpdate);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await removeStudent(deleteTarget.id);
      setDeleteTarget(null);
    } catch (e) {
      const err = e as ApiError;
      alert(err.message || "Failed to delete student");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <PageContainer
      title="Students"
      subtitle={`${total} students registered`}
      actions={
        <>
          <Button onClick={() => { setEditing(null); setShowForm(true); }}>
            <Icon name="plus" size={16} /> Add Student
          </Button>
          <ImportSheetsModal
            show={showImport}
            onClose={() => setShowImport(false)}
            setImportState={setImportState}
            importState={importState}
          />
        </>
      }
      animateKey={`students-${students.length}`}
    >
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-faint)]">
            <Icon name="search" size={16} />
          </span>
          <input
            className="input-base !pl-9"
            placeholder="Search by name, roll number, or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <Loading message="Loading students..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="👥"
          title={search ? "No students match your search" : "No students found"}
          message={search ? "Try a different search term." : "Add your first student to get started."}
          action={!search ? (
            <Button onClick={() => { setEditing(null); setShowForm(true); }}>Add Student</Button>
          ) : undefined}
        />
      ) : (
        <div ref={listRef} className="overflow-hidden rounded-2xl border border-[var(--border)]">
          <div className="hidden grid-cols-[70px_1fr_1fr_100px_120px] gap-2 border-b border-[var(--border)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-faint)] sm:grid">
            <span>Roll</span>
            <span>Name</span>
            <span>Class</span>
            <span>Attendance</span>
            <span className="text-right">Actions</span>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {filtered.map((s) => {
              const pct = pcts[s.id] ?? 0;
              const cls = classes.find((c) => c.id === s.class_id);
              return (
                <div
                  key={s.id}
                  data-stagger
                  className="grid grid-cols-[auto_1fr] items-center gap-3 px-4 py-3 opacity-0 transition-colors hover:bg-[rgba(255,255,255,0.03)] sm:grid-cols-[70px_1fr_1fr_100px_120px]"
                >
                  <span className="text-sm font-mono text-[var(--text-faint)] hidden sm:block">{s.roll_number}</span>
                  <span className="flex items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[rgba(124,106,255,0.15)] text-xs font-semibold text-[var(--primary-2)]">
                      {s.name.slice(0, 1).toUpperCase()}
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium">{s.name}</span>
                      <span className="block text-xs text-[var(--text-faint)] sm:hidden">{s.roll_number}</span>
                    </span>
                  </span>
                  <span className="text-sm text-[var(--text-muted)] hidden sm:block">
                    {cls?.name ?? "—"} · {s.section}
                  </span>
                  <span className="hidden sm:block">
                    {pct > 0 ? (
                      <Badge variant={pct >= 75 ? "success" : pct >= 50 ? "warning" : "danger"}>
                        {pct.toFixed(1)}%
                      </Badge>
                    ) : (
                      <span className="text-xs text-[var(--text-faint)]">—</span>
                    )}
                  </span>
                  <span className="flex justify-end gap-2">
                    <button
                      className="btn-ghost !px-2.5 !py-1 !text-xs"
                      onClick={() => { setEditing(s); setShowForm(true); }}
                    >
                      Edit
                    </button>
                    <button
                      className="btn-ghost !px-2.5 !py-1 !text-xs hover:!text-[var(--danger)]"
                      onClick={() => setDeleteTarget(s)}
                    >
                      Delete
                    </button>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {error && !loading && (
        <div className="mt-4">
          <EmptyState title="Unable to load students" message={error} />
        </div>
      )}

      <StudentForm
        open={showForm}
        onClose={() => setShowForm(false)}
        classes={classes}
        editing={editing}
        onSubmit={editing ? handleEdit : handleAdd}
      />

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Student">
        <p className="text-sm text-[var(--text-muted)]">
          Are you sure you want to delete <strong className="text-[var(--text)]">{deleteTarget?.name}</strong>? This action cannot be undone.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleting}>
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </Modal>
    </PageContainer>
  );
}