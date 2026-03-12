import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "success" | "warning" | "danger" | "neutral" | "info";
type BadgeSize = "sm" | "md";

const VARIANT_STYLES: Record<BadgeVariant, string> = {
  success: "border-emerald-200/80 bg-emerald-50 text-emerald-700",
  warning: "border-amber-200/80 bg-amber-50 text-amber-700",
  danger: "border-rose-200/80 bg-rose-50 text-rose-700",
  neutral: "border-slate-200/80 bg-slate-100 text-slate-700",
  info: "border-sky-200/80 bg-sky-50 text-sky-700",
};

export function Badge({
  variant = "neutral",
  size = "md",
  dot = false,
  className,
  children,
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold uppercase tracking-[0.14em]",
        VARIANT_STYLES[variant],
        size === "sm" ? "px-2.5 py-1 text-[0.64rem]" : "px-3 py-1.5 text-[0.68rem]",
        className,
      )}
    >
      {dot ? <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
