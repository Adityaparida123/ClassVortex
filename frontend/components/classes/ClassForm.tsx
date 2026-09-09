"use client";

import { FormEvent, useEffect, useState } from "react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import type { ClassItem, ClassCreate, ClassUpdate } from "@/types/class";

interface ClassFormProps {
  open: boolean;
  onClose: () => void;
  editing?: ClassItem | null;
  onSubmit: (data: ClassCreate | ClassUpdate, id?: string) => Promise<void>;
}

export default function ClassForm({ open, onClose, editing, onSubmit }: ClassFormProps) {
  const [name, setName] = useState("");
  const [semester, setSemester] = useState(1);
  const [section, setSection] = useState("A");
  const [academicYear, setAcademicYear] = useState("2026-27");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setError(null);
      if (editing) {
        setName(editing.name);
        setSemester(editing.semester);
        setSection(editing.section);
        setAcademicYear(editing.academic_year);
      } else {
        setName("");
        setSemester(1);
        setSection("A");
        setAcademicYear("2026-27");
      }
    }
  }, [open, editing]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = { name, semester, section, academic_year: academicYear };
      if (editing) {
        await onSubmit(payload, editing.id);
      } else {
        await onSubmit(payload);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save class");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={editing ? "Edit Class" : "Create Class"}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
            {error}
          </div>
        )}
        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="class-name">Course Name</label>
          <input id="class-name" className="input-base" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Computer Science" />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="class-semester">Semester</label>
            <input id="class-semester" type="number" min={1} className="input-base" value={semester} onChange={(e) => setSemester(Number(e.target.value))} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="class-section">Section</label>
            <input id="class-section" className="input-base" value={section} onChange={(e) => setSection(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="class-year">Academic Year</label>
            <input id="class-year" className="input-base" value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} />
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : editing ? "Save Changes" : "Create Class"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
