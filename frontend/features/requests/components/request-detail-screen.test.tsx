import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { RequestDetailScreen } from "@/features/requests/components/request-detail-screen";

vi.mock("@/features/requests/api", () => ({
  useRequestQuery: () => ({
    isLoading: false,
    data: {
      id: "req-1",
      organization_id: "org-1",
      title: "Need conveyor upgrade",
      description: "Upgrade line B conveyor system.",
      status: "UNDER_REVIEW",
      source: "EMAIL",
      created_by_membership_id: "mem-1",
      created_at: "2026-03-12T09:00:00Z",
      updated_at: "2026-03-12T10:00:00Z",
    },
  }),
  useRequestActivitiesQuery: () => ({
    data: [
      {
        id: "activity-1",
        request_id: "req-1",
        organization_id: "org-1",
        membership_id: "mem-1",
        type: "REQUEST_CREATED",
        payload: { request_id: "req-1" },
        created_at: "2026-03-12T09:00:00Z",
      },
    ],
  }),
}));

vi.mock("@/features/documents/api", () => ({
  useRequestDocumentsQuery: () => ({
    data: [
      {
        id: "doc-1",
        request_id: "req-1",
        organization_id: "org-1",
        uploaded_by_membership_id: "mem-1",
        original_filename: "spec.pdf",
        storage_key: "documents/org-1/req-1/spec.pdf",
        content_type: "application/pdf",
        size_bytes: 2048,
        processing_status: "PENDING",
        created_at: "2026-03-12T09:00:00Z",
        updated_at: "2026-03-12T09:00:00Z",
      },
    ],
  }),
  useUploadDocumentMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast: vi.fn(),
  }),
}));

vi.mock("@/features/requests/components/request-status-actions", () => ({
  RequestStatusActions: () => <div>Status actions</div>,
}));

describe("RequestDetailScreen", () => {
  it("renders request header, activities and documents", () => {
    render(<RequestDetailScreen requestId="req-1" />);

    expect(screen.getByText("Need conveyor upgrade")).toBeInTheDocument();
    expect(screen.getByText("Status actions")).toBeInTheDocument();
    expect(screen.getByText("spec.pdf")).toBeInTheDocument();
    expect(screen.getByText("Solicitud creada")).toBeInTheDocument();
  });
});
