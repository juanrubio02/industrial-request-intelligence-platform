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

import { getCurrentUser, login as loginRequest } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import type { AuthenticatedUser } from "@/lib/api/types";
import {
  clearStoredAuthState,
  getStoredSession,
  setStoredSession,
} from "@/lib/session-storage";

interface AuthContextValue {
  accessToken: string | null;
  user: AuthenticatedUser | null;
  isBootstrapping: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const logout = useCallback(() => {
    clearStoredAuthState();
    setAccessToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const currentUser = await getCurrentUser();
    if (!currentUser || !accessToken) {
      logout();
      return;
    }

    setUser(currentUser);
    setStoredSession({ accessToken, user: currentUser });
  }, [accessToken, logout]);

  const bootstrap = useCallback(async () => {
    const storedSession = getStoredSession();
    if (!storedSession?.accessToken) {
      setIsBootstrapping(false);
      return;
    }

    setAccessToken(storedSession.accessToken);
    setUser(storedSession.user);

    try {
      const currentUser = await getCurrentUser();
      if (!currentUser) {
        logout();
      } else {
        setUser(currentUser);
        setStoredSession({
          accessToken: storedSession.accessToken,
          user: currentUser,
        });
      }
    } catch {
      logout();
    } finally {
      setIsBootstrapping(false);
    }
  }, [logout]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onUnauthorized = () => logout();
    window.addEventListener("iri:unauthorized", onUnauthorized);
    return () => window.removeEventListener("iri:unauthorized", onUnauthorized);
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const session = await loginRequest({ email, password });
    if (!session?.access_token) {
      throw new ApiError(500, "Login did not return an access token.");
    }

    try {
      setAccessToken(session.access_token);
      setStoredSession({ accessToken: session.access_token, user: null });

      const currentUser = await getCurrentUser();
      if (!currentUser) {
        throw new ApiError(500, "Authenticated user could not be loaded.");
      }

      setUser(currentUser);
      setStoredSession({ accessToken: session.access_token, user: currentUser });
    } catch (error) {
      logout();
      throw error;
    }
  }, [logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      user,
      isBootstrapping,
      isAuthenticated: Boolean(accessToken && user),
      login,
      logout,
      refreshUser,
    }),
    [accessToken, user, isBootstrapping, login, logout, refreshUser],
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
