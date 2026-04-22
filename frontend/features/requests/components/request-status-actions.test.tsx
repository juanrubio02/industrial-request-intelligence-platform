import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { RequestStatusActions } from "@/features/requests/components/request-status-actions";

const mutateAsync = vi.fn();

vi.mock("@/features/requests/api", () => ({
  useTransitionRequestStatusMutation: () => ({
    isPending: false,
    mutateAsync,
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

describe("RequestStatusActions", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("submits a backend transition from the compact select mode", async () => {
    render(
      <RequestStatusActions
        requestId="req-1"
        availableTransitions={["UNDER_REVIEW"]}
        display="select"
      />,
    );

    fireEvent.change(screen.getByLabelText(/mover solicitud/i), {
      target: { value: "UNDER_REVIEW" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /mover/i }));
    });

    expect(mutateAsync).toHaveBeenCalledWith({
      new_status: "UNDER_REVIEW",
    });
  });
});
