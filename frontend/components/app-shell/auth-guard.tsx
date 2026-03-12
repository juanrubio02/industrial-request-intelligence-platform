"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { useMembership } from "@/hooks/use-membership";
import { useI18n } from "@/i18n/hooks";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isBootstrapping } = useAuth();
  const { memberships, isError, isLoading } = useMembership();
  const { messages } = useI18n();

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated && pathname !== "/login") {
      router.replace("/login");
    }
  }, [isAuthenticated, isBootstrapping, pathname, router]);

  if (isBootstrapping || isLoading) {
    return (
      <div className="shell-grid">
        <div className="hidden bg-sidebar lg:block" />
        <div className="app-surface">
          <div className="content-frame space-y-6 py-8">
            <Skeleton className="h-16 w-full" />
            <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
              <Skeleton className="h-[520px] w-full" />
              <Skeleton className="h-[520px] w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (isError) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-xl rounded-3xl border border-line bg-white p-8 shadow-panel">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            {messages.shell.guards.workspaceLoadingFailed}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">
            {messages.shell.guards.workspaceLoadingTitle}
          </h1>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            {messages.shell.guards.workspaceLoadingDescription}
          </p>
        </div>
      </div>
    );
  }

  if (!memberships.length) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-xl rounded-3xl border border-line bg-white p-8 shadow-panel">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            {messages.shell.guards.noWorkspaceEyebrow}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">
            {messages.shell.guards.noWorkspaceTitle}
          </h1>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            {messages.shell.guards.noWorkspaceDescription}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
