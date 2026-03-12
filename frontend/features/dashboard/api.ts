"use client";

import { useQuery } from "@tanstack/react-query";

import { useRequestsQuery } from "@/features/requests/api";
import { getHealthStatus } from "@/lib/api/system";

export function useDashboardHealthQuery() {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: async () => getHealthStatus(),
  });
}

export function useDashboardRequests() {
  return useRequestsQuery();
}
