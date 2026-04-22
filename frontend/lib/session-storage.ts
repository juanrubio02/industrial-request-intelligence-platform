import { ACTIVE_MEMBERSHIP_STORAGE_KEY } from "@/lib/constants";

function isBrowser(): boolean {
  return typeof window !== "undefined";
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
  setStoredActiveMembershipId(null);
}
