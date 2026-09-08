"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Student, StudentCreate, StudentUpdate } from "@/types/student";

export interface Category {
  id: string;
  name: string;
  color: string;
}

export function useStudents() {
  const [students, setStudents] = useState<Student[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStudents = useCallback(
    async (params: Record<string, string | number | undefined> = {}) => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getStudents(params);
        setStudents(res.items ?? []);
        setTotal(res.total ?? 0);
      } catch (e) {
        const err = e as ApiError;
        setError(err.message || "Unable to load students.");
        setStudents([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const addStudent = useCallback(async (data: StudentCreate) => {
    const created = await api.createStudent(data);
    await fetchStudents();
    return created;
  }, [fetchStudents]);

  const editStudent = useCallback(
    async (id: string, data: StudentUpdate) => {
      const updated = await api.updateStudent(id, data);
      await fetchStudents();
      return updated;
    },
    [fetchStudents]
  );

  const removeStudent = useCallback(
    async (id: string) => {
      await api.deleteStudent(id);
      await fetchStudents();
    },
    [fetchStudents]
  );

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  return {
    students,
    total,
    loading,
    error,
    fetchStudents,
    addStudent,
    editStudent,
    removeStudent,
  };
}
