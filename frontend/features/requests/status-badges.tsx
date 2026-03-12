import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/hooks";
import type { RequestStatus } from "@/lib/api/types";

const STATUS_VARIANTS: Record<
  RequestStatus,
  "success" | "warning" | "danger" | "neutral" | "info"
> = {
  NEW: "neutral",
  UNDER_REVIEW: "info",
  QUOTE_PREPARING: "warning",
  QUOTE_SENT: "info",
  NEGOTIATION: "warning",
  WON: "success",
  LOST: "danger",
};

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  const { messages } = useI18n();

  return (
    <Badge variant={STATUS_VARIANTS[status]} dot>
      {messages.requests.statuses[status]}
    </Badge>
  );
}
