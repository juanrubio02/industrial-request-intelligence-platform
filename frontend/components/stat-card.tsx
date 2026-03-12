import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {label}
        </p>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
      {helper ? (
        <CardContent>
          <p className="text-sm text-slate-600">{helper}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}
