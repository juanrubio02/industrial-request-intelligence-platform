"use client";

import { ArrowRightCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { REQUEST_STATUS_TRANSITIONS } from "@/features/requests/transitions";
import { useTransitionRequestStatusMutation } from "@/features/requests/api";
import { useMembership } from "@/hooks/use-membership";
import { useToast } from "@/hooks/use-toast";
import { interpolate, useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";
import type { RequestStatus } from "@/lib/api/types";

export function RequestStatusActions({
  requestId,
  status,
}: {
  requestId: string;
  status: RequestStatus;
}) {
  const { pushToast } = useToast();
  const { activeMembership } = useMembership();
  const mutation = useTransitionRequestStatusMutation(requestId);
  const { messages } = useI18n();
  const availableTransitions = REQUEST_STATUS_TRANSITIONS[status];
  const canTransition = activeMembership?.role === "OWNER" || activeMembership?.role === "ADMIN";

  if (!availableTransitions.length) {
    return null;
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
          onClick={async () => {
            try {
              await mutation.mutateAsync({ new_status: nextStatus });
              pushToast({
                tone: "success",
                title: messages.requests.statusActions.successTitle,
                description: interpolate(messages.requests.statusActions.successDescription, {
                  status: messages.requests.statuses[nextStatus],
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
          }}
        >
          <ArrowRightCircle className="h-4 w-4" />
          {messages.requests.statuses[nextStatus]}
        </Button>
      ))}
    </div>
  );
}
