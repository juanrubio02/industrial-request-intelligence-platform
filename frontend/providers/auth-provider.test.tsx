import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { useAuthContext, AuthProvider } from "@/providers/auth-provider";

const authApiMocks = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  getCurrentUser: authApiMocks.getCurrentUser,
  login: authApiMocks.loginRequest,
  logout: authApiMocks.logoutRequest,
}));

function AuthHarness() {
  const {
    activeMembership,
    activeOrganization,
    canManageMembers,
    isAuthenticated,
    isBootstrapping,
    login,
    logout,
    user,
  } = useAuthContext();

  return (
    <div>
      <p>{isBootstrapping ? "bootstrapping" : "ready"}</p>
      <p>{isAuthenticated ? "authenticated" : "anonymous"}</p>
      <p>{user?.email ?? "no-user"}</p>
      <p>{activeOrganization?.name ?? "no-organization"}</p>
      <p>{activeMembership?.role ?? "no-membership"}</p>
      <p>{canManageMembers ? "can-manage-members" : "cannot-manage-members"}</p>
      <button type="button" onClick={() => void login("alice@example.com", "StrongPass123!")}>
        login
      </button>
      <button type="button" onClick={() => void logout()}>
        logout
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    authApiMocks.getCurrentUser.mockReset();
    authApiMocks.loginRequest.mockReset();
    authApiMocks.logoutRequest.mockReset();
    window.localStorage.clear();
  });

  it("reconstructs the authenticated session with /auth/me on bootstrap", async () => {
    authApiMocks.getCurrentUser.mockResolvedValue({
      id: "user-1",
      email: "alice@example.com",
      full_name: "Alice Example",
      is_active: true,
      active_organization: {
        id: "org-1",
        name: "Acme Industrial",
        slug: "acme-industrial",
      },
      active_membership: {
        id: "membership-1",
        role: "OWNER",
        status: "ACTIVE",
      },
      created_at: "2026-03-13T10:00:00Z",
      updated_at: "2026-03-13T10:00:00Z",
    });

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("ready")).toBeInTheDocument();
      expect(screen.getByText("authenticated")).toBeInTheDocument();
      expect(screen.getByText("alice@example.com")).toBeInTheDocument();
      expect(screen.getByText("Acme Industrial")).toBeInTheDocument();
      expect(screen.getByText("OWNER")).toBeInTheDocument();
      expect(screen.getByText("can-manage-members")).toBeInTheDocument();
    });
    expect(authApiMocks.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  it("logs out through the API and clears the local auth state", async () => {
    const user = userEvent.setup();
    authApiMocks.getCurrentUser.mockResolvedValue({
      id: "user-1",
      email: "alice@example.com",
      full_name: "Alice Example",
      is_active: true,
      active_organization: {
        id: "org-1",
        name: "Acme Industrial",
        slug: "acme-industrial",
      },
      active_membership: {
        id: "membership-1",
        role: "OWNER",
        status: "ACTIVE",
      },
      created_at: "2026-03-13T10:00:00Z",
      updated_at: "2026-03-13T10:00:00Z",
    });
    authApiMocks.logoutRequest.mockResolvedValue(null);

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await screen.findByText("authenticated");
    await user.click(screen.getByRole("button", { name: "logout" }));

    await waitFor(() => {
      expect(authApiMocks.logoutRequest).toHaveBeenCalledTimes(1);
      expect(screen.getByText("anonymous")).toBeInTheDocument();
      expect(screen.getByText("no-user")).toBeInTheDocument();
      expect(screen.getByText("no-organization")).toBeInTheDocument();
      expect(screen.getByText("no-membership")).toBeInTheDocument();
    });
  });
});
