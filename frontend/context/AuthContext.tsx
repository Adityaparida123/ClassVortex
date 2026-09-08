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
import type { User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
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
      let userInfo: User;
      try {
        userInfo = await api.me();
      } catch {
        userInfo = {
          id: "",
          name: "",
          email,
          role: "teacher",
          is_active: true,
        };
      }
      authStore.saveAuth(res.access_token, userInfo);
      setToken(res.access_token);
      setUser(userInfo);
      router.push("/dashboard");
    },
    [router]
  );

  const logout = useCallback(() => {
    authStore.clearAuth();
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, logout, isAuthenticated: !!token }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  return useContext(AuthContext);
}

export { ApiError };
