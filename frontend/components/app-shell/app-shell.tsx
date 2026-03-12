"use client";

import type { ReactNode } from "react";

import { Sidebar } from "@/components/app-shell/sidebar";
import { Topbar } from "@/components/app-shell/topbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell-grid">
      <Sidebar />
      <div className="app-surface">
        <Topbar />
        <main className="content-frame page-stack">{children}</main>
      </div>
    </div>
  );
}
