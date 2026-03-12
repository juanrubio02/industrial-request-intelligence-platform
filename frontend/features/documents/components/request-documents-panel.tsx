import Link from "next/link";
import { ArrowUpRight, FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentProcessingStatusBadge } from "@/features/documents/status-badges";
import { interpolate, useI18n } from "@/i18n/hooks";
import type { DocumentRecord } from "@/lib/api/types";
import { formatDateTime, formatRelativeFileSize } from "@/lib/utils";

export function RequestDocumentsPanel({
  documents,
}: {
  documents: DocumentRecord[];
}) {
  const { locale, messages } = useI18n();

  return (
    <Card className="h-full">
      <CardHeader>
        <p className="eyebrow">
          {messages.documents.panel.eyebrow}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <CardTitle>{messages.documents.panel.title}</CardTitle>
          <Badge variant="neutral" size="sm">
            {interpolate(messages.documents.panel.files, { count: documents.length })}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {documents.length ? (
          documents.map((document) => (
            <Link
              key={document.id}
              href={`/documents/${document.id}`}
              className="focus-ring flex items-center justify-between rounded-[var(--radius-control)] border border-line/80 bg-surface/70 px-4 py-4 transition hover:border-slate-300 hover:bg-surface"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-control)] bg-white shadow-soft">
                  <FileText className="h-4 w-4 text-slate-600" />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-semibold tracking-[-0.01em] text-slate-900">
                    {document.original_filename}
                  </p>
                  <p className="text-sm text-slate-500">
                    {formatRelativeFileSize(document.size_bytes, locale)} ·{" "}
                    {formatDateTime(document.updated_at, locale)}
                  </p>
                </div>
              </div>
              <div className="ml-4 flex items-center gap-3">
                <DocumentProcessingStatusBadge status={document.processing_status} />
                <ArrowUpRight className="h-4 w-4 text-slate-400" />
              </div>
            </Link>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-line px-6 py-8 text-sm text-slate-600">
            {messages.documents.panel.empty}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
