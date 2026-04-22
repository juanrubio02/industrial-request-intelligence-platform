import React from "react";
import { render, screen } from "@testing-library/react";

import { PipelineFunnelChart } from "@/features/dashboard/components/pipeline-funnel-chart";

describe("PipelineFunnelChart", () => {
  it("renders the funnel stages and counts", () => {
    render(
      <PipelineFunnelChart
        analytics={{
          total_requests: 8,
          conversion_rate: 0.25,
          loss_rate: 0.125,
          requests_by_status: {
            NEW: 3,
            UNDER_REVIEW: 2,
            QUOTE_PREPARING: 1,
            QUOTE_SENT: 1,
            NEGOTIATION: 0,
            WON: 1,
            LOST: 0,
          },
          avg_time_per_stage: {
            NEW: 1.1,
            UNDER_REVIEW: 2.2,
            QUOTE_PREPARING: 3.3,
            QUOTE_SENT: 1.5,
            NEGOTIATION: 0,
            WON: 0,
            LOST: 0,
          },
          pipeline_velocity_days: 8.2,
          bottlenecks: [],
        }}
      />,
    );

    expect(screen.getByText(/funnel del pipeline/i)).toBeInTheDocument();
    expect(screen.getAllByText(/nueva/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/3 solicitudes/i)).toBeInTheDocument();
  });
});
