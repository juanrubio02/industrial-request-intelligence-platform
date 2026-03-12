import { apiRequest } from "@/lib/api/client";
import type { HealthStatus } from "@/lib/api/types";

export function getHealthStatus(): Promise<HealthStatus | null> {
  return apiRequest<HealthStatus>("/health");
}
