import { apiRequest } from "@/lib/api/client";
import type { PipelineAnalytics } from "@/lib/api/types";

export function getPipelineAnalytics(): Promise<PipelineAnalytics | null> {
  return apiRequest<PipelineAnalytics>("/analytics/pipeline", {
    includeAuth: true,
    includeMembership: true,
  });
}
