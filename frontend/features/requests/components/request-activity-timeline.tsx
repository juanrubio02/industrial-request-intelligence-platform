import { FileUp, ListChecks, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { interpolate, useI18n } from "@/i18n/hooks";
import type { RequestActivity } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils";

function activityIcon(type: RequestActivity["type"]) {
  if (type === "DOCUMENT_UPLOADED") {
    return FileUp;
  }

  if (type === "STATUS_CHANGED") {
    return ListChecks;
  }

  return Sparkles;
}

function activityVariant(type: RequestActivity["type"]) {
  if (type === "DOCUMENT_UPLOADED") {
    return "info" as const;
  }

  if (type === "STATUS_CHANGED") {
    return "warning" as const;
  }

  return "neutral" as const;
}

export function RequestActivityTimeline({
  activities,
}: {
  activities: RequestActivity[];
}) {
  const { locale, messages } = useI18n();

  return (
    <Card className="h-full">
      <CardHeader>
        <p className="eyebrow">
          {messages.requests.timeline.eyebrow}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <CardTitle>{messages.requests.timeline.title}</CardTitle>
          <Badge variant="neutral" size="sm">
            {interpolate(messages.requests.timeline.events, { count: activities.length })}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {!activities.length ? (
          <div className="rounded-2xl border border-dashed border-line px-6 py-8 text-sm text-slate-600">
            {messages.requests.timeline.empty}
          </div>
        ) : null}
        {activities.map((activity, index) => {
          const Icon = activityIcon(activity.type);
          return (
            <div key={activity.id} className="relative flex gap-4 pl-1">
              {index < activities.length - 1 ? (
                <div className="absolute left-5 top-11 h-[calc(100%-1.5rem)] w-px bg-line" />
              ) : null}
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-control)] bg-surface shadow-soft">
                <Icon className="h-4 w-4 text-slate-600" />
              </div>
              <div className="min-w-0 flex-1 space-y-2 pb-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={activityVariant(activity.type)} size="sm" dot>
                    {messages.requests.activitiesMap[activity.type]}
                  </Badge>
                  <p className="text-sm text-slate-500">
                    {formatDateTime(activity.created_at, locale)}
                  </p>
                </div>
                <pre className="technical-block mt-1 max-h-56">
                  {JSON.stringify(activity.payload, null, 2)}
                </pre>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
