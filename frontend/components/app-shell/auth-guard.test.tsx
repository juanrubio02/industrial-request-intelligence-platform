import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AuthGuard } from "@/components/app-shell/auth-guard";

const replace = vi.fn();
const useAuth = vi.fn();
const useMembership = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/requests",
}));

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => useAuth(),
}));

vi.mock("@/hooks/use-membership", () => ({
  useMembership: () => useMembership(),
}));

vi.mock("@/i18n/hooks", () => ({
  useI18n: () => ({
    messages: {
      shell: {
        guards: {
          workspaceLoadingFailed: "workspace failed",
          workspaceLoadingTitle: "workspace title",
          workspaceLoadingDescription: "workspace description",
          noWorkspaceEyebrow: "no workspace",
          noWorkspaceTitle: "no workspace title",
          noWorkspaceDescription: "no workspace description",
        },
      },
    },
  }),
}));

describe("AuthGuard", () => {
  beforeEach(() => {
    replace.mockReset();
    useAuth.mockReset();
    useMembership.mockReset();
  });

  it("redirects private routes to /login when there is no session", async () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      isBootstrapping: false,
    });
    useMembership.mockReturnValue({
      memberships: [],
      isError: false,
      isLoading: false,
    });

    render(
      <AuthGuard>
        <div>private content</div>
      </AuthGuard>,
    );

    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/login");
    });
    expect(screen.queryByText("private content")).not.toBeInTheDocument();
  });

  it("renders children when the session and memberships are loaded", () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      isBootstrapping: false,
    });
    useMembership.mockReturnValue({
      memberships: [{ id: "membership-1" }],
      isError: false,
      isLoading: false,
    });

    render(
      <AuthGuard>
        <div>private content</div>
      </AuthGuard>,
    );

    expect(screen.getByText("private content")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
