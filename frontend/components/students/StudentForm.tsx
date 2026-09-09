"use client";

import { FormEvent, useEffect, useState } from "react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import type { Student, StudentCreate, StudentUpdate } from "@/types/student";
import type { ClassItem } from "@/types/class";

interface StudentFormProps {
  open: boolean;
  onClose: () => void;
  classes: ClassItem[];
  editing?: Student | null;
  onSubmit: (data: StudentCreate | StudentUpdate, id?: string) => Promise<void>;
}

export default function StudentForm({
  open,
  onClose,
  classes,
  editing,
  onSubmit,
}: StudentFormProps) {
  const [rollNumber, setRollNumber] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [classId, setClassId] = useState("");
  const [semester, setSemester] = useState(1);
  const [section, setSection] = useState("A");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setError(null);
      if (editing) {
        setRollNumber(editing.roll_number);
        setName(editing.name);
        setEmail(editing.email ?? "");
        setPhone(editing.phone ?? "");
        setClassId(editing.class_id);
        setSemester(editing.semester);
        setSection(editing.section);
      } else {
        setRollNumber("");
        setName("");
        setEmail("");
        setPhone("");
        setClassId(classes[0]?.id ?? "");
        setSemester(1);
        setSection("A");
      }
    }
  }, [open, editing, classes]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (editing) {
        await onSubmit(
          { name, roll_number: rollNumber, email, phone, class_id: classId, semester, section },
          editing.id
        );
      } else {
        await onSubmit({
          roll_number: rollNumber,
          name,
          email,
          phone,
          class_id: classId,
          semester,
          section,
        });
      }
      onClose();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save student";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={editing ? "Edit Student" : "Add Student"}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-name">Name</label>
            <input id="student-name" className="input-base" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-roll">Roll Number</label>
            <input id="student-roll" className="input-base" value={rollNumber} onChange={(e) => setRollNumber(e.target.value)} required />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-email">Email</label>
            <input id="student-email" type="email" className="input-base" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-phone">Phone</label>
            <input id="student-phone" className="input-base" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-class">Course</label>
          <select id="student-class" className="input-base" value={classId} onChange={(e) => setClassId(e.target.value)} required>
            {classes.length === 0 && <option value="">No courses available</option>}
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} · Sem {c.semester} · {c.section}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-semester">Semester</label>
            <input id="student-semester" type="number" min={1} className="input-base" value={semester} onChange={(e) => setSemester(Number(e.target.value))} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-[var(--text-muted)]" htmlFor="student-section">Section</label>
            <input id="student-section" className="input-base" value={section} onChange={(e) => setSection(e.target.value)} />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : editing ? "Save Changes" : "Add Student"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
