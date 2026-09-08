export interface DailyReport {
  date: string;
  sessions: AttendanceSession[];
  total_present: number;
  total_absent: number;
  total_records: number;
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

import type { AttendanceSession } from "./attendance";
