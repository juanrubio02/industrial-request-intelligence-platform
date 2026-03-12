import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/hooks";
import type { DocumentDetectedType, DocumentProcessingStatus } from "@/lib/api/types";

const PROCESSING_STATUS_VARIANTS: Record<
  DocumentProcessingStatus,
  "success" | "warning" | "danger" | "neutral" | "info"
> = {
  PENDING: "neutral",
  PROCESSING: "info",
  PROCESSED: "success",
  FAILED: "danger",
};

export function DocumentProcessingStatusBadge({
  status,
}: {
  status: DocumentProcessingStatus;
}) {
  const { messages } = useI18n();

  return (
    <Badge variant={PROCESSING_STATUS_VARIANTS[status]} dot>
      {messages.documents.processingStatuses[status]}
    </Badge>
  );
}

export function DocumentTypeBadge({
  value,
}: {
  value: DocumentDetectedType | null | undefined;
}) {
  const { messages } = useI18n();

  if (!value) {
    return <Badge variant="neutral">{messages.documents.detectedTypes.UNKNOWN}</Badge>;
  }

  return (
    <Badge variant="neutral">
      {messages.documents.detectedTypes[value]}
    </Badge>
  );
}
