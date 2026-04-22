"use client";

import { Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import {
  useRequestActivitiesQuery,
  useRequestCommentsQuery,
  useRequestQuery,
} from "@/features/requests/api";
import { RequestStatusBadge } from "@/features/requests/status-badges";
import { RequestStatusActions } from "@/features/requests/components/request-status-actions";
import { RequestActivityTimeline } from "@/features/requests/components/request-activity-timeline";
import { RequestCommentsPanel } from "@/features/requests/components/request-comments-panel";
import { RequestAssignmentCard } from "@/features/requests/components/request-assignment-card";
import { useRequestDocumentsQuery } from "@/features/documents/api";
import { RequestDocumentsPanel } from "@/features/documents/components/request-documents-panel";
import { DocumentUploadCard } from "@/features/documents/components/document-upload-card";
import { useI18n } from "@/i18n/hooks";
import { formatDateTime } from "@/lib/utils";

function InlineQueryError({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800">
      {message}
    </div>
  );
}

export function RequestDetailScreen({ requestId }: { requestId: string }) {
  const requestQuery = useRequestQuery(requestId);
  const activitiesQuery = useRequestActivitiesQuery(requestId);
  const commentsQuery = useRequestCommentsQuery(requestId);
  const documentsQuery = useRequestDocumentsQuery(requestId);
  const { locale, messages } = useI18n();

  if (requestQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-36 w-full" />
        <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <Skeleton className="h-[520px]" />
          <Skeleton className="h-[520px]" />
        </div>
      </div>
    );
  }

  if (requestQuery.isError) {
    return (
        <Card>
        <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
          {messages.requests.detail.loadError}
        </CardContent>
      </Card>
    );
  }

  if (!requestQuery.data) {
    return (
        <Card>
        <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
          {messages.requests.detail.notFound}
        </CardContent>
      </Card>
    );
  }

  const request = requestQuery.data;

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={messages.requests.detail.eyebrow}
        title={request.title}
        description={request.description ?? messages.requests.detail.noDescription}
        actions={
          <>
            <RequestStatusBadge status={request.status} />
            <RequestStatusActions
              requestId={request.id}
              availableTransitions={request.available_status_transitions ?? []}
            />
          </>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Badge variant="neutral" size="sm">
          {messages.requests.detail.source} · {messages.requests.sources[request.source]}
        </Badge>
        <Badge variant="info" size="sm">
          {messages.requests.detail.updated} · {formatDateTime(request.updated_at, locale)}
        </Badge>
        <Badge variant="neutral" size="sm">
          {messages.requests.detail.created} · {formatDateTime(request.created_at, locale)}
        </Badge>
        {!documentsQuery.isError ? (
          <Badge variant="neutral" size="sm">
            {messages.requests.detail.documents} · {(documentsQuery.data ?? []).length}
          </Badge>
        ) : null}
        {!activitiesQuery.isError ? (
          <Badge variant="neutral" size="sm">
            {messages.requests.detail.activities} · {(activitiesQuery.data ?? []).length}
          </Badge>
        ) : null}
      </div>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <p className="eyebrow">
              {messages.requests.detail.requestContextEyebrow}
            </p>
            <CardTitle className="mt-2">{messages.requests.detail.requestContextTitle}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            <div className="surface-muted rounded-[var(--radius-control)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.requests.detail.source}
              </p>
              <p className="mt-2 text-base font-semibold tracking-[-0.01em]">
                {messages.requests.sources[request.source]}
              </p>
            </div>
            <div className="surface-muted rounded-[var(--radius-control)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.requests.detail.lastUpdated}
              </p>
              <p className="mt-2 text-base font-semibold tracking-[-0.01em]">
                {formatDateTime(request.updated_at, locale)}
              </p>
            </div>
            <div className="surface-muted rounded-[var(--radius-control)] p-4 md:col-span-2">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-slate-500" />
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {messages.requests.detail.workflow}
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {messages.requests.detail.workflowDescription}
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <RequestAssignmentCard request={request} />
          <DocumentUploadCard requestId={requestId} />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          {documentsQuery.isError ? (
            <InlineQueryError message={messages.requests.detail.documentsError} />
          ) : null}
          <RequestDocumentsPanel documents={documentsQuery.data ?? []} />
        </div>
        <div className="space-y-4">
          {activitiesQuery.isError ? (
            <InlineQueryError message={messages.requests.detail.timelineError} />
          ) : null}
          <RequestActivityTimeline activities={activitiesQuery.data ?? []} />
        </div>
      </section>

      <RequestCommentsPanel
        requestId={requestId}
        comments={commentsQuery.data ?? []}
        isLoading={Boolean(commentsQuery.isLoading)}
        isError={Boolean(commentsQuery.isError)}
      />
    </div>
  );
}
