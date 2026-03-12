"use client";

import { useEffect, useMemo, useState } from "react";
import { Cpu, FileCog, ScanSearch } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { DocumentProcessingStatusBadge, DocumentTypeBadge } from "@/features/documents/status-badges";
import {
  useDocumentProcessingResultQuery,
  useDocumentQuery,
  useEnqueueDocumentProcessingMutation,
  useUpdateVerifiedDocumentDataMutation,
} from "@/features/documents/api";
import { useMembership } from "@/hooks/use-membership";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";
import { formatDateTime, formatRelativeFileSize } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

function extractionSignals(structuredData: Record<string, unknown> | null | undefined) {
  const extractionStrategy = structuredData?.text_extraction_strategy;
  const ocrUsed = structuredData?.ocr_used;
  const extractedFields = structuredData?.extracted_fields;

  return { extractionStrategy, ocrUsed, extractedFields };
}

const VERIFIED_FIELD_KEYS = [
  "material",
  "requested_quantity",
  "delivery_deadline",
  "rfq_number",
] as const;

type VerifiedFieldKey = (typeof VERIFIED_FIELD_KEYS)[number];
type VerifiedDataFormState = Record<VerifiedFieldKey, string>;

function normalizeRecord(
  value: Record<string, unknown> | null | undefined,
): Partial<VerifiedDataFormState> {
  if (!value) {
    return {};
  }

  return VERIFIED_FIELD_KEYS.reduce<Partial<VerifiedDataFormState>>((accumulator, key) => {
    const rawValue = value[key];
    accumulator[key] = typeof rawValue === "string" ? rawValue : "";
    return accumulator;
  }, {});
}

function buildVerifiedDataFormState(
  verifiedStructuredData: Record<string, unknown> | null | undefined,
  extractedFields: Record<string, unknown> | null | undefined,
): VerifiedDataFormState {
  const verified = normalizeRecord(verifiedStructuredData);
  const extracted = normalizeRecord(extractedFields);

  return {
    material: verified.material || extracted.material || "",
    requested_quantity: verified.requested_quantity || extracted.requested_quantity || "",
    delivery_deadline: verified.delivery_deadline || extracted.delivery_deadline || "",
    rfq_number: verified.rfq_number || extracted.rfq_number || "",
  };
}

function InlineQueryError({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800">
      {message}
    </div>
  );
}

