import { RequestDetailScreen } from "@/features/requests/components/request-detail-screen";

export default function RequestDetailPage({
  params,
}: {
  params: { requestId: string };
}) {
  return <RequestDetailScreen requestId={params.requestId} />;
}
