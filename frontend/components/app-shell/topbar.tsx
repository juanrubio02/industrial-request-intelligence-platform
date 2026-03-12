"use client";

import { LogOut, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useMembership } from "@/hooks/use-membership";
import { type Locale, SUPPORTED_LOCALES } from "@/i18n/config";
import { useI18n } from "@/i18n/hooks";

export function Topbar() {
  const { logout, user } = useAuth();
  const { activeMembership, memberships, setActiveMembershipId } = useMembership();
  const { locale, messages, setLocale } = useI18n();

  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-white/84 backdrop-blur-xl">
      <div className="content-frame flex flex-wrap items-center justify-between gap-4 py-4">
        <div className="space-y-2">
          <p className="eyebrow">
            {messages.shell.topbar.workspaceEyebrow}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <div className="min-w-[300px]">
              <Select
                aria-label={messages.shell.topbar.membershipLabel}
                value={activeMembership?.id ?? ""}
                onChange={(event) => setActiveMembershipId(event.target.value)}
              >
                {memberships.map((membership) => (
                  <option key={membership.id} value={membership.id}>
                    {membership.organization_name} · {messages.common.memberships[membership.role]}
                  </option>
                ))}
              </Select>
            </div>
            {activeMembership ? (
              <Badge variant="info" dot>
                <ShieldCheck className="h-3.5 w-3.5" />
                {messages.common.memberships[activeMembership.role]}
              </Badge>
            ) : null}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="min-w-[144px]">
            <Select
              aria-label={messages.language.label}
              value={locale}
              onChange={(event) => setLocale(event.target.value as Locale)}
            >
              {SUPPORTED_LOCALES.map((supportedLocale) => (
                <option key={supportedLocale} value={supportedLocale}>
                  {messages.language.options[supportedLocale]}
                </option>
              ))}
            </Select>
          </div>
          <div className="rounded-[var(--radius-control)] border border-line/80 bg-white px-4 py-2.5 shadow-soft">
            <p className="text-sm font-semibold tracking-[-0.01em]">
              {user?.full_name ?? messages.shell.topbar.userFallback}
            </p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <Button type="button" variant="secondary" onClick={logout}>
            <LogOut className="h-4 w-4" />
            {messages.shell.topbar.signOut}
          </Button>
        </div>
      </div>
    </header>
  );
}
