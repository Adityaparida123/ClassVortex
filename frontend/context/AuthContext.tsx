"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import * as authStore from "@/lib/auth";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";
import type { User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = authStore.getAuthState();
    if (stored.token && stored.user) {
      setToken(stored.token);
      setUser(stored.user);
    }
    setLoading(false);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password);
      const token = res.access_token;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
      }
      let userInfo: User;
      try {
        userInfo = await api.me();
      } catch {
        userInfo = {
          id: "",
          name: email.split("@")[0],
          email,
          role: "teacher",
          is_active: true,
        };
      }
      authStore.saveAuth(token, userInfo);
      setToken(token);
      setUser(userInfo);
      router.push("/dashboard");
    },
    [router]
  );

  const register = useCallback(
    async (name: string, email: string, password: string, role = "teacher") => {
      await api.register(name, email, password, role);
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(() => {
    authStore.clearAuth();
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout, isAuthenticated: !!token }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  return useContext(AuthContext);
}

export { ApiError };
