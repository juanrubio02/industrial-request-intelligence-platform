import { DEFAULT_API_BASE_URL } from "@/lib/constants";
import {
  clearStoredAuthState,
  getStoredActiveMembershipId,
} from "@/lib/session-storage";
import type { ApiErrorShape } from "@/lib/api/types";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

type ApiRequestOptions = RequestInit & {
  includeAuth?: boolean;
  includeMembership?: boolean;
  includeOptionalMembership?: boolean;
  suppressNotFound?: boolean;
};

function buildHeaders(options: ApiRequestOptions): Headers {
  const headers = new Headers(options.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.includeMembership || options.includeOptionalMembership) {
    const membershipId = getStoredActiveMembershipId();
    if (!membershipId) {
      if (options.includeOptionalMembership) {
        return headers;
      }

      throw new ApiError(
        400,
        "An active access context must be selected before this request can be executed.",
      );
    }

    headers.set("X-Membership-Id", membershipId);
  }

  return headers;
}

function handleUnauthorized(): void {
  clearStoredAuthState();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("iri:unauthorized"));
  }
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T | null> {
  const headers = buildHeaders(options);
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    ...options,
    credentials: options.credentials ?? "include",
    headers,
  });

  if (response.status === 401) {
    handleUnauthorized();
  }

  if (options.suppressNotFound && response.status === 404) {
    return null;
  }

  if (!response.ok) {
    let detail = "Unexpected request error.";

    try {
      const payload = (await response.json()) as ApiErrorShape;
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = response.statusText || detail;
    }

    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return null;
  }

  return (await response.json()) as T;
}