export function DocumentDetailPanel({ documentId }: { documentId: string }) {
  const { pushToast } = useToast();
  const { activeMembership } = useMembership();
  const { locale, messages } = useI18n();
  const documentQuery = useDocumentQuery(documentId);
  const resultQuery = useDocumentProcessingResultQuery(documentId);
  const requestId = documentQuery.data?.request_id ?? "";
  const enqueueMutation = useEnqueueDocumentProcessingMutation(documentId, requestId);
  const updateVerifiedDataMutation = useUpdateVerifiedDocumentDataMutation(documentId, requestId);
  const canProcess = activeMembership?.role === "OWNER" || activeMembership?.role === "ADMIN";

  if (documentQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <Skeleton className="h-[360px]" />
          <Skeleton className="h-[360px]" />
        </div>
      </div>
    );
  }

  if (documentQuery.isError) {
    return (
        <Card>
        <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
          {messages.documents.detail.loadError}
        </CardContent>
      </Card>
    );
  }

  if (!documentQuery.data) {
    return (
        <Card>
        <CardContent className="px-8 py-10 text-center text-sm text-slate-600">
          {messages.documents.detail.notFound}
        </CardContent>
      </Card>
    );
  }

  const document = documentQuery.data;
  const processingResult = resultQuery.data;
  const signals = extractionSignals(
    (processingResult?.structured_data as Record<string, unknown> | null | undefined) ?? null,
  );
  const hasVerifiedData =
    Boolean(document.verified_structured_data) &&
    Object.keys(document.verified_structured_data ?? {}).length > 0;
  const initialVerifiedData = useMemo(
    () =>
      buildVerifiedDataFormState(
        (document.verified_structured_data as Record<string, unknown> | null | undefined) ?? null,
        (signals.extractedFields as Record<string, unknown> | null | undefined) ?? null,
      ),
    [document.verified_structured_data, signals.extractedFields],
  );
  const [verifiedDataForm, setVerifiedDataForm] = useState<VerifiedDataFormState>(
    initialVerifiedData,
  );

  useEffect(() => {
    setVerifiedDataForm(initialVerifiedData);
  }, [initialVerifiedData]);

  return (
    <div className="page-stack">
      <Card>
        <CardHeader className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="eyebrow">
              {messages.documents.detail.eyebrow}
            </p>
            <CardTitle className="mt-2 text-3xl tracking-[-0.03em]">
              {document.original_filename}
            </CardTitle>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              {messages.documents.detail.description}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant="neutral" size="sm">
                {document.content_type}
              </Badge>
              <Badge variant="neutral" size="sm">
                {formatRelativeFileSize(document.size_bytes, locale)}
              </Badge>
              <Badge variant="info" size="sm">
                {messages.documents.detail.updated} · {formatDateTime(document.updated_at, locale)}
              </Badge>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <DocumentProcessingStatusBadge status={document.processing_status} />
            <Button
              type="button"
              disabled={
                !canProcess ||
                enqueueMutation.isPending ||
                !requestId ||
                document.processing_status !== "PENDING"
              }
              onClick={async () => {
                try {
                  await enqueueMutation.mutateAsync();
                  pushToast({
                    tone: "success",
                    title: messages.documents.detail.processingStartedTitle,
                    description: messages.documents.detail.processingStartedDescription,
                  });
                } catch (error) {
                  pushToast({
                    tone: "error",
                    title: messages.documents.detail.processingErrorTitle,
                    description:
                      error instanceof ApiError
                        ? error.detail
                        : messages.documents.detail.processingErrorDescription,
                  });
                }
              }}
            >
              <Cpu className="h-4 w-4" />
              {document.processing_status === "PENDING"
                ? messages.documents.detail.launchProcessing
                : messages.documents.detail.processingStarted}
            </Button>
          </div>
        </CardHeader>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {messages.documents.detail.metadataEyebrow}
            </p>
            <CardTitle className="mt-2">{messages.documents.detail.metadataTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                {messages.documents.detail.storageKey}
              </p>
              <p className="mt-2 break-all font-[family-name:var(--font-mono)] text-[0.82rem]">
                {document.storage_key}
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {messages.documents.detail.contentType}
                </p>
                <p className="mt-2 font-semibold">{document.content_type}</p>
              </div>
              <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {messages.documents.detail.size}
                </p>
                <p className="mt-2 font-semibold">
                  {formatRelativeFileSize(document.size_bytes, locale)}
                </p>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {messages.documents.detail.created}
                </p>
                <p className="mt-2 font-semibold">{formatDateTime(document.created_at, locale)}</p>
              </div>
              <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {messages.documents.detail.updated}
                </p>
                <p className="mt-2 font-semibold">{formatDateTime(document.updated_at, locale)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {messages.documents.detail.resultEyebrow}
            </p>
            <CardTitle className="mt-2">{messages.documents.detail.resultTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {resultQuery.isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : resultQuery.isError ? (
              <InlineQueryError message={messages.documents.detail.resultLoadError} />
            ) : processingResult ? (
              <>
                <div className="flex flex-wrap items-center gap-3">
                  <DocumentTypeBadge value={processingResult.detected_document_type} />
                  {signals.extractionStrategy ? (
                    <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-slate-600">
                      <ScanSearch className="h-3.5 w-3.5" />
                      {String(signals.extractionStrategy)}
                    </span>
                  ) : null}
                  {signals.ocrUsed ? (
                    <Badge variant="warning" size="sm">
                      {messages.documents.detail.ocrUsed}
                    </Badge>
                  ) : null}
                  <Badge variant={processingResult.status === "PROCESSED" ? "success" : "danger"} size="sm">
                    {messages.documents.detail.resultLabel} · {messages.documents.resultStatuses[processingResult.status]}
                  </Badge>
                  <Badge variant={hasVerifiedData ? "success" : "info"} size="sm">
                    {hasVerifiedData
                      ? messages.documents.verifiedData.humanVerified
                      : messages.documents.verifiedData.aiExtracted}
                  </Badge>
                </div>

                {processingResult.summary ? (
                  <div className="surface-muted rounded-[var(--radius-control)] px-4 py-4">
                    <div className="mb-2 flex items-center gap-2">
                      <FileCog className="h-4 w-4 text-slate-500" />
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                        {messages.documents.detail.summary}
                      </p>
                    </div>
                    <p className="text-sm leading-6 text-slate-700">{processingResult.summary}</p>
                  </div>
                ) : null}

                {processingResult.extracted_text ? (
                  <div className="space-y-3 rounded-[var(--radius-control)] border border-line/70 bg-surface/70 px-4 py-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {messages.documents.detail.extractedText}
                    </p>
                    <pre className="technical-block max-h-[420px] whitespace-pre-wrap">
                      {processingResult.extracted_text}
                    </pre>
                  </div>
                ) : null}

                <div className="space-y-3 rounded-[var(--radius-control)] border border-line/70 bg-surface/70 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {messages.documents.detail.structuredData}
                  </p>
                  <pre className="technical-block whitespace-pre-wrap">
                    {JSON.stringify(processingResult.structured_data ?? {}, null, 2)}
                  </pre>
                </div>

                <div className="space-y-4 rounded-[var(--radius-control)] border border-line/70 bg-surface/70 px-4 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                        {messages.documents.verifiedData.title}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {messages.documents.verifiedData.description}
                      </p>
                    </div>
                    <Badge variant={hasVerifiedData ? "success" : "info"} size="sm">
                      {hasVerifiedData
                        ? messages.documents.verifiedData.humanVerified
                        : messages.documents.verifiedData.aiExtracted}
                    </Badge>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    {VERIFIED_FIELD_KEYS.map((fieldKey) => (
                      <div key={fieldKey} className="space-y-2">
                        <label
                          className="text-sm font-medium"
                          htmlFor={`verified-${fieldKey}`}
                        >
                          {messages.documents.verifiedData.fields[fieldKey]}
                        </label>
                        <Input
                          id={`verified-${fieldKey}`}
                          value={verifiedDataForm[fieldKey]}
                          onChange={(event) =>
                            setVerifiedDataForm((current) => ({
                              ...current,
                              [fieldKey]: event.target.value,
                            }))
                          }
                          placeholder={messages.common.labels.notAvailable}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      disabled={updateVerifiedDataMutation.isPending}
                      onClick={async () => {
                        try {
                          await updateVerifiedDataMutation.mutateAsync({
                            verified_structured_data: verifiedDataForm,
                          });
                          pushToast({
                            tone: "success",
                            title: messages.documents.verifiedData.successTitle,
                            description: messages.documents.verifiedData.successDescription,
                          });
                        } catch (error) {
                          pushToast({
                            tone: "error",
                            title: messages.documents.verifiedData.errorTitle,
                            description:
                              error instanceof ApiError
                                ? error.detail
                                : messages.documents.verifiedData.fallbackError,
                          });
                        }
                      }}
                    >
                      {updateVerifiedDataMutation.isPending
                        ? messages.documents.verifiedData.saving
                        : messages.documents.verifiedData.save}
                    </Button>
                  </div>
                </div>

                {processingResult.error_message ? (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
                    {processingResult.error_message}
                  </div>
                ) : null}
              </>
            ) : (
              <div className="rounded-2xl border border-dashed border-line px-6 py-8 text-sm text-slate-600">
                {messages.documents.detail.noResult}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
