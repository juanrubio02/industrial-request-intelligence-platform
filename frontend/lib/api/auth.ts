import { apiRequest } from "@/lib/api/client";
import type {
  AccessTokenResponse,
  AuthenticatedUser,
  LoginPayload,
  MembershipOption,
} from "@/lib/api/types";

export function login(payload: LoginPayload): Promise<AccessTokenResponse | null> {
  return apiRequest<AccessTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser(): Promise<AuthenticatedUser | null> {
  return apiRequest<AuthenticatedUser>("/auth/me", {
    includeAuth: true,
  });
}

export function getMembershipOptions(): Promise<MembershipOption[] | null> {
  return apiRequest<MembershipOption[]>("/auth/memberships", {
    includeAuth: true,
  });
}
