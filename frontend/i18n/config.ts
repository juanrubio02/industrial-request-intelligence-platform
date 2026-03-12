import { en } from "@/i18n/dictionaries/en";
import { es } from "@/i18n/dictionaries/es";

export const LOCALE_STORAGE_KEY = "iri.locale";
export const LOCALE_COOKIE_KEY = "iri.locale";
export const DEFAULT_LOCALE = "es";
export const SUPPORTED_LOCALES = ["es", "en"] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

type DeepMessageShape<T> = {
  [K in keyof T]: T[K] extends string
    ? string
    : T[K] extends readonly (infer U)[]
      ? U extends string
        ? readonly string[]
        : readonly DeepMessageShape<U>[]
      : T[K] extends object
        ? DeepMessageShape<T[K]>
        : T[K];
};

export type Messages = DeepMessageShape<typeof es>;

export const dictionaries: Record<Locale, Messages> = {
  es,
  en,
};

export function isSupportedLocale(value: string | null | undefined): value is Locale {
  return SUPPORTED_LOCALES.includes(value as Locale);
}

export function getDictionary(locale: Locale): Messages {
  return dictionaries[locale];
}

export function getIntlLocale(locale: Locale): string {
  return locale === "es" ? "es-ES" : "en-US";
}
