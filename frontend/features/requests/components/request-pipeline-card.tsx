"use client";

import Link from "next/link";
import { Clock3, Files, MessageSquare, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RequestStatusActions } from "@/features/requests/components/request-status-actions";
import { useI18n } from "@/i18n/hooks";
import type { RequestRecord } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils";

export function RequestPipelineCard({
  request,
  assigneeLabel,
}: {
  request: RequestRecord;
  assigneeLabel: string;
}) {
  const { locale, messages } = useI18n();

  return (
    <Card className="border-line/80 bg-white">
      <CardContent className="space-y-4 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <Badge variant="neutral" size="sm">
              {messages.requests.sources[request.source]}
            </Badge>
            <Link
              href={`/requests/${request.id}`}
              className="mt-3 block text-sm font-semibold leading-5 tracking-[-0.01em] text-slate-900 transition hover:text-accent"
            >
              {request.title}
            </Link>
          </div>
          <Link
            href={`/requests/${request.id}`}
            className="focus-ring inline-flex h-8 shrink-0 items-center justify-center rounded-[var(--radius-control)] px-2 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-slate-600 transition hover:bg-surfaceMuted"
          >
            {messages.requests.pipeline.open}
          </Link>
        </div>

        <div className="space-y-2 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <Clock3 className="h-3.5 w-3.5 text-slate-400" />
            <span>
              {messages.requests.pipeline.updatedLabel}{" "}
              {formatDateTime(request.updated_at, locale)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <UserRound className="h-3.5 w-3.5 text-slate-400" />
            <span>
              {messages.requests.pipeline.assigneeLabel} {assigneeLabel}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="neutral" size="sm">
            <Files className="h-3.5 w-3.5" />
            {messages.requests.pipeline.documentsLabel} {request.documents_count ?? 0}
          </Badge>
          <Badge variant="neutral" size="sm">
            <MessageSquare className="h-3.5 w-3.5" />
            {messages.requests.pipeline.commentsLabel} {request.comments_count ?? 0}
          </Badge>
        </div>

        <RequestStatusActions
          requestId={request.id}
          availableTransitions={request.available_status_transitions ?? []}
          display="select"
        />
      </CardContent>
    </Card>
  );
}
