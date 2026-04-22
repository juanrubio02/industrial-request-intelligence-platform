import { ApiError } from "@/lib/api/client";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { LoginForm } from "@/features/auth/components/login-form";

const pushToast = vi.fn();
const login = vi.fn();
const replace = vi.fn();

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    login,
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    login.mockReset();
    pushToast.mockReset();
    replace.mockReset();
  });

  it("validates required credentials and submits the login flow", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));

    expect(await screen.findByText(/introduce un correo válido/i)).toBeInTheDocument();

    login.mockResolvedValue(undefined);

    await user.type(screen.getByLabelText(/correo electrónico/i), "alice@example.com");
    await user.type(screen.getByLabelText(/contraseña/i), "StrongPass123!");
    await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("alice@example.com", "StrongPass123!");
      expect(replace).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows an error toast when credentials are invalid", async () => {
    const user = userEvent.setup();
    login.mockRejectedValue(new ApiError(401, "Invalid email or password."));

    render(<LoginForm />);

    await user.type(screen.getByLabelText(/correo electrónico/i), "alice@example.com");
    await user.type(screen.getByLabelText(/contraseña/i), "WrongPass123!");
    await user.click(screen.getByRole("button", { name: /iniciar sesión/i }));

    await waitFor(() => {
      expect(pushToast).toHaveBeenCalledWith(
        expect.objectContaining({
          tone: "error",
          description: "Invalid email or password.",
        }),
      );
    });
    expect(replace).not.toHaveBeenCalled();
  });
});
