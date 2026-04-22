"use client";

import { Badge } from "@/components/ui/badge";
import { RequestPipelineCard } from "@/features/requests/components/request-pipeline-card";
import { RequestStatusBadge } from "@/features/requests/status-badges";
import { cn } from "@/lib/utils";
import type { RequestRecord, RequestStatus } from "@/lib/api/types";

const COLUMN_ACCENTS: Record<RequestStatus, string> = {
  NEW: "border-slate-200 bg-slate-50/80",
  UNDER_REVIEW: "border-sky-200 bg-sky-50/80",
  QUOTE_PREPARING: "border-amber-200 bg-amber-50/80",
  QUOTE_SENT: "border-cyan-200 bg-cyan-50/80",
  NEGOTIATION: "border-orange-200 bg-orange-50/80",
  WON: "border-emerald-200 bg-emerald-50/80",
  LOST: "border-rose-200 bg-rose-50/80",
};

export function RequestsPipelineColumn({
  status,
  label,
  requests,
  emptyLabel,
  assigneeByMembershipId,
  unassignedLabel,
}: {
  status: RequestStatus;
  label: string;
  requests: RequestRecord[];
  emptyLabel: string;
  assigneeByMembershipId: Record<string, string>;
  unassignedLabel: string;
}) {
  return (
    <section className="flex min-h-[34rem] min-w-[18rem] flex-col rounded-[var(--radius-panel)] border border-line/70 bg-white/70 p-3 shadow-panel">
      <div className={cn("rounded-[calc(var(--radius-panel)-6px)] border px-4 py-4", COLUMN_ACCENTS[status])}>
        <div className="flex items-center justify-between gap-3">
          <RequestStatusBadge status={status} />
          <Badge variant="neutral" size="sm">
            {requests.length}
          </Badge>
        </div>
        <p className="mt-3 text-sm font-semibold tracking-[-0.01em] text-slate-900">
          {label}
        </p>
      </div>

      <div className="mt-3 flex flex-1 flex-col gap-3">
        {requests.length ? (
          requests.map((request) => (
            <RequestPipelineCard
              key={request.id}
              request={request}
              assigneeLabel={
                request.assigned_membership_id
                  ? assigneeByMembershipId[request.assigned_membership_id] ?? unassignedLabel
                  : unassignedLabel
              }
            />
          ))
        ) : (
          <div className="flex min-h-40 flex-1 items-center justify-center rounded-[var(--radius-panel)] border border-dashed border-line bg-slate-50/70 px-4 text-center text-sm text-slate-500">
            {emptyLabel}
          </div>
        )}
      </div>
    </section>
  );
}
