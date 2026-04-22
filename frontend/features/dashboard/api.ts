"use client";

import { useQuery } from "@tanstack/react-query";

import { getPipelineAnalytics } from "@/lib/api/analytics";

export function usePipelineAnalyticsQuery() {
  return useQuery({
    queryKey: ["analytics", "pipeline"],
    queryFn: async () => getPipelineAnalytics(),
  });
}
