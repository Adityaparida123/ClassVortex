export interface Student {
  id: string;
  roll_number: string;
  name: string;
  email?: string;
  phone?: string;
  class_id: string;
  semester: number;
  section: string;
  is_active: boolean;
  created_at?: string;
}

export interface StudentCreate {
  roll_number: string;
  name: string;
  email?: string;
  phone?: string;
  class_id: string;
  semester: number;
  section: string;
}

export interface StudentUpdate {
  roll_number?: string;
  name?: string;
  email?: string;
  phone?: string;
  class_id?: string;
  semester?: number;
  section?: string;
  is_active?: boolean;
}
