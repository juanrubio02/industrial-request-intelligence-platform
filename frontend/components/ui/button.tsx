import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "default" | "sm" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "focus-ring inline-flex items-center justify-center gap-2 rounded-[var(--radius-control)] border text-sm font-medium transition duration-150 disabled:pointer-events-none disabled:opacity-50",
          variant === "primary" &&
            "border-accent bg-accent px-4 text-accentForeground shadow-sm hover:brightness-95",
          variant === "secondary" &&
            "border-line bg-white px-4 text-foreground shadow-sm hover:bg-surfaceMuted",
          variant === "ghost" &&
            "border-transparent px-3 text-foreground hover:bg-surfaceMuted hover:text-slate-950",
          variant === "danger" &&
            "border-rose-600 bg-rose-600 px-4 text-white shadow-sm hover:bg-rose-700",
          size === "default" && "h-11",
          size === "sm" && "h-9 px-3 text-[0.72rem]",
          size === "lg" && "h-12 px-5 text-base",
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
