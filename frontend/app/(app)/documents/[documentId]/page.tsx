import { DocumentDetailPanel } from "@/features/documents/components/document-detail-panel";

export default function DocumentDetailPage({
  params,
}: {
  params: { documentId: string };
}) {
  return <DocumentDetailPanel documentId={params.documentId} />;
}
