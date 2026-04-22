"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RequestStatusBadge } from "@/features/requests/status-badges";
import { interpolate, useI18n } from "@/i18n/hooks";
import type { PipelineAnalytics, RequestStatus } from "@/lib/api/types";

const FUNNEL_STATUSES: RequestStatus[] = [
  "NEW",
  "UNDER_REVIEW",
  "QUOTE_PREPARING",
  "QUOTE_SENT",
  "NEGOTIATION",
  "WON",
];

export function PipelineFunnelChart({
  analytics,
}: {
  analytics: PipelineAnalytics;
}) {
  const { messages } = useI18n();
  const maxCount = Math.max(
    ...FUNNEL_STATUSES.map((status) => analytics.requests_by_status[status] ?? 0),
    1,
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <p className="eyebrow">{messages.dashboard.funnel.eyebrow}</p>
        <CardTitle className="mt-2">{messages.dashboard.funnel.title}</CardTitle>
        <p className="text-sm text-slate-600">{messages.dashboard.funnel.description}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {FUNNEL_STATUSES.map((status, index) => {
          const count = analytics.requests_by_status[status] ?? 0;
          const width = `${Math.max((count / maxCount) * 100, count > 0 ? 24 : 12)}%`;

          return (
            <div key={status} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <RequestStatusBadge status={status} />
                </div>
                <span className="text-sm font-semibold text-slate-700">
                  {interpolate(messages.dashboard.funnel.count, { count })}
                </span>
              </div>
              <div className="rounded-[var(--radius-panel)] bg-slate-100 p-1">
                <div
                  className="flex h-12 items-center rounded-[calc(var(--radius-panel)-6px)] bg-[linear-gradient(135deg,rgba(15,23,42,0.92),rgba(51,65,85,0.86))] px-4 text-sm font-semibold text-white shadow-sm transition-[width]"
                  style={{ width }}
                >
                  {messages.requests.statuses[status]}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
