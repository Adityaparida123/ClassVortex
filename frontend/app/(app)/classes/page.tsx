"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PageContainer from "@/components/layout/PageContainer";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Loading from "@/components/ui/Loading";
import EmptyState from "@/components/ui/EmptyState";
import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Icon from "@/components/ui/Icon";
import ClassForm from "@/components/classes/ClassForm";
import { api, ApiError } from "@/lib/api";
import type { ClassItem, ClassCreate, ClassUpdate } from "@/types/class";
import { staggerIn } from "@/animations/index";

export default function ClassesPage() {
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<ClassItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ClassItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);

  const fetchClasses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getClasses({ limit: 100 });
      setClasses(res.items ?? []);
      const c: Record<string, number> = {};
      await Promise.all(
        (res.items ?? []).map(async (cls) => {
          try {
            const s = await api.getStudents({ class_id: cls.id, limit: 1 });
            c[cls.id] = s.total ?? 0;
          } catch {
            c[cls.id] = 0;
          }
        })
      );
      setCounts(c);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message || "Unable to load classes.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  useEffect(() => {
    if (!loading && gridRef.current) {
      const els = Array.from(gridRef.current.querySelectorAll<HTMLElement>("[data-stagger]"));
      staggerIn(els, { duration: 400, stagger: 60 });
    }
  }, [classes.length, loading]);

  const handleSubmit = async (data: ClassCreate | ClassUpdate, id?: string) => {
    if (id) {
      await api.updateClass(id, data as ClassUpdate);
    } else {
      await api.createClass(data as ClassCreate);
    }
    await fetchClasses();
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteClass(deleteTarget.id);
      setDeleteTarget(null);
      await fetchClasses();
    } catch (e) {
      const err = e as ApiError;
      alert(err.message || "Failed to delete class");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <PageContainer
      title="Classes"
      subtitle={`${classes.length} classes`}
      actions={
        <Button onClick={() => { setEditing(null); setShowForm(true); }}>
          <Icon name="plus" size={16} /> Create Class
        </Button>
      }
      animateKey={`classes-${classes.length}`}
    >
      {loading ? (
        <Loading message="Loading classes..." />
      ) : classes.length === 0 ? (
        <EmptyState
          icon="🗂️"
          title="No classes yet"
          message="Create your first class to start organizing students."
          action={<Button onClick={() => { setEditing(null); setShowForm(true); }}>Create Class</Button>}
        />
      ) : (
        <div ref={gridRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {classes.map((cls) => {
            const count = counts[cls.id] ?? 0;
            return (
              <Card key={cls.id} data-stagger className="opacity-0 p-5" variant="glass">
                <div className="flex items-start justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl text-xl font-bold text-[var(--bg)]" style={{ background: "linear-gradient(135deg, var(--primary-2), var(--primary))" }}>
                    {cls.name.slice(0, 1)}
                  </div>
                  <Badge variant="primary">Sem {cls.semester}</Badge>
                </div>
                <h3 className="mt-4 text-lg font-semibold">{cls.name}</h3>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  Section {cls.section} · {cls.academic_year}
                </p>
                <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3">
                  <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                    <Icon name="users" size={16} /> {count} students
                  </div>
                  <div className="flex gap-2">
                    <button className="btn-ghost !px-2.5 !py-1 !text-xs" onClick={() => { setEditing(cls); setShowForm(true); }}>
                      Edit
                    </button>
                    <button className="btn-ghost !px-2.5 !py-1 !text-xs hover:!text-[var(--danger)]" onClick={() => setDeleteTarget(cls)}>
                      Delete
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {error && !loading && (
        <div className="mt-4">
          <EmptyState title="Unable to load classes" message={error} />
        </div>
      )}

      <ClassForm
        open={showForm}
        onClose={() => setShowForm(false)}
        editing={editing}
        onSubmit={handleSubmit}
      />

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Class">
        <p className="text-sm text-[var(--text-muted)]">
          Delete <strong className="text-[var(--text)]">{deleteTarget?.name}</strong>? This may affect associated students and attendance records.
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
