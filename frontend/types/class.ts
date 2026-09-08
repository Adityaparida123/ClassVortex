export interface ClassItem {
  id: string;
  name: string;
  semester: number;
  section: string;
  academic_year: string;
  is_active: boolean;
  created_at?: string;
}

export interface ClassCreate {
  name: string;
  semester: number;
  section: string;
  academic_year: string;
}

export interface ClassUpdate {
  name?: string;
  semester?: number;
  section?: string;
  academic_year?: string;
  is_active?: boolean;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  class_id: string;
  teacher_id: string;
  is_active: boolean;
  created_at?: string;
}

export interface SubjectCreate {
  name: string;
  code: string;
  class_id: string;
  teacher_id: string;
}
