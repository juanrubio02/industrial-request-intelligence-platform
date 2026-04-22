"use client";

import { useMemo } from "react";

import { RequestsPipelineColumn } from "@/features/requests/components/requests-pipeline-column";
import { useI18n } from "@/i18n/hooks";
import type { RequestRecord, RequestStatus } from "@/lib/api/types";

const PIPELINE_STATUSES: RequestStatus[] = [
  "NEW",
  "UNDER_REVIEW",
  "QUOTE_PREPARING",
  "QUOTE_SENT",
  "NEGOTIATION",
  "WON",
  "LOST",
];

export function RequestsPipelineBoard({
  requests,
  assigneeByMembershipId,
}: {
  requests: RequestRecord[];
  assigneeByMembershipId: Record<string, string>;
}) {
  const { messages } = useI18n();
  const groupedRequests = useMemo(() => {
    const emptyGroups = Object.fromEntries(
      PIPELINE_STATUSES.map((status) => [status, [] as RequestRecord[]]),
    ) as Record<RequestStatus, RequestRecord[]>;

    for (const request of requests) {
      emptyGroups[request.status].push(request);
    }

    for (const status of PIPELINE_STATUSES) {
      emptyGroups[status].sort(
        (left, right) =>
          new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime(),
      );
    }

    return emptyGroups;
  }, [requests]);

  return (
    <div className="overflow-x-auto pb-3">
      <div className="flex min-w-[136rem] gap-4">
        {PIPELINE_STATUSES.map((status) => (
          <RequestsPipelineColumn
            key={status}
            status={status}
            label={messages.requests.statuses[status]}
            requests={groupedRequests[status]}
            emptyLabel={messages.requests.pipeline.emptyColumn}
            assigneeByMembershipId={assigneeByMembershipId}
            unassignedLabel={messages.requests.assignment.unassigned}
          />
        ))}
      </div>
    </div>
  );
}
