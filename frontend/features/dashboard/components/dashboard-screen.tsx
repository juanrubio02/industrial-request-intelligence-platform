"use client";

import { EmptyState } from "@/components/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { usePipelineAnalyticsQuery } from "@/features/dashboard/api";
import { BottleneckAlert } from "@/features/dashboard/components/bottleneck-alert";
import { PipelineFunnelChart } from "@/features/dashboard/components/pipeline-funnel-chart";
import { PipelineMetricsCards } from "@/features/dashboard/components/pipeline-metrics-cards";
import { StageDurationChart } from "@/features/dashboard/components/stage-duration-chart";
import { useI18n } from "@/i18n/hooks";

export function DashboardScreen() {
  const analyticsQuery = usePipelineAnalyticsQuery();
  const { messages } = useI18n();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={messages.dashboard.header.eyebrow}
        title={messages.dashboard.header.title}
        description={messages.dashboard.header.description}
      />

      {analyticsQuery.isLoading ? (
        <div className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-36 w-full" />
            ))}
          </div>
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Skeleton className="h-[26rem] w-full" />
            <Skeleton className="h-[26rem] w-full" />
          </div>
          <Skeleton className="h-[26rem] w-full" />
        </div>
      ) : analyticsQuery.isError ? (
        <Card>
          <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
            {messages.dashboard.loadError}
          </CardContent>
        </Card>
      ) : !analyticsQuery.data || analyticsQuery.data.total_requests === 0 ? (
        <EmptyState
          title={messages.dashboard.empty.title}
          description={messages.dashboard.empty.description}
          action={{ label: messages.dashboard.empty.action, href: "/requests/new" }}
        />
      ) : (
        <div className="space-y-6">
          <PipelineMetricsCards analytics={analyticsQuery.data} />

          <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <PipelineFunnelChart analytics={analyticsQuery.data} />
            <BottleneckAlert analytics={analyticsQuery.data} />
          </section>

          <StageDurationChart analytics={analyticsQuery.data} />
        </div>
      )}
    </div>
  );
}
