import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

import { DEFAULT_LOCALE, type Locale, getIntlLocale } from "@/i18n/config";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDateTime(value: string, locale: Locale = DEFAULT_LOCALE): string {
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatRelativeFileSize(
  sizeBytes: number,
  locale: Locale = DEFAULT_LOCALE,
): string {
  const numberFormatter = new Intl.NumberFormat(getIntlLocale(locale), {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  });

  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }

  if (sizeBytes < 1024 * 1024) {
    return `${numberFormatter.format(sizeBytes / 1024)} KB`;
  }

  return `${numberFormatter.format(sizeBytes / (1024 * 1024))} MB`;
}
