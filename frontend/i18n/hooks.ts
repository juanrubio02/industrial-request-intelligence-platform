import { useI18nContext } from "@/i18n/provider";

export function useI18n() {
  return useI18nContext();
}

export function interpolate(
  template: string,
  values: Record<string, string | number>,
): string {
  return Object.entries(values).reduce(
    (result, [key, value]) => result.replaceAll(`{${key}}`, String(value)),
    template,
  );
}
