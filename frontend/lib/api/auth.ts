import { apiRequest } from "@/lib/api/client";
import type {
  AuthenticatedUser,
  LoginResponse,
  LoginPayload,
  MembershipOption,
  OrganizationMembershipOption,
} from "@/lib/api/types";

export function login(payload: LoginPayload): Promise<LoginResponse | null> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<null> {
  return apiRequest<null>("/auth/logout", {
    method: "POST",
    includeAuth: true,
  });
}

export function getCurrentUser(): Promise<AuthenticatedUser | null> {
  return apiRequest<AuthenticatedUser>("/auth/me", {
    includeAuth: true,
    includeOptionalMembership: true,
  });
}

export function getMembershipOptions(): Promise<MembershipOption[] | null> {
  return apiRequest<MembershipOption[]>("/auth/memberships", {
    includeAuth: true,
  });
}

export function getOrganizationMembershipOptions(
  organizationId: string,
): Promise<OrganizationMembershipOption[] | null> {
  return apiRequest<OrganizationMembershipOption[]>(
    `/organizations/${organizationId}/memberships`,
    {
      includeAuth: true,
      includeMembership: true,
    },
  );
}
