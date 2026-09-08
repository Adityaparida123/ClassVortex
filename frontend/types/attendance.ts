export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export interface AttendanceSession {
  id: string;
  class_id: string;
  subject_id: string;
  teacher_id: string;
  date: string;
  start_time: string;
  status: string;
  created_at?: string;
}

export interface AttendanceSessionCreate {
  class_id: string;
  subject_id: string;
  date: string;
  start_time: string;
}

export interface AttendanceRecord {
  id: string;
  session_id: string;
  student_id: string;
  status: string;
  marked_at?: string;
}

export interface AttendanceRecordBulk {
  records: { student_id: string; status: string }[];
}

export interface StudentSummary {
  student_id: string;
  total_classes: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  attendance_percentage: number;
}
