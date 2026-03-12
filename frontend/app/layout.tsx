import type { Metadata } from "next";
import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { Inter, JetBrains_Mono } from "next/font/google";

import { AppProviders } from "@/providers/app-providers";
import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE_KEY,
  isSupportedLocale,
} from "@/i18n/config";
import "@/app/globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Industrial Request Intelligence",
  description: "Workspace operativo para solicitudes industriales e inteligencia documental.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const localeCookie = cookies().get(LOCALE_COOKIE_KEY)?.value;
  const initialLocale = isSupportedLocale(localeCookie) ? localeCookie : DEFAULT_LOCALE;

  return (
    <html lang={initialLocale} className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-background font-sans antialiased">
        <AppProviders initialLocale={initialLocale}>{children}</AppProviders>
      </body>
    </html>
  );
}
