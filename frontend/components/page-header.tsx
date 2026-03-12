import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col justify-between gap-5 rounded-[var(--radius-panel)] border border-line/80 bg-white/92 px-6 py-6 shadow-panel xl:flex-row xl:items-start",
        className,
      )}
    >
      <div className="space-y-3">
        {eyebrow ? (
          <p className="eyebrow">{eyebrow}</p>
        ) : null}
        <h1 className="max-w-4xl text-3xl font-semibold tracking-[-0.03em] text-foreground md:text-[2.2rem]">
          {title}
        </h1>
        {description ? (
          <p className="max-w-3xl text-sm leading-6 text-slate-600 md:text-[0.95rem]">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex flex-wrap items-center gap-2.5 xl:justify-end">{actions}</div>
      ) : null}
    </div>
  );
}
