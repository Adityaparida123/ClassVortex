"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import type {
  AttendanceRecordBulk,
  AttendanceStatus,
  AttendanceSession,
  AttendanceSessionCreate,
} from "@/types/attendance";

export interface LocalRecord {
  key: string;
  student_id: string;
  status: AttendanceStatus;
}

export function useAttendance() {
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [records, setRecords] = useState<LocalRecord[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const createSession = useCallback(async (data: AttendanceSessionCreate) => {
    setSuccess(false);
    setError(null);
    const s = await api.createSession(data);
    setSession(s);
    return s;
  }, []);

  const seedRecords = useCallback(
    (studentIds: string[]) => {
      setRecords(
        studentIds.map((id, i) => ({
          key: `s-${i}-${id}`,
          student_id: id,
          status: "present" as AttendanceStatus,
        }))
      );
    },
    []
  );

  const setStatus = useCallback((key: string, status: AttendanceStatus) => {
    setRecords((prev) =>
      prev.map((r) => (r.key === key ? { ...r, status } : r))
    );
  }, []);

  const markAll = useCallback((status: AttendanceStatus) => {
    setRecords((prev) => prev.map((r) => ({ ...r, status })));
  }, []);

  const save = useCallback(async () => {
    if (!session) {
      setError("No active session.");
      return null;
    }
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const payload: AttendanceRecordBulk = {
        records: records.map((r) => ({
          student_id: r.student_id,
          status: r.status,
        })),
      };
      const result = await api.bulkMarkAttendance(session.id, payload);
      setSuccess(true);
      return result;
    } catch (e) {
      const err = e as Error;
      setError(err.message || "Failed to save attendance.");
      return null;
    } finally {
      setSaving(false);
    }
  }, [session, records]);

  const reset = useCallback(() => {
    setSession(null);
    setRecords([]);
    setSuccess(false);
    setError(null);
  }, []);

  const counts = {
    present: records.filter((r) => r.status === "present").length,
    absent: records.filter((r) => r.status === "absent").length,
    late: records.filter((r) => r.status === "late").length,
    excused: records.filter((r) => r.status === "excused").length,
    total: records.length,
  };

  return {
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
  };
}
