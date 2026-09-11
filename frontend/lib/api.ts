import { TOKEN_STORAGE_KEY } from "./constants";
import { clearAuth } from "./auth";
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

function getBaseUrl(): string {
  const envUrl = (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    (typeof process !== "undefined" && process.env?.VITE_API_URL) ||
    ""
  ).trim();

  if (!envUrl) return "";
  const cleaned = envUrl.replace(/\/+$/, "");
  if (!cleaned.endsWith("/api/v1")) {
    return `${cleaned}/api/v1`;
  }
  return cleaned;
}

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

let redirectingToLogin = false;

function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  clearAuth();
  if (!redirectingToLogin) {
    redirectingToLogin = true;
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
    window.setTimeout(() => {
      redirectingToLogin = false;
    }, 3000);
  }
}

function friendlyMessage(status: number, detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  switch (status) {
    case 400:
      return "The request could not be processed. Please check your input.";
    case 401:
      return "Your session has expired. Please sign in again.";
    case 403:
      return "You don't have permission to perform this action.";
    case 404:
      return "The requested item was not found.";
    case 409:
      return "This already exists or conflicts with existing data.";
    case 422:
      return "Please check the information you provided and try again.";
    case 500:
      return "Something went wrong on our side. Please try again.";
    default:
      return fallback || "Request failed.";
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const DEFAULT_TIMEOUT_MS = 30000;

async function requestRaw<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    auth?: boolean;
    headers?: Record<string, string>;
    timeoutMs?: number;
  } = {}
): Promise<T> {
  const { method = "GET", body, auth = true, headers = {}, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const baseUrl = getBaseUrl();

  if (!baseUrl) {
    throw new ApiError(
      "API URL is not configured. Set NEXT_PUBLIC_API_URL in your deployment environment variables and redeploy.",
      0
    );
  }

  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (auth) {
    Object.assign(init.headers as Record<string, string>, authHeaders());
  }

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${baseUrl}${path}`, { ...init, signal: controller.signal });
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError(
        "The request timed out. The server did not respond in time. Please try again.",
        0
      );
    }
    throw new ApiError("Network error. Please check your connection.", 0);
  } finally {
    clearTimeout(timeoutId);
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
    if (res.status === 401 && auth) handleUnauthorized();
    const detail = (data as { detail?: unknown } | null)?.detail;
    const fallbackMsg = res.statusText || "Request failed";
    const message = friendlyMessage(res.status, detail, fallbackMsg);
    console.error(`API ${method} ${path} failed`, {
      status: res.status,
      detail,
      data,
    });
    throw new ApiError(message, res.status, data);
  }

  return data as T;
}

async function request<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    auth?: boolean;
    headers?: Record<string, string>;
    timeoutMs?: number;
  } = {}
): Promise<T> {
  const body = await requestRaw<{ success?: boolean; data?: T }>(path, options);
  if (body && typeof body === "object" && "data" in body) {
    return body.data as T;
  }
  return body as T;
}

interface ListEnvelope<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

async function requestList<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    auth?: boolean;
    headers?: Record<string, string>;
  } = {}
): Promise<ListEnvelope<T>> {
  const body = await requestRaw<{
    data?: T[];
    pagination?: { total?: number; page?: number; limit?: number };
  }>(path, options);
  const pagination = body?.pagination ?? {};
  return {
    items: body?.data ?? [],
    total: pagination.total ?? 0,
    page: pagination.page ?? 1,
    limit: pagination.limit ?? 0,
  };
}

function queryString(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") q.set(k, String(v));
  });
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

async function download(path: string): Promise<Blob | null> {
  const baseUrl = getBaseUrl();
  if (!baseUrl) {
    throw new ApiError(
      "API URL is not configured. Set NEXT_PUBLIC_API_URL in your deployment environment variables and redeploy.",
      0
    );
  }
  const res = await fetch(`${baseUrl}${path}`, { headers: authHeaders() });
  const contentType = res.headers.get("content-type") || "";

  if (!res.ok) {
    if (res.status === 401) handleUnauthorized();
    const message = friendlyMessage(res.status, undefined, res.statusText || "Export failed");
    console.error(`API GET ${path} failed`, { status: res.status });
    throw new ApiError(message, res.status);
  }
  if (contentType.includes("application/json")) {
    const j = (await res.json().catch(() => null)) as {
      data?: { message?: string };
    } | null;
    const msg = j?.data?.message;
    if (msg) return null;
    throw new ApiError("Export failed", res.status);
  }
  return res.blob();
}

export const api = {
  // Auth
  register: (name: string, email: string, password: string, role = "teacher") =>
    request<User>("/auth/register", {
      method: "POST",
      body: { name, email, password, role },
      auth: false,
    }),
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    }),
  demoLogin: () =>
    request<LoginResponse>("/auth/demo", {
      method: "POST",
      auth: false,
    }),
  me: () => request<User>("/auth/me"),

  // Students Import
  importSheetsAnalyze: (url: string) =>
    request<{
      spreadsheet_title: string;
      sheet_name: string;
      spreadsheet_id: string;
      headers: string[];
      total_rows: number;
      auto_detected: boolean;
      column_mapping: { k: string | null; v: number | null }[];
      preview: {
        row: number;
        name: string;
        registration_number: string;
        email: string;
        status: string;
        valid: boolean;
      }[];
      summary: { total: number; ready: number; duplicates: number; invalid: number };
    }>("/api/v1/students/import/google-sheets/analyze", {
      method: "POST",
      body: { url },
      auth: false,
    }),
  importSheetsConfirm: (body: {
    spreadsheet_id: string;
    sheet_name: string;
    column_mapping: { name?: string; registration_number?: string; email?: string };
    headers: string[];
    rows: { row: number; name: string; registration_number: string; email: string; status: string; valid: boolean }[];
  }) =>
    request<{
      imported: number;
      skipped_duplicates: number;
      invalid: number;
      details: { row: number; reason: string }[];
    }>("/api/v1/students/import/google-sheets/confirm", {
      method: "POST",
      body,
      auth: false,
    }),

  // Students
  getStudents: (params: Record<string, string | number | undefined> = {}) =>
    requestList<Student>(`/students${queryString(params)}`),
  getStudent: (id: string) => request<Student>(`/students/${id}`),
  createStudent: (data: StudentCreate) =>
    request<Student>("/students", { method: "POST", body: data }),
  updateStudent: (id: string, data: StudentUpdate) =>
    request<Student>(`/students/${id}`, { method: "PUT", body: data }),
  deleteStudent: (id: string) =>
    request<{ message: string }>(`/students/${id}`, { method: "DELETE" }),

  // Classes
  getClasses: (params: Record<string, string | number | undefined> = {}) =>
    requestList<ClassItem>(`/classes${queryString(params)}`),
  getClass: (id: string) => request<ClassItem>(`/classes/${id}`),
  createClass: (data: ClassCreate) =>
    request<ClassItem>("/classes", { method: "POST", body: data }),
  updateClass: (id: string, data: ClassUpdate) =>
    request<ClassItem>(`/classes/${id}`, { method: "PUT", body: data }),
  deleteClass: (id: string) =>
    request<{ message: string }>(`/classes/${id}`, { method: "DELETE" }),

  // Subjects
  getSubjects: (params: Record<string, string | number | undefined> = {}) =>
    requestList<Subject>(`/subjects${queryString(params)}`),
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
  getSessions: (params: Record<string, string | number | undefined> = {}) =>
    requestList<AttendanceSession>(`/attendance/sessions${queryString(params)}`),
  getSession: (id: string) =>
    request<{ session: AttendanceSession; records: AttendanceRecord[] }>(
      `/attendance/sessions/${id}`
    ),
  deleteAttendanceSession: (sessionId: string) =>
    request<{ message: string }>(`/attendance/sessions/${sessionId}`, {
      method: "DELETE",
    }),
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
  exportCSV: async (params: {
    class_id?: string;
    subject_id?: string;
    student_id?: string;
    from_date?: string;
    to_date?: string;
  } = {}): Promise<boolean> => {
    const blob = await download(`/exports/attendance/csv${queryString(params)}`);
    if (!blob) return false;
    triggerDownload(blob, "attendance.csv");
    return true;
  },
  exportExcel: async (params: {
    class_id?: string;
    subject_id?: string;
    student_id?: string;
    from_date?: string;
    to_date?: string;
  } = {}): Promise<boolean> => {
    const blob = await download(`/exports/attendance/excel${queryString(params)}`);
    if (!blob) return false;
    triggerDownload(blob, "attendance.xlsx");
    return true;
  },

  // AI
  chat: (message: string) =>
    request<{
      answer?: string;
      message?: string;
      data?: unknown;
      tool_used?: string | null;
      ai_unavailable?: boolean;
    }>("/ai/chat", {
      method: "POST",
      body: { message },
      timeoutMs: 70000,
    }),
  aiHealth: () =>
    request<{
      available: boolean;
      provider: string;
      model: string;
      reason?: string | null;
    }>("/ai/status", {
      method: "GET",
      auth: false,
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
