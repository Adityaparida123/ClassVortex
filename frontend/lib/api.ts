import { TOKEN_STORAGE_KEY } from "./constants";
import type {
  AuthState,
  LoginResponse,
  User,
} from "@/types/auth";
import type {
  Student,
  StudentCreate,
  StudentUpdate,
} from "@/types/student";
import type {
  ClassItem,
  ClassCreate,
  ClassUpdate,
  Subject,
  SubjectCreate,
} from "@/types/class";
import type {
  AttendanceSession,
  AttendanceSessionCreate,
  AttendanceRecord,
  AttendanceRecordBulk,
  StudentSummary,
  AttendanceStatus,
} from "@/types/attendance";
import type {
  DailyReport,
  MonthlyReport,
  StudentReport,
  ClassReport,
} from "@/types/report";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  raw: unknown;
  constructor(message: string, status: number, raw?: unknown) {
    super(message);
    this.status = status;
    this.raw = raw;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

async function request<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    auth?: boolean;
    headers?: Record<string, string>;
  } = {}
): Promise<T> {
  const { method = "GET", body, auth = true, headers = {} } = options;
  const url = `${BASE_URL}${path}`;

  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (auth) {
    const token = getToken();
    if (token) {
      (init.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }
  }

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new ApiError("Network error. Please check your connection.", 0);
  }

  const contentType = res.headers.get("content-type") || "";
  let data: Record<string, unknown> | null = null;
  if (contentType.includes("application/json")) {
    try {
      data = (await res.json()) as Record<string, unknown>;
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const message =
      (data?.detail as string) ??
      ((data?.data as Record<string, unknown>)?.message as string) ??
      res.statusText ??
      "Request failed";
    throw new ApiError(message, res.status, data);
  }

  if (data && typeof data === "object" && "data" in data) {
    return data.data as T;
  }
  return data as T;
}

async function download(path: string): Promise<Blob> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new ApiError("Export failed", res.status);
  }
  return res.blob();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),
  me: () => request<User>("/auth/me"),

  // Students
  getStudents: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    const qs = q.toString();
    return request<{ items: Student[]; total: number; page: number; limit: number }>(
      `/students${qs ? `?${qs}` : ""}`
    );
  },
  getStudent: (id: string) => request<Student>(`/students/${id}`),
  createStudent: (data: StudentCreate) =>
    request<Student>("/students", { method: "POST", body: data }),
  updateStudent: (id: string, data: StudentUpdate) =>
    request<Student>(`/students/${id}`, { method: "PUT", body: data }),
  deleteStudent: (id: string) =>
    request<{ message: string }>(`/students/${id}`, { method: "DELETE" }),

  // Classes
  getClasses: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    const qs = q.toString();
    return request<{ items: ClassItem[]; total: number; page: number; limit: number }>(
      `/classes${qs ? `?${qs}` : ""}`
    );
  },
  getClass: (id: string) => request<ClassItem>(`/classes/${id}`),
  createClass: (data: ClassCreate) =>
    request<ClassItem>("/classes", { method: "POST", body: data }),
  updateClass: (id: string, data: ClassUpdate) =>
    request<ClassItem>(`/classes/${id}`, { method: "PUT", body: data }),
  deleteClass: (id: string) =>
    request<{ message: string }>(`/classes/${id}`, { method: "DELETE" }),

  // Subjects
  getSubjects: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    const qs = q.toString();
    return request<{ items: Subject[]; total: number; page: number; limit: number }>(
      `/subjects${qs ? `?${qs}` : ""}`
    );
  },
  getSubject: (id: string) => request<Subject>(`/subjects/${id}`),
  createSubject: (data: SubjectCreate) =>
    request<Subject>("/subjects", { method: "POST", body: data }),
  updateSubject: (id: string, data: Partial<SubjectCreate>) =>
    request<Subject>(`/subjects/${id}`, { method: "PUT", body: data }),
  deleteSubject: (id: string) =>
    request<{ message: string }>(`/subjects/${id}`, { method: "DELETE" }),

  // Attendance
  createSession: (data: AttendanceSessionCreate) =>
    request<AttendanceSession>("/attendance/sessions", {
      method: "POST",
      body: data,
    }),
  getSessions: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") q.set(k, String(v));
    });
    const qs = q.toString();
    return request<{
      items: AttendanceSession[];
      total: number;
      page: number;
      limit: number;
    }>(`/attendance/sessions${qs ? `?${qs}` : ""}`);
  },
  getSession: (id: string) =>
    request<{ session: AttendanceSession; records: AttendanceRecord[] }>(
      `/attendance/sessions/${id}`
    ),
  bulkMarkAttendance: (sessionId: string, data: AttendanceRecordBulk) =>
    request<AttendanceRecord[]>(`/attendance/sessions/${sessionId}/bulk`, {
      method: "POST",
      body: data,
    }),
  updateRecord: (recordId: string, status: AttendanceStatus) =>
    request<AttendanceRecord>(`/attendance/records/${recordId}`, {
      method: "PUT",
      body: { status },
    }),
  getStudentSummary: (studentId: string) =>
    request<StudentSummary>(`/attendance/student/${studentId}/summary`),

  // Reports
  getDailyReport: (params: { class_id?: string; date?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.class_id) q.set("class_id", params.class_id);
    if (params.date) q.set("date", params.date);
    const qs = q.toString();
    return request<DailyReport>(`/reports/daily${qs ? `?${qs}` : ""}`);
  },
  getMonthlyReport: (params: { class_id?: string; month?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.class_id) q.set("class_id", params.class_id);
    if (params.month) q.set("month", params.month);
    const qs = q.toString();
    return request<MonthlyReport>(`/reports/monthly${qs ? `?${qs}` : ""}`);
  },
  getStudentReport: (studentId: string) =>
    request<StudentReport>(`/reports/student/${studentId}`),
  getClassReport: (classId: string) =>
    request<ClassReport>(`/reports/class/${classId}`),

  // Exports
  exportCSV: async (params: { class_id?: string; from_date?: string; to_date?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.class_id) q.set("class_id", params.class_id);
    if (params.from_date) q.set("from_date", params.from_date);
    if (params.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    const blob = await download(`/exports/attendance/csv${qs ? `?${qs}` : ""}`);
    return triggerDownload(blob, "attendance.csv");
  },
  exportExcel: async (params: { class_id?: string; from_date?: string; to_date?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.class_id) q.set("class_id", params.class_id);
    if (params.from_date) q.set("from_date", params.from_date);
    if (params.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    const blob = await download(
      `/exports/attendance/excel${qs ? `?${qs}` : ""}`
    );
    return triggerDownload(blob, "attendance.xlsx");
  },

  // AI
  chat: (message: string) =>
    request<{ message: string }>("/ai/chat", {
      method: "POST",
      body: { message },
    }),
};

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export type { AuthState };
