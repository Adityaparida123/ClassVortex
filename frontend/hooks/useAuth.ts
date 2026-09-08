"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/context/AuthContext";

/**
 * Protects a page: redirects to /login when unauthenticated.
 * Returns `{ user, loading, isAuthenticated }`.
 */
export function useAuth(requireAuth = true) {
  const { user, token, loading, login, logout, isAuthenticated } =
    useAuthContext();
  const router = useRouter();

  useEffect(() => {
    if (!loading && requireAuth && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, requireAuth, isAuthenticated, router]);

  return { user, token, loading, login, logout, isAuthenticated };
}
