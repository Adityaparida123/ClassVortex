"use client";

import { ReactNode } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import MobileNav from "./MobileNav";

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full">
      <Sidebar />
      <TopBar />
      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 pb-24 pt-6 sm:px-6 lg:pb-10 lg:pt-8">
          {children}
        </div>
      </main>
      <MobileNav />
    </div>
  );
}
