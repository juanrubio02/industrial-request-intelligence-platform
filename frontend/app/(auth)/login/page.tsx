"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Select } from "@/components/ui/select";
import { LoginForm } from "@/features/auth/components/login-form";
import { useAuth } from "@/hooks/use-auth";
import { type Locale, SUPPORTED_LOCALES } from "@/i18n/config";
import { useI18n } from "@/i18n/hooks";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isBootstrapping } = useAuth();
  const { locale, messages, setLocale } = useI18n();

  useEffect(() => {
    if (!isBootstrapping && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isBootstrapping, router]);

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="grid w-full max-w-6xl gap-8 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="hidden rounded-[2rem] border border-white/70 bg-white/70 p-10 shadow-panel xl:flex xl:flex-col xl:justify-between">
          <div>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {messages.login.hero.eyebrow}
            </p>
            <h1 className="mt-5 max-w-xl text-5xl font-semibold tracking-tight text-slate-950">
              {messages.login.hero.title}
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600">
              {messages.login.hero.description}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {messages.login.hero.highlights.map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-line bg-white px-4 py-4 text-sm font-medium text-slate-700"
              >
                {item}
              </div>
            ))}
          </div>
        </section>

        <div className="flex flex-col gap-5">
          <div className="flex justify-end">
            <div className="w-full max-w-[180px]">
              <Select
                aria-label={messages.language.label}
                value={locale}
                onChange={(event) => setLocale(event.target.value as Locale)}
              >
                {SUPPORTED_LOCALES.map((supportedLocale) => (
                  <option key={supportedLocale} value={supportedLocale}>
                    {messages.language.options[supportedLocale]}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="flex items-center justify-center">
            <LoginForm />
          </div>
        </div>
      </div>
    </main>
  );
}
