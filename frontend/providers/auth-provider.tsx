"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from "@/lib/api/auth";
import type {
  ActiveMembershipSummary,
  ActiveOrganization,
  AuthenticatedUser,
  MembershipRole,
} from "@/lib/api/types";
import { clearStoredAuthState } from "@/lib/session-storage";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  activeOrganization: ActiveOrganization | null;
  activeMembership: ActiveMembershipSummary | null;
  role: MembershipRole | null;
  isBootstrapping: boolean;
  isLoading: boolean;
  isAuthenticated: boolean;
  canManageMembers: boolean;
  canEditRequests: boolean;
  canAssignRequests: boolean;
  isViewer: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const activeOrganization = user?.active_organization ?? null;
  const activeMembership = user?.active_membership ?? null;
  const role = activeMembership?.role ?? null;

  const clearAuthState = useCallback(() => {
    clearStoredAuthState();
    setUser(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      clearAuthState();
      return;
    }

    setUser(currentUser);
  }, [clearAuthState]);

  const bootstrap = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      if (!currentUser) {
        clearAuthState();
      } else {
        setUser(currentUser);
      }
    } catch {
      clearAuthState();
    } finally {
      setIsBootstrapping(false);
    }
  }, [clearAuthState]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onUnauthorized = () => clearAuthState();
    window.addEventListener("iri:unauthorized", onUnauthorized);
    return () => window.removeEventListener("iri:unauthorized", onUnauthorized);
  }, [clearAuthState]);

  const login = useCallback(async (email: string, password: string) => {
    const session = await loginRequest({ email, password });
    if (!session?.user) {
      clearAuthState();
      throw new Error("Login did not return an authenticated user.");
    }

    setUser(session.user);
  }, [clearAuthState]);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      clearAuthState();
    }
  }, [clearAuthState]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      activeOrganization,
      activeMembership,
      role,
      isBootstrapping,
      isLoading: isBootstrapping,
      isAuthenticated: Boolean(user),
      canManageMembers: role === "OWNER" || role === "ADMIN",
      canEditRequests:
        role === "OWNER" ||
        role === "ADMIN" ||
        role === "MANAGER" ||
        role === "MEMBER",
      canAssignRequests:
        role === "OWNER" || role === "ADMIN" || role === "MANAGER",
      isViewer: role === "VIEWER",
      login,
      logout,
      refreshMe,
    }),
    [
      user,
      activeOrganization,
      activeMembership,
      role,
      isBootstrapping,
      login,
      logout,
      refreshMe,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }

  return context;
}
