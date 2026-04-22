import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { RequestsScreen } from "@/features/requests/components/requests-screen";

const useRequestsQueryMock = vi.fn();

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>(
    "@tanstack/react-query",
  );
  return {
    ...actual,
    useQuery: () => ({
      data: [
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
      ],
      isLoading: false,
      isError: false,
    }),
  };
});

vi.mock("@/features/requests/api", () => ({
  useRequestsQuery: (...args: unknown[]) => useRequestsQueryMock(...args),
  useTransitionRequestStatusMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-membership", () => ({
  useMembership: () => ({
    activeMembership: {
      organization_id: "org-1",
    },
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast: vi.fn(),
  }),
}));

describe("RequestsScreen", () => {
  beforeEach(() => {
    useRequestsQueryMock.mockReset();
    useRequestsQueryMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: [],
    });
  });

  it("renders filter controls and updates the query filters", async () => {
    render(<RequestsScreen />);

    expect(screen.getByLabelText(/buscar por título/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/estado/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/responsable/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/origen/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/buscar por título/i), {
      target: { value: "stainless" },
    });
    fireEvent.change(screen.getByLabelText(/estado/i), {
      target: { value: "UNDER_REVIEW" },
    });

    await waitFor(() => {
      expect(useRequestsQueryMock).toHaveBeenLastCalledWith({
        q: "stainless",
        status: "UNDER_REVIEW",
        assigned_membership_id: undefined,
        source: undefined,
      });
    });
  });

  it("shows filtered empty state when no results match", () => {
    render(<RequestsScreen />);

    fireEvent.change(screen.getByLabelText(/buscar por título/i), {
      target: { value: "nomatch" },
    });

    expect(screen.getByText(/no hay resultados para los filtros aplicados/i)).toBeInTheDocument();
  });

  it("switches to pipeline view without changing the data source", () => {
    useRequestsQueryMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: [
        {
          id: "req-1",
          organization_id: "org-1",
          title: "Need stainless pumps",
          description: null,
          status: "NEW",
          source: "EMAIL",
          created_by_membership_id: "mem-1",
          assigned_membership_id: "mem-1",
          documents_count: 1,
          comments_count: 2,
          available_status_transitions: ["UNDER_REVIEW"],
          created_at: "2026-03-12T09:00:00Z",
          updated_at: "2026-03-12T10:00:00Z",
        },
      ],
    });

    render(<RequestsScreen />);

    fireEvent.click(screen.getByRole("button", { name: /vista pipeline/i }));

    expect(screen.getByText(/pipeline visual/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Need stainless pumps" })).toHaveAttribute(
      "href",
      "/requests/req-1",
    );
  });
});
