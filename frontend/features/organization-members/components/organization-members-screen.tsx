"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { OrganizationMembersTable } from "@/features/organization-members/components/organization-members-table";
import {
  useOrganizationMembersQuery,
  useUpdateOrganizationMemberRoleMutation,
  useUpdateOrganizationMemberStatusMutation,
} from "@/features/organization-members/api";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";
import type { MembershipRole, MembershipStatus } from "@/lib/api/types";

export function OrganizationMembersScreen() {
  const { activeMembership, activeOrganization, canManageMembers, refreshMe } = useAuth();
  const { pushToast } = useToast();
  const { messages } = useI18n();
  const membersQuery = useOrganizationMembersQuery();
  const updateRoleMutation = useUpdateOrganizationMemberRoleMutation();
  const updateStatusMutation = useUpdateOrganizationMemberStatusMutation();

  const isUpdating = updateRoleMutation.isPending || updateStatusMutation.isPending;

  async function handleRoleChange(membershipId: string, role: MembershipRole) {
    try {
      await updateRoleMutation.mutateAsync({
        membershipId,
        payload: { role },
      });
      await refreshMe();
      pushToast({
        tone: "success",
        title: messages.organizationMembers.toasts.roleUpdatedTitle,
        description: messages.organizationMembers.toasts.roleUpdatedDescription,
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.organizationMembers.toasts.roleErrorTitle,
        description:
          error instanceof ApiError
            ? error.detail
            : messages.organizationMembers.toasts.fallbackError,
      });
    }
  }

  async function handleStatusChange(membershipId: string, status: MembershipStatus) {
    try {
      await updateStatusMutation.mutateAsync({
        membershipId,
        payload: { status },
      });
      await refreshMe();
      pushToast({
        tone: "success",
        title: messages.organizationMembers.toasts.statusUpdatedTitle,
        description: messages.organizationMembers.toasts.statusUpdatedDescription,
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.organizationMembers.toasts.statusErrorTitle,
        description:
          error instanceof ApiError
            ? error.detail
            : messages.organizationMembers.toasts.fallbackError,
      });
    }
  }

  if (!canManageMembers) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow={messages.organizationMembers.header.eyebrow}
          title={messages.organizationMembers.header.title}
          description={messages.organizationMembers.header.description}
        />
        <Card>
          <CardContent className="px-8 py-10">
            <h2 className="text-xl font-semibold tracking-tight">
              {messages.organizationMembers.noPermission.title}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
              {messages.organizationMembers.noPermission.description}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={messages.organizationMembers.header.eyebrow}
        title={messages.organizationMembers.header.title}
        description={messages.organizationMembers.header.description}
        actions={
          activeOrganization ? (
            <div className="rounded-[var(--radius-control)] border border-line/80 bg-white px-4 py-2.5 shadow-soft">
              <p className="text-sm font-semibold">{activeOrganization.name}</p>
              <p className="text-xs text-slate-500">
                {messages.organizationMembers.header.activeRoleLabel}{" "}
                {activeMembership
                  ? messages.common.memberships[activeMembership.role]
                  : messages.common.labels.notAvailable}
              </p>
            </div>
          ) : null
        }
      />

      {membersQuery.isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-[24rem] w-full" />
        </div>
      ) : membersQuery.isError ? (
        <Card>
          <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
            {messages.organizationMembers.loadError}
          </CardContent>
        </Card>
      ) : !membersQuery.data?.length ? (
        <EmptyState
          title={messages.organizationMembers.empty.title}
          description={messages.organizationMembers.empty.description}
        />
      ) : (
        <OrganizationMembersTable
          canManageMembers={canManageMembers}
          currentMembershipId={activeMembership?.id ?? null}
          isUpdating={isUpdating}
          members={membersQuery.data}
          onRoleChange={handleRoleChange}
          onStatusChange={handleStatusChange}
        />
      )}
    </div>
  );
}
