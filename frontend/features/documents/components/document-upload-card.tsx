"use client";

import { useState } from "react";
import { Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUploadDocumentMutation } from "@/features/documents/api";
import { useToast } from "@/hooks/use-toast";
import { interpolate, useI18n } from "@/i18n/hooks";
import { ApiError } from "@/lib/api/client";

export function DocumentUploadCard({ requestId }: { requestId: string }) {
  const [file, setFile] = useState<File | null>(null);
  const mutation = useUploadDocumentMutation(requestId);
  const { pushToast } = useToast();
  const { messages } = useI18n();

  const handleUpload = async () => {
    if (!file) {
      pushToast({
        tone: "error",
        title: messages.documents.upload.noFileTitle,
        description: messages.documents.upload.noFileDescription,
      });
      return;
    }

    try {
      await mutation.mutateAsync(file);
      setFile(null);
      pushToast({
        tone: "success",
        title: messages.documents.upload.successTitle,
        description: messages.documents.upload.successDescription,
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: messages.documents.upload.errorTitle,
        description:
          error instanceof ApiError ? error.detail : messages.documents.upload.fallbackError,
      });
    }
  };

  return (
    <Card>
      <CardHeader>
        <p className="eyebrow">
          {messages.documents.upload.eyebrow}
        </p>
        <CardTitle className="mt-2">{messages.documents.upload.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-[var(--radius-panel)] border border-dashed border-line bg-surface/70 px-4 py-8 text-center transition hover:border-slate-300 hover:bg-surface">
          <Upload className="h-6 w-6 text-slate-500" />
          <p className="mt-3 font-semibold">
            {file
              ? interpolate(messages.documents.upload.dropzoneSelected, { filename: file.name })
              : messages.documents.upload.dropzoneIdle}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {messages.documents.upload.description}
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <Badge variant="neutral" size="sm">
              PDF
            </Badge>
            <Badge variant="neutral" size="sm">
              TXT
            </Badge>
            <Badge variant="neutral" size="sm">
              MD
            </Badge>
          </div>
          <input
            className="sr-only"
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-slate-500">
            {file ? messages.documents.upload.ready : messages.documents.upload.pending}
          </p>
          <Button type="button" onClick={handleUpload} disabled={mutation.isPending}>
            {mutation.isPending
              ? messages.documents.upload.uploading
              : messages.documents.upload.upload}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
