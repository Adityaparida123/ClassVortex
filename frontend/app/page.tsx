"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Loading from "@/components/ui/Loading";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("attendvortex_token");
    router.replace(stored ? "/dashboard" : "/login");
  }, [router]);

  return (
    <div className="grid-bg flex h-screen items-center justify-center">
      <Loading message="AttendVortex..." size="lg" />
    </div>
  );
}
