import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { RequestsPipelineScreen } from "@/features/requests/components/requests-pipeline-screen";
import type { OrganizationMembershipOption, RequestRecord } from "@/lib/api/types";

const memberships: OrganizationMembershipOption[] = [
  {
    id: "mem-1",
    organization_id: "org-1",
    user_id: "user-1",
    user_full_name: "Alice Admin",
    user_email: "alice@example.com",
    role: "ADMIN",
    is_active: true,
    created_at: "2026-03-12T09:00:00Z",
    updated_at: "2026-03-12T09:00:00Z",
  },
];

const requests: RequestRecord[] = [
  {
    id: "req-1",
    organization_id: "org-1",
    title: "Need stainless pumps",
    description: null,
    status: "NEW",
    source: "EMAIL",
    created_by_membership_id: "mem-1",
    assigned_membership_id: "mem-1",
    documents_count: 2,
    comments_count: 1,
    available_status_transitions: ["UNDER_REVIEW"],
    created_at: "2026-03-12T09:00:00Z",
    updated_at: "2026-03-12T10:00:00Z",
  },
  {
    id: "req-2",
    organization_id: "org-1",
    title: "Review extrusion quote",
    description: null,
    status: "UNDER_REVIEW",
    source: "MANUAL",
    created_by_membership_id: "mem-1",
    assigned_membership_id: null,
    documents_count: 0,
    comments_count: 3,
    available_status_transitions: ["QUOTE_PREPARING"],
    created_at: "2026-03-12T08:00:00Z",
    updated_at: "2026-03-12T11:00:00Z",
  },
];

vi.mock("@/features/requests/api", () => ({
  useTransitionRequestStatusMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-membership", () => ({
  useMembership: () => ({
    activeMembership: {
      role: "ADMIN",
    },
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast: vi.fn(),
  }),
}));

describe("RequestsPipelineScreen", () => {
  it("renders pipeline columns and groups requests by status", () => {
    render(
      <RequestsPipelineScreen
        requests={requests}
        memberships={memberships}
      />,
    );

    expect(screen.getByText(/pipeline visual/i)).toBeInTheDocument();
    expect(screen.getByText("Need stainless pumps")).toBeInTheDocument();
    expect(screen.getByText("Review extrusion quote")).toBeInTheDocument();
    expect(screen.getAllByText(/no hay solicitudes en esta fase/i).length).toBeGreaterThan(0);
  });

  it("renders cards as links to request detail", () => {
    render(
      <RequestsPipelineScreen
        requests={requests}
        memberships={memberships}
      />,
    );

    expect(screen.getByRole("link", { name: "Need stainless pumps" })).toHaveAttribute(
      "href",
      "/requests/req-1",
    );
  });
});
