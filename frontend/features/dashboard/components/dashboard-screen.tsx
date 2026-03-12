"use client";

import Link from "next/link";
import { Activity, ArrowRight, CheckCircle2, Layers3 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { useDashboardHealthQuery, useDashboardRequests } from "@/features/dashboard/api";
import { RequestStatusBadge } from "@/features/requests/status-badges";
import { interpolate, useI18n } from "@/i18n/hooks";
import { formatDateTime } from "@/lib/utils";

export function DashboardScreen() {
  const requestsQuery = useDashboardRequests();
  const healthQuery = useDashboardHealthQuery();
  const { locale, messages } = useI18n();

  const requests = requestsQuery.data ?? [];
  const openRequests = requests.filter((request) => !["WON", "LOST"].includes(request.status));
  const latestRequests = requests.slice(0, 5);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={messages.dashboard.header.eyebrow}
        title={messages.dashboard.header.title}
        description={messages.dashboard.header.description}
      />

      <section className="grid gap-4 xl:grid-cols-4">
        <StatCard
          label={messages.dashboard.stats.totalRequests}
          value={String(requests.length)}
          helper={messages.dashboard.stats.totalRequestsHelper}
        />
        <StatCard
          label={messages.dashboard.stats.openPipeline}
          value={String(openRequests.length)}
          helper={messages.dashboard.stats.openPipelineHelper}
        />
        <StatCard
          label={messages.dashboard.stats.systemHealth}
          value={healthQuery.data?.status ?? messages.dashboard.stats.checking}
          helper={
            healthQuery.data
              ? `${healthQuery.data.service} · ${healthQuery.data.environment}`
              : messages.dashboard.stats.systemHealthHelperLoading
          }
        />
        <StatCard
          label={messages.dashboard.stats.recentSignals}
          value={String(latestRequests.length)}
          helper={messages.dashboard.stats.recentSignalsHelper}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.dashboard.recentRequests.eyebrow}
              </p>
              <CardTitle className="mt-2">{messages.dashboard.recentRequests.title}</CardTitle>
            </div>
            <Link href="/requests" className="text-sm font-medium text-accent hover:underline">
              {messages.dashboard.recentRequests.action}
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {requestsQuery.isLoading ? (
              Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-20 w-full" />
              ))
            ) : latestRequests.length ? (
              latestRequests.map((request) => (
                <Link
                  key={request.id}
                  href={`/requests/${request.id}`}
                  className="flex items-center justify-between rounded-2xl border border-line bg-surface/70 px-4 py-4 transition hover:bg-surface"
                >
                  <div className="space-y-1">
                    <p className="font-semibold">{request.title}</p>
                    <p className="text-sm text-slate-500">
                      {formatDateTime(request.updated_at, locale)}
                    </p>
                  </div>
                  <RequestStatusBadge status={request.status} />
                </Link>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-line px-6 py-8 text-sm text-slate-600">
                {messages.dashboard.recentRequests.empty}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.dashboard.systemState.eyebrow}
              </p>
              <CardTitle className="mt-2">{messages.dashboard.systemState.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 rounded-2xl bg-surface px-4 py-4">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <div>
                  <p className="font-semibold">{messages.dashboard.systemState.apiAvailable}</p>
                  <p className="text-sm text-slate-500">
                    {interpolate(messages.dashboard.systemState.apiDescription, {
                      status: healthQuery.data?.status ?? messages.dashboard.systemState.pending,
                    })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl bg-surface px-4 py-4">
                <Layers3 className="h-5 w-5 text-sky-600" />
                <div>
                  <p className="font-semibold">
                    {messages.dashboard.systemState.intelligenceOnline}
                  </p>
                  <p className="text-sm text-slate-500">
                    {messages.dashboard.systemState.intelligenceDescription}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.dashboard.nextStep.eyebrow}
              </p>
              <CardTitle className="mt-2">{messages.dashboard.nextStep.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <Link
                href="/requests/new"
                className="flex items-center justify-between rounded-2xl border border-line bg-white px-4 py-4 transition hover:bg-surfaceMuted"
              >
                <div>
                  <p className="font-semibold">{messages.dashboard.nextStep.actionTitle}</p>
                  <p className="text-sm text-slate-500">
                    {messages.dashboard.nextStep.actionDescription}
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-500" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
