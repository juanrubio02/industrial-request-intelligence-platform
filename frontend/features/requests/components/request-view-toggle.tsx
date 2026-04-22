"use client";

import { LayoutGrid, Rows3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type RequestViewMode = "list" | "pipeline";

export function RequestViewToggle({
  value,
  onChange,
  listLabel,
  pipelineLabel,
}: {
  value: RequestViewMode;
  onChange: (next: RequestViewMode) => void;
  listLabel: string;
  pipelineLabel: string;
}) {
  return (
    <div className="inline-flex rounded-[var(--radius-panel)] border border-line bg-white p-1 shadow-sm">
      <Button
        type="button"
        size="sm"
        variant={value === "list" ? "secondary" : "ghost"}
        aria-pressed={value === "list"}
        className={cn("rounded-[calc(var(--radius-control)-2px)]", value !== "list" && "border-transparent")}
        onClick={() => onChange("list")}
      >
        <Rows3 className="h-4 w-4" />
        {listLabel}
      </Button>
      <Button
        type="button"
        size="sm"
        variant={value === "pipeline" ? "secondary" : "ghost"}
        aria-pressed={value === "pipeline"}
        className={cn(
          "rounded-[calc(var(--radius-control)-2px)]",
          value !== "pipeline" && "border-transparent",
        )}
        onClick={() => onChange("pipeline")}
      >
        <LayoutGrid className="h-4 w-4" />
        {pipelineLabel}
      </Button>
    </div>
  );
}
