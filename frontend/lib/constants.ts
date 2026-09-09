export const APP_NAME = "AttendVortex";
export const TAGLINE = "Attendance. Intelligence. In Motion.";

export const DEMO_MODE: boolean =
  typeof process !== "undefined" &&
  process.env &&
  process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export const DEMO_ACCOUNT = {
  displayName: "AttendVortex Demo Teacher",
  email: "demo@attendvortex.local",
  password: "DemoAttendVortex2026!",
} as const;

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "layout" },
  { href: "/attendance", label: "Attendance", icon: "check" },
  { href: "/students", label: "Students", icon: "users" },
  { href: "/reports", label: "Reports", icon: "chart" },
  { href: "/ai", label: "AI Assistant", icon: "spark" },
] as const;

export const TOKEN_STORAGE_KEY = "attendvortex_token";
export const USER_STORAGE_KEY = "attendvortex_user";

export const ATTENDANCE_STATUSES = [
  { value: "present", label: "Present", color: "#34d399" },
  { value: "absent", label: "Absent", color: "#fb7185" },
  { value: "late", label: "Late", color: "#fbbf24" },
  { value: "excused", label: "Excused", color: "#38bdf8" },
] as const;
