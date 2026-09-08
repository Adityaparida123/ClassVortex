import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from "./constants";
import type { AuthState, User } from "@/types/auth";

export function saveAuth(token: string, user: User): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function getAuthState(): AuthState {
  if (typeof window === "undefined") {
    return { token: null, user: null };
  }
  return { token: getStoredToken(), user: getStoredUser() };
}
