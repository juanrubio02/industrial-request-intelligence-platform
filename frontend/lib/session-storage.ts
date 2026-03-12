import {
  ACTIVE_MEMBERSHIP_STORAGE_KEY,
  SESSION_STORAGE_KEY,
} from "@/lib/constants";
import type { AuthenticatedUser } from "@/lib/api/types";

export interface StoredSession {
  accessToken: string;
  user: AuthenticatedUser | null;
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getStoredSession(): StoredSession | null {
  if (!isBrowser()) {
    return null;
  }

  const rawValue = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as StoredSession;
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function setStoredSession(session: StoredSession | null): void {
  if (!isBrowser()) {
    return;
  }

  if (session === null) {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function getStoredActiveMembershipId(): string | null {
  if (!isBrowser()) {
    return null;
  }

  return window.localStorage.getItem(ACTIVE_MEMBERSHIP_STORAGE_KEY);
}

export function setStoredActiveMembershipId(membershipId: string | null): void {
  if (!isBrowser()) {
    return;
  }

  if (membershipId === null) {
    window.localStorage.removeItem(ACTIVE_MEMBERSHIP_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(ACTIVE_MEMBERSHIP_STORAGE_KEY, membershipId);
}

export function clearStoredAuthState(): void {
  setStoredSession(null);
  setStoredActiveMembershipId(null);
}
