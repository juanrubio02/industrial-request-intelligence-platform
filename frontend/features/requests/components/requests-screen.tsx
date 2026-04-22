"use client";

import Link from "next/link";
import { useDeferredValue, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRequestsQuery } from "@/features/requests/api";
import { RequestFiltersBar, type RequestListFilterState } from "@/features/requests/components/request-filters-bar";
import { RequestListTable } from "@/features/requests/components/request-list-table";
import { RequestViewToggle, type RequestViewMode } from "@/features/requests/components/request-view-toggle";
import { RequestsPipelineScreen } from "@/features/requests/components/requests-pipeline-screen";
import { useQuery } from "@tanstack/react-query";
import { getOrganizationMembershipOptions } from "@/lib/api/auth";
import { useMembership } from "@/hooks/use-membership";
import { interpolate, useI18n } from "@/i18n/hooks";

const DEFAULT_FILTERS: RequestListFilterState = {
  q: "",
  status: "",
  assigned_membership_id: "",
  source: "",
};

export function RequestsScreen() {
  const { messages } = useI18n();
  const { activeMembership } = useMembership();
  const [filters, setFilters] = useState<RequestListFilterState>(DEFAULT_FILTERS);
  const [view, setView] = useState<RequestViewMode>("list");
  const deferredSearch = useDeferredValue(filters.q);
  const appliedFilters = useMemo(
    () => ({
      q: deferredSearch.trim() || undefined,
      status: filters.status || undefined,
      assigned_membership_id: filters.assigned_membership_id || undefined,
      source: filters.source || undefined,
    }),
    [deferredSearch, filters.assigned_membership_id, filters.source, filters.status],
  );
  const requestsQuery = useRequestsQuery(appliedFilters);
  const membershipsQuery = useQuery({
    queryKey: ["request-filter-memberships", activeMembership?.organization_id ?? null],
    queryFn: async () =>
      activeMembership?.organization_id
        ? (await getOrganizationMembershipOptions(activeMembership.organization_id)) ?? []
        : [],
    enabled: Boolean(activeMembership?.organization_id),
  });
  const hasActiveFilters = Boolean(
    filters.q || filters.status || filters.assigned_membership_id || filters.source,
  );

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

      <RequestFiltersBar
        filters={filters}
        memberships={membershipsQuery.data ?? []}
        onChange={setFilters}
        onReset={() => setFilters(DEFAULT_FILTERS)}
      />

      <div className="flex justify-end">
        <RequestViewToggle
          value={view}
          onChange={setView}
          listLabel={messages.requests.views.list}
          pipelineLabel={messages.requests.views.pipeline}
        />
      </div>

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
        <>
          {view === "list" ? (
            <RequestListTable
              requests={requestsQuery.data ?? []}
              hasActiveFilters={hasActiveFilters}
            />
          ) : (
            <RequestsPipelineScreen
              requests={requestsQuery.data ?? []}
              memberships={membershipsQuery.data ?? []}
              hasActiveFilters={hasActiveFilters}
            />
          )}
        </>
      )}
    </div>
  );
}
