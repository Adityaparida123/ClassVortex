"use client";

import { FormEvent, useEffect, useState } from "react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import type { SubjectCreate } from "@/types/class";

interface SubjectFormProps {
  open: boolean;
  onClose: () => void;
  classId: string;
  teacherId: string;
  onSubmit: (data: SubjectCreate) => Promise<void>;
}

export default function SubjectForm({
  open,
  onClose,
  classId,
  teacherId,
  onSubmit,
}: SubjectFormProps) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setError(null);
      setName("");
      setCode("");
    }
  }, [open]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    const trimmedCode = code.trim();

    if (!trimmedName) {
      setError("Subject name is required.");
      return;
    }
    if (!trimmedCode) {
      setError("Subject code is required.");
      return;
    }
    if (!classId) {
      setError("Select a class before creating a subject.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({
        name: trimmedName,
        code: trimmedCode,
        class_id: classId,
        teacher_id: teacherId,
      });
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create subject"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Subject">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div
            className="rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]"
            role="alert"
          >
            {error}
          </div>
        )}
        <div>
          <label
            className="mb-1 block text-sm font-medium text-[var(--text-muted)]"
            htmlFor="subject-name"
          >
            Subject Name
          </label>
          <input
            id="subject-name"
            className="input-base"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g. Data Structures"
            autoFocus
          />
        </div>
        <div>
          <label
            className="mb-1 block text-sm font-medium text-[var(--text-muted)]"
            htmlFor="subject-code"
          >
            Subject Code
          </label>
          <input
            id="subject-code"
            className="input-base"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            placeholder="e.g. CS301"
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create Subject"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}