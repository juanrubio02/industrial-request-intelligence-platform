"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  listOrganizationMembers,
  updateOrganizationMemberRole,
  updateOrganizationMemberStatus,
} from "@/lib/api/organization-members";
import type {
  UpdateOrganizationMemberRolePayload,
  UpdateOrganizationMemberStatusPayload,
} from "@/lib/api/types";

export const organizationMembersKeys = {
  all: ["organization-members"] as const,
};

export function useOrganizationMembersQuery() {
  return useQuery({
    queryKey: organizationMembersKeys.all,
    queryFn: async () => (await listOrganizationMembers()) ?? [],
  });
}

export function useUpdateOrganizationMemberRoleMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      membershipId,
      payload,
    }: {
      membershipId: string;
      payload: UpdateOrganizationMemberRolePayload;
    }) => updateOrganizationMemberRole(membershipId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: organizationMembersKeys.all }),
        queryClient.invalidateQueries({ queryKey: ["auth", "memberships"] }),
      ]);
    },
  });
}

export function useUpdateOrganizationMemberStatusMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      membershipId,
      payload,
    }: {
      membershipId: string;
      payload: UpdateOrganizationMemberStatusPayload;
    }) => updateOrganizationMemberStatus(membershipId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: organizationMembersKeys.all }),
        queryClient.invalidateQueries({ queryKey: ["auth", "memberships"] }),
      ]);
    },
  });
}
