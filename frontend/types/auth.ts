export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
}
