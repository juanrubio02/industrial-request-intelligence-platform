"use client";

import { ShieldCheck } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/hooks";
import type {
  MembershipRole,
  MembershipStatus,
  OrganizationMemberRecord,
} from "@/lib/api/types";

const MANAGEABLE_ROLES: MembershipRole[] = [
  "OWNER",
  "ADMIN",
  "MANAGER",
  "MEMBER",
  "VIEWER",
];

const MANAGEABLE_STATUSES: MembershipStatus[] = ["ACTIVE", "DISABLED"];

export function OrganizationMembersTable({
  canManageMembers,
  currentMembershipId,
  isUpdating,
  members,
  onRoleChange,
  onStatusChange,
}: {
  canManageMembers: boolean;
  currentMembershipId: string | null;
  isUpdating: boolean;
  members: OrganizationMemberRecord[];
  onRoleChange: (membershipId: string, role: MembershipRole) => void;
  onStatusChange: (membershipId: string, status: MembershipStatus) => void;
}) {
  const { locale, messages } = useI18n();
  const dateFormatter = new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{messages.organizationMembers.table.columns.member}</TableHead>
          <TableHead>{messages.organizationMembers.table.columns.role}</TableHead>
          <TableHead>{messages.organizationMembers.table.columns.status}</TableHead>
          <TableHead>{messages.organizationMembers.table.columns.joinedAt}</TableHead>
          <TableHead className="text-right">{messages.organizationMembers.table.columns.actions}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {members.map((member) => {
          const isCurrentMembership = member.id === currentMembershipId;

          return (
            <TableRow key={member.id}>
              <TableCell>
                <div className="space-y-1">
                  <p className="font-semibold text-slate-900">{member.user_full_name}</p>
                  <p className="text-xs text-slate-500">{member.user_email}</p>
                </div>
              </TableCell>
              <TableCell>
                {canManageMembers ? (
                  <Select
                    aria-label={messages.organizationMembers.table.roleSelectLabel}
                    value={member.role}
                    disabled={isUpdating}
                    onChange={(event) =>
                      onRoleChange(member.id, event.target.value as MembershipRole)
                    }
                  >
                    {MANAGEABLE_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {messages.common.memberships[role]}
                      </option>
                    ))}
                  </Select>
                ) : (
                  <Badge variant="info" dot>
                    <ShieldCheck className="h-3.5 w-3.5" />
                    {messages.common.memberships[member.role]}
                  </Badge>
                )}
              </TableCell>
              <TableCell>
                {canManageMembers ? (
                  <Select
                    aria-label={messages.organizationMembers.table.statusSelectLabel}
                    value={member.status}
                    disabled={isUpdating}
                    onChange={(event) =>
                      onStatusChange(member.id, event.target.value as MembershipStatus)
                    }
                  >
                    {MANAGEABLE_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {messages.organizationMembers.statuses[status]}
                      </option>
                    ))}
                  </Select>
                ) : (
                  <Badge variant={member.status === "ACTIVE" ? "success" : "neutral"}>
                    {messages.organizationMembers.statuses[member.status]}
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-slate-600">
                {dateFormatter.format(new Date(member.joined_at))}
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-end gap-2">
                  {isCurrentMembership ? (
                    <Badge variant="neutral" size="sm">
                      {messages.organizationMembers.table.currentUser}
                    </Badge>
                  ) : (
                    <span className="text-xs text-slate-400">-</span>
                  )}
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
