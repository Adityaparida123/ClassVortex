"use client";

import { FormEvent, useEffect, useState } from "react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import type { ClassItem, SubjectCreate } from "@/types/class";

interface SubjectFormProps {
  open: boolean;
  onClose: () => void;
  classes: ClassItem[];
  teacherId: string;
  onSubmit: (data: SubjectCreate) => Promise<void>;
  onCreateClass: () => void;
  defaultClassId?: string;
}

export default function SubjectForm({
  open,
  onClose,
  classes,
  teacherId,
  onSubmit,
  onCreateClass,
  defaultClassId = "",
}: SubjectFormProps) {
  const [selectedClassId, setSelectedClassId] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setError(null);
      setName("");
      setCode("");
      setSelectedClassId(
        defaultClassId || (classes.length === 1 ? classes[0].id : "")
      );
    }
  }, [open, classes, defaultClassId]);

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
    if (classes.length === 0) {
      setError("No courses available. Create a course first.");
      return;
    }
    if (classes.length > 0 && !selectedClassId) {
      setError("Please select a course.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({
        name: trimmedName,
        code: trimmedCode,
        class_id: selectedClassId,
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

  const showClassSelector = classes.length > 1;

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
        {showClassSelector && (
          <div>
            <label
              className="mb-1 block text-sm font-medium text-[var(--text-muted)]"
              htmlFor="subject-class"
            >
              Course
            </label>
            <select
              id="subject-class"
              className="input-base"
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              required
            >
              <option value="">Select course</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} ({cls.section})
                </option>
              ))}
            </select>
          </div>
        )}
        {classes.length === 0 && (
          <div className="space-y-3">
            <div
              className="rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]"
              role="alert"
            >
              No courses available. Create a course first.
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="!px-3 !py-1.5 !text-xs"
              onClick={onCreateClass}
            >
              <Icon name="plus" size={14} /> Create Course
            </Button>
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
          <Button type="submit" disabled={submitting || classes.length === 0}>
            {submitting ? "Creating..." : "Create Subject"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}