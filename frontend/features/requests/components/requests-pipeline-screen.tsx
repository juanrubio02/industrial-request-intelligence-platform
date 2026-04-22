"use client";

import { useMemo } from "react";

import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RequestsPipelineBoard } from "@/features/requests/components/requests-pipeline-board";
import { interpolate, useI18n } from "@/i18n/hooks";
import type { OrganizationMembershipOption, RequestRecord, RequestStatus } from "@/lib/api/types";

const OPEN_PIPELINE_STATUSES: RequestStatus[] = [
  "NEW",
  "UNDER_REVIEW",
  "QUOTE_PREPARING",
  "QUOTE_SENT",
  "NEGOTIATION",
];

export function RequestsPipelineScreen({
  requests,
  memberships,
  hasActiveFilters = false,
}: {
  requests: RequestRecord[];
  memberships: OrganizationMembershipOption[];
  hasActiveFilters?: boolean;
}) {
  const { messages } = useI18n();
  const assigneeByMembershipId = useMemo(
    () =>
      Object.fromEntries(
        memberships.map((membership) => [
          membership.id,
          `${membership.user_full_name} · ${messages.common.memberships[membership.role]}`,
        ]),
      ),
    [memberships, messages.common.memberships],
  );
  const metrics = useMemo(
    () => ({
      total: requests.length,
      open: requests.filter((request) => OPEN_PIPELINE_STATUSES.includes(request.status)).length,
      won: requests.filter((request) => request.status === "WON").length,
      lost: requests.filter((request) => request.status === "LOST").length,
    }),
    [requests],
  );

  if (!requests.length) {
    return (
      <EmptyState
        title={
          hasActiveFilters
            ? messages.requests.list.emptyFilteredTitle
            : messages.requests.list.emptyTitle
        }
        description={
          hasActiveFilters
            ? messages.requests.list.emptyFilteredDescription
            : messages.requests.pipeline.emptyDescription
        }
        action={{ label: messages.requests.list.emptyAction, href: "/requests/new" }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden">
        <CardContent className="grid gap-4 bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.05),_transparent_45%),linear-gradient(135deg,rgba(248,250,252,0.95),rgba(241,245,249,0.9))] px-6 py-5 md:grid-cols-4">
          <div className="space-y-2">
            <p className="eyebrow">{messages.requests.pipeline.eyebrow}</p>
            <p className="text-sm text-slate-600">{messages.requests.pipeline.description}</p>
          </div>
          <div className="rounded-[var(--radius-panel)] border border-white/70 bg-white/80 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {messages.requests.pipeline.metrics.total}
            </p>
            <p className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-slate-950">
              {metrics.total}
            </p>
          </div>
          <div className="rounded-[var(--radius-panel)] border border-white/70 bg-white/80 px-4 py-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {messages.requests.pipeline.metrics.open}
            </p>
            <p className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-slate-950">
              {metrics.open}
            </p>
          </div>
          <div className="flex flex-wrap gap-3 rounded-[var(--radius-panel)] border border-white/70 bg-white/80 px-4 py-4">
            <Badge variant="success" size="sm">
              {interpolate(messages.requests.pipeline.metrics.won, { count: metrics.won })}
            </Badge>
            <Badge variant="danger" size="sm">
              {interpolate(messages.requests.pipeline.metrics.lost, { count: metrics.lost })}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <RequestsPipelineBoard
        requests={requests}
        assigneeByMembershipId={assigneeByMembershipId}
      />
    </div>
  );
}
