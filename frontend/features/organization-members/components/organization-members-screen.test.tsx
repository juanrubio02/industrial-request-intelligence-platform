import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { OrganizationMembersScreen } from "@/features/organization-members/components/organization-members-screen";
import { ApiError } from "@/lib/api/client";

const useAuthMock = vi.fn();
const useMembersQueryMock = vi.fn();
const updateRoleMutateAsync = vi.fn();
const updateStatusMutateAsync = vi.fn();
const pushToast = vi.fn();

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast,
  }),
}));

vi.mock("@/i18n/hooks", () => ({
  useI18n: () => ({
    locale: "es",
    messages: {
      common: {
        labels: {
          notAvailable: "No disponible",
        },
        memberships: {
          OWNER: "Owner",
          ADMIN: "Admin",
          MANAGER: "Gestor",
          MEMBER: "Miembro",
          VIEWER: "Visualizador",
        },
      },
      organizationMembers: {
        header: {
          eyebrow: "Gobierno interno",
          title: "Miembros y accesos",
          description: "Gestiona el equipo",
          activeRoleLabel: "Rol activo:",
        },
        loadError: "Load error",
        empty: {
          title: "Empty",
          description: "Empty description",
        },
        noPermission: {
          title: "No tienes permisos para gestionar miembros",
          description: "Sin permisos",
        },
        table: {
          columns: {
            member: "Miembro",
            role: "Rol",
            status: "Estado",
            joinedAt: "Alta",
            actions: "Acciones",
          },
          roleSelectLabel: "Cambiar rol del miembro",
          statusSelectLabel: "Cambiar estado del miembro",
          currentUser: "Tu acceso",
        },
        statuses: {
          ACTIVE: "Activo",
          DISABLED: "Deshabilitado",
        },
        toasts: {
          roleUpdatedTitle: "Rol actualizado",
          roleUpdatedDescription: "El rol del miembro ya está actualizado.",
          roleErrorTitle: "No se pudo actualizar el rol",
          statusUpdatedTitle: "Estado actualizado",
          statusUpdatedDescription: "El estado del miembro ya está actualizado.",
          statusErrorTitle: "No se pudo actualizar el estado",
          fallbackError: "Error",
        },
      },
    },
  }),
}));

vi.mock("@/features/organization-members/api", () => ({
  useOrganizationMembersQuery: () => useMembersQueryMock(),
  useUpdateOrganizationMemberRoleMutation: () => ({
    isPending: false,
    mutateAsync: updateRoleMutateAsync,
  }),
  useUpdateOrganizationMemberStatusMutation: () => ({
    isPending: false,
    mutateAsync: updateStatusMutateAsync,
  }),
}));

describe("OrganizationMembersScreen", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    useMembersQueryMock.mockReset();
    updateRoleMutateAsync.mockReset();
    updateStatusMutateAsync.mockReset();
    pushToast.mockReset();

    useAuthMock.mockReturnValue({
      activeMembership: {
        id: "membership-1",
        role: "OWNER",
        status: "ACTIVE",
      },
      activeOrganization: {
        id: "org-1",
        name: "Acme Industrial",
        slug: "acme-industrial",
      },
      canManageMembers: true,
      refreshMe: vi.fn().mockResolvedValue(undefined),
    });
    useMembersQueryMock.mockReturnValue({
      isLoading: false,
      isError: false,
      data: [
        {
          id: "membership-1",
          organization_id: "org-1",
          user_id: "user-1",
          user_full_name: "Alice Owner",
          user_email: "alice@example.com",
          role: "OWNER",
          status: "ACTIVE",
          joined_at: "2026-03-10T10:00:00Z",
          created_at: "2026-03-10T10:00:00Z",
          updated_at: "2026-03-10T10:00:00Z",
          is_active: true,
        },
        {
          id: "membership-2",
          organization_id: "org-1",
          user_id: "user-2",
          user_full_name: "Bob Member",
          user_email: "bob@example.com",
          role: "MEMBER",
          status: "ACTIVE",
          joined_at: "2026-03-11T10:00:00Z",
          created_at: "2026-03-11T10:00:00Z",
          updated_at: "2026-03-11T10:00:00Z",
          is_active: true,
        },
      ],
    });
  });

  it("renders members and allows authorized role updates", async () => {
    const refreshMe = vi.fn().mockResolvedValue(undefined);
    useAuthMock.mockReturnValue({
      activeMembership: {
        id: "membership-1",
        role: "OWNER",
        status: "ACTIVE",
      },
      activeOrganization: {
        id: "org-1",
        name: "Acme Industrial",
        slug: "acme-industrial",
      },
      canManageMembers: true,
      refreshMe,
    });
    updateRoleMutateAsync.mockResolvedValue(undefined);

    render(<OrganizationMembersScreen />);

    expect(screen.getByText(/miembros y accesos/i)).toBeInTheDocument();
    expect(screen.getByText("Bob Member")).toBeInTheDocument();

    fireEvent.change(screen.getAllByLabelText(/cambiar rol del miembro/i)[1], {
      target: { value: "MANAGER" },
    });

    await waitFor(() => {
      expect(updateRoleMutateAsync).toHaveBeenCalledWith({
        membershipId: "membership-2",
        payload: { role: "MANAGER" },
      });
      expect(refreshMe).toHaveBeenCalledTimes(1);
    });
  });

  it("hides management UI for users without permission", () => {
    useAuthMock.mockReturnValue({
      activeMembership: {
        id: "membership-3",
        role: "MEMBER",
        status: "ACTIVE",
      },
      activeOrganization: {
        id: "org-1",
        name: "Acme Industrial",
        slug: "acme-industrial",
      },
      canManageMembers: false,
      refreshMe: vi.fn(),
    });

    render(<OrganizationMembersScreen />);

    expect(screen.getByText(/no tienes permisos para gestionar miembros/i)).toBeInTheDocument();
    expect(screen.queryByText("Bob Member")).not.toBeInTheDocument();
  });

  it("surfaces API errors on status updates", async () => {
    updateStatusMutateAsync.mockRejectedValue(new ApiError(400, "Cannot disable last owner."));

    render(<OrganizationMembersScreen />);

    fireEvent.change(screen.getAllByLabelText(/cambiar estado del miembro/i)[1], {
      target: { value: "DISABLED" },
    });

    await waitFor(() => {
      expect(pushToast).toHaveBeenCalledWith(
        expect.objectContaining({
          tone: "error",
          description: "Cannot disable last owner.",
        }),
      );
    });
  });
});
