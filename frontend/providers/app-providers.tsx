"use client";

import type { ReactNode } from "react";

import type { Locale } from "@/i18n/config";
import { I18nProvider } from "@/i18n/provider";
import { AuthProvider } from "@/providers/auth-provider";
import { MembershipProvider } from "@/providers/membership-provider";
import { QueryProvider } from "@/providers/query-provider";
import { ToastProvider } from "@/providers/toast-provider";

export function AppProviders({
  children,
  initialLocale,
}: {
  children: ReactNode;
  initialLocale: Locale;
}) {
  return (
    <QueryProvider>
      <I18nProvider initialLocale={initialLocale}>
        <ToastProvider>
          <AuthProvider>
            <MembershipProvider>{children}</MembershipProvider>
          </AuthProvider>
        </ToastProvider>
      </I18nProvider>
    </QueryProvider>
  );
}
