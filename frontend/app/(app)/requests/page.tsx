"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RequestListTable } from "@/features/requests/components/request-list-table";
import { useRequestsQuery } from "@/features/requests/api";
import { interpolate, useI18n } from "@/i18n/hooks";

export default function RequestsPage() {
  const requestsQuery = useRequestsQuery();
  const { messages } = useI18n();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={messages.requests.header.eyebrow}
        title={messages.requests.header.title}
        description={messages.requests.header.description}
        actions={
          <>
            {!requestsQuery.isLoading && !requestsQuery.isError ? (
              <Badge variant="neutral" size="sm">
                {interpolate(messages.requests.header.count, {
                  count: (requestsQuery.data ?? []).length,
                })}
              </Badge>
            ) : null}
            <Link
              href="/requests/new"
              className="focus-ring inline-flex h-11 items-center justify-center rounded-[var(--radius-control)] border border-accent bg-accent px-4 text-sm font-medium text-accent-foreground shadow-sm transition hover:brightness-95"
            >
              {messages.requests.header.create}
            </Link>
          </>
        }
      />

      {requestsQuery.isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-[520px] w-full" />
        </div>
      ) : requestsQuery.isError ? (
        <Card>
          <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
            {messages.requests.loadError}
          </CardContent>
        </Card>
      ) : (
        <RequestListTable requests={requestsQuery.data ?? []} />
      )}
    </div>
  );
}
