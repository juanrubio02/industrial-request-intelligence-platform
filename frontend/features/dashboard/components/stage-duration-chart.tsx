"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/i18n/hooks";
import type { PipelineAnalytics, RequestStatus } from "@/lib/api/types";

const STAGE_STATUSES: RequestStatus[] = [
  "NEW",
  "UNDER_REVIEW",
  "QUOTE_PREPARING",
  "QUOTE_SENT",
  "NEGOTIATION",
  "WON",
  "LOST",
];

export function StageDurationChart({
  analytics,
}: {
  analytics: PipelineAnalytics;
}) {
  const { locale, messages } = useI18n();
  const maxDays = Math.max(
    ...STAGE_STATUSES.map((status) => analytics.avg_time_per_stage[status] ?? 0),
    1,
  );
  const numberFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  return (
    <Card>
      <CardHeader>
        <p className="eyebrow">{messages.dashboard.stageDuration.eyebrow}</p>
        <CardTitle className="mt-2">{messages.dashboard.stageDuration.title}</CardTitle>
        <p className="text-sm text-slate-600">{messages.dashboard.stageDuration.description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {STAGE_STATUSES.map((status) => {
          const days = analytics.avg_time_per_stage[status] ?? 0;
          const width = `${Math.max((days / maxDays) * 100, days > 0 ? 10 : 2)}%`;

          return (
            <div key={status} className="grid gap-2 md:grid-cols-[12rem_1fr_5rem] md:items-center">
              <p className="text-sm font-medium text-slate-700">
                {messages.requests.statuses[status]}
              </p>
              <div className="rounded-full bg-slate-100 p-1">
                <div
                  className="h-3 rounded-full bg-[linear-gradient(90deg,rgba(14,116,144,0.92),rgba(59,130,246,0.8))]"
                  style={{ width }}
                />
              </div>
              <p className="text-right text-sm font-semibold text-slate-700">
                {numberFormatter.format(days)} {messages.dashboard.common.daysShort}
              </p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
