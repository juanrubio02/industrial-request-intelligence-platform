"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";

type LoginFormValues = {
  email: string;
  password: string;
};

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const { pushToast } = useToast();
  const { messages } = useI18n();
  const loginSchema = z.object({
    email: z.string().email(messages.login.form.validation.email),
    password: z.string().min(8, messages.login.form.validation.password),
  });
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await login(values.email, values.password);
      pushToast({
        tone: "success",
        title: messages.login.form.successTitle,
        description: messages.login.form.successDescription,
      });
      router.replace("/dashboard");
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.login.form.errorTitle,
        description:
          error instanceof ApiError ? error.detail : messages.login.form.fallbackError,
      });
    }
  });

  return (
    <Card className="w-full max-w-md border-white/70 bg-white/90">
      <CardHeader className="space-y-3">
        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {messages.login.form.eyebrow}
        </p>
        <CardTitle className="text-3xl">{messages.login.form.title}</CardTitle>
        <CardDescription>
          {messages.login.form.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={onSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="email">
              {messages.login.form.email}
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                id="email"
                type="email"
                autoComplete="email"
                className="pl-10"
                {...form.register("email")}
              />
            </div>
            {form.formState.errors.email ? (
              <p className="text-sm text-rose-600">{form.formState.errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="password">
              {messages.login.form.password}
            </label>
            <div className="relative">
              <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                className="pl-10"
                {...form.register("password")}
              />
            </div>
            {form.formState.errors.password ? (
              <p className="text-sm text-rose-600">{form.formState.errors.password.message}</p>
            ) : null}
          </div>

          <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting
              ? messages.login.form.submitting
              : messages.login.form.submit}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
