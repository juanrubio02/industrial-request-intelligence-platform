import { apiRequest } from "@/lib/api/client";
import type {
  CreateRequestPayload,
  RequestActivity,
  RequestRecord,
  TransitionRequestStatusPayload,
} from "@/lib/api/types";

export function listRequests(): Promise<RequestRecord[] | null> {
  return apiRequest<RequestRecord[]>("/requests", {
    includeAuth: true,
    includeMembership: true,
  });
}

export function getRequestById(requestId: string): Promise<RequestRecord | null> {
  return apiRequest<RequestRecord>(`/requests/${requestId}`, {
    includeAuth: true,
    includeMembership: true,
    suppressNotFound: true,
  });
}

export function createRequest(payload: CreateRequestPayload): Promise<RequestRecord | null> {
  return apiRequest<RequestRecord>("/requests", {
    method: "POST",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}

export function listRequestActivities(
  requestId: string,
): Promise<RequestActivity[] | null> {
  return apiRequest<RequestActivity[]>(`/requests/${requestId}/activities`, {
    includeAuth: true,
    includeMembership: true,
    suppressNotFound: true,
  });
}

export function transitionRequestStatus(
  requestId: string,
  payload: TransitionRequestStatusPayload,
): Promise<RequestRecord | null> {
  return apiRequest<RequestRecord>(`/requests/${requestId}/status-transitions`, {
    method: "POST",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}
