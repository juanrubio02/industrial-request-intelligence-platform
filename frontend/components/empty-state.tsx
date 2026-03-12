import { Inbox } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: {
    label: string;
    onClick?: () => void;
    href?: string;
  };
}) {
  return (
    <div className="rounded-3xl border border-dashed border-line bg-white/70 px-8 py-12 text-center shadow-panel">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-surface">
        <Inbox className="h-6 w-6 text-slate-500" />
      </div>
      <h3 className="mt-5 text-lg font-semibold">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">{description}</p>
      {action ? (
        <div className="mt-6">
          {action.href ? (
            <Link
              href={action.href}
              className="inline-flex h-11 items-center justify-center rounded-xl border border-accent bg-accent px-4 text-sm font-medium text-accent-foreground transition hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {action.label}
            </Link>
          ) : (
            <Button type="button" onClick={action.onClick}>
              {action.label}
            </Button>
          )}
        </div>
      ) : null}
    </div>
  );
}
