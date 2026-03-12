import React from "react";
import { render, screen } from "@testing-library/react";

import { RequestListTable } from "@/features/requests/components/request-list-table";
import type { RequestRecord } from "@/lib/api/types";

const requests: RequestRecord[] = [
  {
    id: "req-1",
    organization_id: "org-1",
    title: "Need stainless pumps",
    description: null,
    status: "UNDER_REVIEW",
    source: "EMAIL",
    created_by_membership_id: "mem-1",
    created_at: "2026-03-12T09:00:00Z",
    updated_at: "2026-03-12T10:00:00Z",
  },
];

describe("RequestListTable", () => {
  it("renders request rows", () => {
    render(<RequestListTable requests={requests} />);

    expect(screen.getByText("Need stainless pumps")).toBeInTheDocument();
    expect(screen.getByText("En revisión")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /abrir/i })).toHaveAttribute(
      "href",
      "/requests/req-1",
    );
  });
});
