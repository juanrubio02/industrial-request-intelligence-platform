"use client";

import Link from "next/link";
import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/i18n/hooks";
import type { PipelineAnalytics } from "@/lib/api/types";

export function BottleneckAlert({
  analytics,
}: {
  analytics: PipelineAnalytics;
}) {
  const { locale, messages } = useI18n();
  const numberFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  return (
    <Card className="h-full overflow-hidden">
      <CardHeader>
        <p className="eyebrow">{messages.dashboard.bottlenecks.eyebrow}</p>
        <CardTitle className="mt-2">{messages.dashboard.bottlenecks.title}</CardTitle>
        <p className="text-sm text-slate-600">{messages.dashboard.bottlenecks.description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {analytics.bottlenecks.length ? (
          <>
            {analytics.bottlenecks.map((bottleneck) => (
              <div
                key={bottleneck.status}
                className="rounded-[var(--radius-panel)] border border-amber-200 bg-amber-50 px-4 py-4"
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-4.5 w-4.5 text-amber-700" />
                  <div className="min-w-0">
                    <p className="font-semibold text-amber-950">
                      {messages.requests.statuses[bottleneck.status]}
                    </p>
                    <p className="text-sm text-amber-800">
                      {messages.dashboard.bottlenecks.stageExceeded}{" "}
                      <span className="font-semibold">
                        {numberFormatter.format(bottleneck.avg_days)} {messages.dashboard.common.daysShort}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div className="flex flex-wrap gap-2">
              {analytics.bottlenecks.map((bottleneck) => (
                <Badge key={bottleneck.status} variant="warning" size="sm">
                  {messages.requests.statuses[bottleneck.status]}
                </Badge>
              ))}
            </div>
          </>
        ) : (
          <div className="rounded-[var(--radius-panel)] border border-emerald-200 bg-emerald-50 px-4 py-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-4.5 w-4.5 text-emerald-700" />
              <div>
                <p className="font-semibold text-emerald-950">
                  {messages.dashboard.bottlenecks.healthyTitle}
                </p>
                <p className="text-sm text-emerald-800">
                  {messages.dashboard.bottlenecks.healthyDescription}
                </p>
              </div>
            </div>
          </div>
        )}

        <Link
          href="/requests"
          className="flex items-center justify-between rounded-[var(--radius-panel)] border border-line bg-white px-4 py-4 transition hover:bg-surfaceMuted"
        >
          <div>
            <p className="font-semibold">{messages.dashboard.bottlenecks.ctaTitle}</p>
            <p className="text-sm text-slate-500">{messages.dashboard.bottlenecks.ctaDescription}</p>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-500" />
        </Link>
      </CardContent>
    </Card>
  );
}
