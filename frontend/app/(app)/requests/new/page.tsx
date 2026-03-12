"use client";

import { PageHeader } from "@/components/page-header";
import { RequestForm } from "@/features/requests/components/request-form";
import { useI18n } from "@/i18n/hooks";

export default function NewRequestPage() {
  const { messages } = useI18n();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={messages.requests.new.eyebrow}
        title={messages.requests.new.title}
        description={messages.requests.new.description}
      />
      <RequestForm />
    </div>
  );
}
