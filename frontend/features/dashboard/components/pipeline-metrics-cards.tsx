"use client";

import type { ComponentType } from "react";
import { Activity, CirclePercent, Gauge, Target } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/i18n/hooks";
import type { PipelineAnalytics } from "@/lib/api/types";

function formatPercent(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatDays(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(value);
}

export function PipelineMetricsCards({
  analytics,
}: {
  analytics: PipelineAnalytics;
}) {
  const { locale, messages } = useI18n();

  return (
    <section className="grid gap-4 xl:grid-cols-4">
      <PipelineMetricCard
        icon={Activity}
        label={messages.dashboard.kpis.totalRequests}
        value={String(analytics.total_requests)}
        helper={messages.dashboard.kpis.totalRequestsHelper}
      />
      <PipelineMetricCard
        icon={Target}
        label={messages.dashboard.kpis.conversionRate}
        value={formatPercent(analytics.conversion_rate, locale)}
        helper={messages.dashboard.kpis.conversionRateHelper}
      />
      <PipelineMetricCard
        icon={CirclePercent}
        label={messages.dashboard.kpis.lossRate}
        value={formatPercent(analytics.loss_rate, locale)}
        helper={messages.dashboard.kpis.lossRateHelper}
      />
      <PipelineMetricCard
        icon={Gauge}
        label={messages.dashboard.kpis.pipelineVelocity}
        value={`${formatDays(analytics.pipeline_velocity_days, locale)} ${messages.dashboard.common.daysShort}`}
        helper={messages.dashboard.kpis.pipelineVelocityHelper}
      />
    </section>
  );
}

function PipelineMetricCard({
  icon: Icon,
  label,
  value,
  helper,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="relative">
        <div className="absolute right-5 top-5 rounded-2xl border border-line/70 bg-slate-50 p-2.5">
          <Icon className="h-4.5 w-4.5 text-slate-600" />
        </div>
        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {label}
        </p>
        <CardTitle className="max-w-[12rem] text-3xl tracking-[-0.03em]">{value}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-slate-600">{helper}</p>
      </CardContent>
    </Card>
  );
}
