"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/context/AuthContext";
import AppShell from "@/components/layout/AppShell";
import Loading from "@/components/ui/Loading";
import VortexBackground from "@/components/background/VortexBackground";

export default function AppLayout({ children }: { children: ReactNode }) {
  const { token, loading } = useAuthContext();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) {
      router.replace("/login");
    }
  }, [loading, token, router]);

  if (loading || !token) {
    return (
      <div className="grid-bg flex h-screen items-center justify-center">
        <Loading message="Loading AttendVortex..." size="lg" />
      </div>
    );
  }

  return (
    <div className="relative min-h-full">
      <VortexBackground />
      <div className="relative z-10">
        <AppShell>{children}</AppShell>
      </div>
    </div>
  );
}
