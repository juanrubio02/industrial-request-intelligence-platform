"use client";

import { useMembershipContext } from "@/providers/membership-provider";

export function useMembership() {
  return useMembershipContext();
}
