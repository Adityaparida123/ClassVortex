export interface DailyReport {
  date: string;
  sessions: AttendanceSession[];
  total_present: number;
  total_absent: number;
  total_records: number;
  total_late?: number;
  total_excused?: number;
}

export interface StudentSummaryRow {
  student_id: string;
  total_classes: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  attendance_percentage: number;
}

export interface MonthlyReport {
  month: string;
  total_sessions: number;
  student_summaries: StudentSummaryRow[];
}

export interface StudentReport {
  student_id: string;
  student_name: string;
  roll_number: string;
  total_classes: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  attendance_percentage: number;
}

export interface ClassReport {
  class_id: string;
  class_name: string;
  total_sessions: number;
  student_summaries: (StudentSummaryRow & {
    student_name: string;
    roll_number: string;
  })[];
}

export interface DashboardSessionRow {
  session_id: string;
  class_id: string;
  class_name: string;
  subject_id: string;
  subject_name: string;
  date: string;
  start_time: string;
}

export interface AttentionStudentRow {
  student_id: string;
  name: string;
  roll_number: string;
  attendance_percentage: number;
}

export interface AttentionClassRow {
  class_id: string;
  name: string;
  attendance_percentage: number;
}

export interface AttentionSubjectRow {
  subject_id: string;
  name: string;
  attendance_percentage: number;
}

export interface DashboardSummary {
  totals: { students: number; classes: number; subjects: number };
  today: {
    date: string;
    present: number;
    absent: number;
    late: number;
    excused: number;
    records: number;
  };
  overall_percentage: number;
  recent_sessions: DashboardSessionRow[];
  attention: {
    students: AttentionStudentRow[];
    classes: AttentionClassRow[];
    subjects: AttentionSubjectRow[];
  };
}

import type { AttendanceSession } from "./attendance";
