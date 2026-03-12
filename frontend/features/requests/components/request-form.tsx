"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateRequestMutation } from "@/features/requests/api";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";
import type { RequestSource } from "@/lib/api/types";

type FormValues = {
  title: string;
  description?: string;
  source: RequestSource;
};

const requestSources: RequestSource[] = ["EMAIL", "WEB_FORM", "API", "MANUAL"];

export function RequestForm() {
  const router = useRouter();
  const { pushToast } = useToast();
  const mutation = useCreateRequestMutation();
  const { messages } = useI18n();
  const schema = z.object({
    title: z.string().min(3, messages.requests.form.validation.title),
    description: z.string().max(2000).optional(),
    source: z.enum(["EMAIL", "WEB_FORM", "API", "MANUAL"]),
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      description: "",
      source: "EMAIL",
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const request = await mutation.mutateAsync({
        title: values.title,
        description: values.description?.trim() || null,
        source: values.source,
      });

      if (!request) {
        throw new ApiError(500, messages.requests.form.fallbackError);
      }

      pushToast({
        tone: "success",
        title: messages.requests.form.successTitle,
        description: messages.requests.form.successDescription,
      });
      router.push(`/requests/${request.id}`);
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.requests.form.errorTitle,
        description:
          error instanceof ApiError ? error.detail : messages.requests.form.fallbackError,
      });
    }
  });

  return (
    <Card className="max-w-3xl">
      <CardHeader>
        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {messages.requests.form.eyebrow}
        </p>
        <CardTitle className="mt-2 text-2xl">{messages.requests.form.title}</CardTitle>
        <CardDescription>
          {messages.requests.form.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={onSubmit}>
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">
              {messages.requests.form.titleLabel}
            </label>
            <Input
              id="title"
              placeholder={messages.requests.form.titlePlaceholder}
              {...form.register("title")}
            />
            {form.formState.errors.title ? (
              <p className="text-sm text-rose-600">{form.formState.errors.title.message}</p>
            ) : null}
          </div>

          <div className="grid gap-5 md:grid-cols-[0.6fr_1fr]">
            <div className="space-y-2">
              <label htmlFor="source" className="text-sm font-medium">
                {messages.requests.form.sourceLabel}
              </label>
              <Select id="source" {...form.register("source")}>
                {requestSources.map((source) => (
                  <option key={source} value={source}>
                    {messages.requests.sources[source]}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                {messages.requests.form.descriptionLabel}
              </label>
              <Textarea
                id="description"
                placeholder={messages.requests.form.descriptionPlaceholder}
                {...form.register("description")}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? messages.requests.form.submitting
                : messages.requests.form.submit}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
