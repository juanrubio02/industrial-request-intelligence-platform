"use client";

import { useState } from "react";
import { ArrowRightCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { useTransitionRequestStatusMutation } from "@/features/requests/api";
import { useMembership } from "@/hooks/use-membership";
import { useToast } from "@/hooks/use-toast";
import { interpolate, useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";
import type { RequestStatus } from "@/lib/api/types";

export function RequestStatusActions({
  requestId,
  availableTransitions,
  display = "buttons",
}: {
  requestId: string;
  availableTransitions: RequestStatus[];
  display?: "buttons" | "select";
}) {
  const { pushToast } = useToast();
  const { activeMembership } = useMembership();
  const mutation = useTransitionRequestStatusMutation(requestId);
  const { messages } = useI18n();
  const [nextStatus, setNextStatus] = useState<RequestStatus | "">("");
  const canTransition = activeMembership?.role === "OWNER" || activeMembership?.role === "ADMIN";

  if (!availableTransitions.length) {
    return null;
  }

  async function handleTransition(targetStatus: RequestStatus) {
    try {
      await mutation.mutateAsync({ new_status: targetStatus });
      setNextStatus("");
      pushToast({
        tone: "success",
        title: messages.requests.statusActions.successTitle,
        description: interpolate(messages.requests.statusActions.successDescription, {
          status: messages.requests.statuses[targetStatus],
        }),
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.requests.statusActions.errorTitle,
        description:
          error instanceof ApiError
            ? error.detail
            : messages.requests.statusActions.fallbackError,
      });
    }
  }

  if (display === "select") {
    return (
      <div className="flex items-center gap-2">
        <Select
          aria-label={messages.requests.pipeline.moveLabel}
          value={nextStatus}
          disabled={!canTransition || mutation.isPending}
          onChange={(event) => setNextStatus(event.target.value as RequestStatus | "")}
          className="h-9 min-w-0 text-xs"
        >
          <option value="">{messages.requests.pipeline.movePlaceholder}</option>
          {availableTransitions.map((targetStatus) => (
            <option key={targetStatus} value={targetStatus}>
              {messages.requests.statuses[targetStatus]}
            </option>
          ))}
        </Select>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={!canTransition || mutation.isPending || !nextStatus}
          onClick={() => {
            if (nextStatus) {
              void handleTransition(nextStatus);
            }
          }}
        >
          {messages.requests.pipeline.moveAction}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {availableTransitions.map((nextStatus) => (
        <Button
          key={nextStatus}
          type="button"
          size="sm"
          variant="secondary"
          disabled={!canTransition || mutation.isPending}
          onClick={() => {
            void handleTransition(nextStatus);
          }}
        >
          <ArrowRightCircle className="h-4 w-4" />
          {messages.requests.statuses[nextStatus]}
        </Button>
      ))}
    </div>
  );
}
