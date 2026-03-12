"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getMembershipOptions } from "@/lib/api/auth";
import type { MembershipOption } from "@/lib/api/types";
import {
  getStoredActiveMembershipId,
  setStoredActiveMembershipId,
} from "@/lib/session-storage";
import { useAuthContext } from "@/providers/auth-provider";

interface MembershipContextValue {
  memberships: MembershipOption[];
  activeMembership: MembershipOption | null;
  activeMembershipId: string | null;
  isLoading: boolean;
  isError: boolean;
  setActiveMembershipId: (membershipId: string) => void;
}

const MembershipContext = createContext<MembershipContextValue | null>(null);

export function MembershipProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuthContext();
  const [activeMembershipId, setActiveMembershipIdState] = useState<string | null>(null);

  const membershipsQuery = useQuery({
    queryKey: ["auth", "memberships", user?.id ?? null],
    queryFn: async () => (await getMembershipOptions()) ?? [],
    enabled: isAuthenticated && Boolean(user?.id),
  });

  useEffect(() => {
    if (!isAuthenticated) {
      setActiveMembershipIdState(null);
      setStoredActiveMembershipId(null);
      void queryClient.removeQueries({ queryKey: ["auth", "memberships"] });
      return;
    }

    const memberships = membershipsQuery.data ?? [];
    if (!memberships.length) {
      setActiveMembershipIdState(null);
      return;
    }

    const storedMembershipId = getStoredActiveMembershipId();
    const matchingMembership = memberships.find(
      (membership) => membership.id === storedMembershipId,
    );
    const fallbackMembership = matchingMembership ?? memberships[0];

    setActiveMembershipIdState(fallbackMembership.id);
    setStoredActiveMembershipId(fallbackMembership.id);
  }, [isAuthenticated, membershipsQuery.data, queryClient]);

  const setActiveMembershipId = useCallback(
    (membershipId: string) => {
      setActiveMembershipIdState(membershipId);
      setStoredActiveMembershipId(membershipId);
      void queryClient.invalidateQueries({
        predicate: (query) =>
          !String(query.queryKey[0] ?? "").startsWith("auth"),
      });
    },
    [queryClient],
  );

  const activeMembership =
    membershipsQuery.data?.find((membership) => membership.id === activeMembershipId) ?? null;

  const value = useMemo<MembershipContextValue>(
    () => ({
      memberships: membershipsQuery.data ?? [],
      activeMembership,
      activeMembershipId,
      isLoading: membershipsQuery.isLoading,
      isError: membershipsQuery.isError,
      setActiveMembershipId,
    }),
    [
      membershipsQuery.data,
      activeMembership,
      activeMembershipId,
      membershipsQuery.isLoading,
      membershipsQuery.isError,
      setActiveMembershipId,
    ],
  );

  return (
    <MembershipContext.Provider value={value}>{children}</MembershipContext.Provider>
  );
}

export function useMembershipContext(): MembershipContextValue {
  const context = useContext(MembershipContext);
  if (!context) {
    throw new Error("useMembershipContext must be used within MembershipProvider");
  }

  return context;
}
