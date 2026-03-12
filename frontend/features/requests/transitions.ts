import type { RequestStatus } from "@/lib/api/types";

export const REQUEST_STATUS_TRANSITIONS: Record<RequestStatus, RequestStatus[]> = {
  NEW: ["UNDER_REVIEW"],
  UNDER_REVIEW: ["QUOTE_PREPARING"],
  QUOTE_PREPARING: ["QUOTE_SENT"],
  QUOTE_SENT: ["NEGOTIATION", "WON", "LOST"],
  NEGOTIATION: ["WON", "LOST"],
  WON: [],
  LOST: [],
};
