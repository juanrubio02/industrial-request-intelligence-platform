import { apiRequest } from "@/lib/api/client";
import type {
  OrganizationMemberRecord,
  UpdateOrganizationMemberRolePayload,
  UpdateOrganizationMemberStatusPayload,
} from "@/lib/api/types";

export function listOrganizationMembers(): Promise<OrganizationMemberRecord[] | null> {
  return apiRequest<OrganizationMemberRecord[]>("/organization/members", {
    includeAuth: true,
    includeMembership: true,
  });
}

export function updateOrganizationMemberRole(
  membershipId: string,
  payload: UpdateOrganizationMemberRolePayload,
): Promise<OrganizationMemberRecord | null> {
  return apiRequest<OrganizationMemberRecord>(`/organization/members/${membershipId}/role`, {
    method: "PATCH",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}

export function updateOrganizationMemberStatus(
  membershipId: string,
  payload: UpdateOrganizationMemberStatusPayload,
): Promise<OrganizationMemberRecord | null> {
  return apiRequest<OrganizationMemberRecord>(`/organization/members/${membershipId}/status`, {
    method: "PATCH",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}
