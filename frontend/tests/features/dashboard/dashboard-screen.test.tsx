import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DashboardScreen } from "@/features/dashboard/components/dashboard-screen";

const usePipelineAnalyticsQueryMock = vi.fn();

vi.mock("@/features/dashboard/api", () => ({
  usePipelineAnalyticsQuery: () => usePipelineAnalyticsQueryMock(),
}));

describe("DashboardScreen", () => {
  beforeEach(() => {
    usePipelineAnalyticsQueryMock.mockReset();
  });

  it("renders pipeline intelligence metrics and bottlenecks", () => {
    usePipelineAnalyticsQueryMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        total_requests: 12,
        conversion_rate: 0.25,
        loss_rate: 0.1,
        requests_by_status: {
          NEW: 4,
          UNDER_REVIEW: 2,
          QUOTE_PREPARING: 3,
          QUOTE_SENT: 1,
          NEGOTIATION: 1,
          WON: 1,
          LOST: 0,
        },
        avg_time_per_stage: {
          NEW: 1.5,
          UNDER_REVIEW: 2.1,
          QUOTE_PREPARING: 5.3,
          QUOTE_SENT: 2.4,
          NEGOTIATION: 1.2,
          WON: 0,
          LOST: 0,
        },
        pipeline_velocity_days: 11.4,
        bottlenecks: [
          {
            status: "QUOTE_PREPARING",
            avg_days: 5.3,
          },
        ],
      },
    });

    render(<DashboardScreen />);

    expect(screen.getByText(/pipeline intelligence/i)).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText(/25/)).toBeInTheDocument();
    expect(screen.getAllByText(/preparando oferta/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/5[.,]3/).length).toBeGreaterThan(0);
  });

  it("renders empty state when there are no requests", () => {
    usePipelineAnalyticsQueryMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        total_requests: 0,
        conversion_rate: 0,
        loss_rate: 0,
        requests_by_status: {
          NEW: 0,
          UNDER_REVIEW: 0,
          QUOTE_PREPARING: 0,
          QUOTE_SENT: 0,
          NEGOTIATION: 0,
          WON: 0,
          LOST: 0,
        },
        avg_time_per_stage: {
          NEW: 0,
          UNDER_REVIEW: 0,
          QUOTE_PREPARING: 0,
          QUOTE_SENT: 0,
          NEGOTIATION: 0,
          WON: 0,
          LOST: 0,
        },
        pipeline_velocity_days: 0,
        bottlenecks: [],
      },
    });

    render(<DashboardScreen />);

    expect(screen.getByText(/todavía no hay suficientes solicitudes/i)).toBeInTheDocument();
  });
});
