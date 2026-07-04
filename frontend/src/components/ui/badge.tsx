/**
 * src/components/ui/badge.tsx
 * ============================
 * Inline status pill for semantic labelling.
 *
 * Used for:
 *   - Metric labels: EXCELLENT, GOOD, PASS, PARTIAL, FAIL
 *   - Health status: online, degraded, offline
 *   - Tool call status: success, failed
 *   - Profile tier: basic, intermediate, complete
 *
 * Each variant uses the subtle background (low-saturation fill) with the
 * full-saturation text — matches the terminal aesthetic without being loud.
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  [
    "inline-flex items-center gap-1 rounded-full px-2 py-0.5",
    "text-[11px] font-semibold leading-none tracking-wide",
    "border transition-colors",
  ],
  {
    variants: {
      variant: {
        // Metric evaluation results
        excellent: "bg-[var(--success-subtle)] text-[var(--success)] border-[var(--success)]/20",
        good:      "bg-[var(--info-subtle)] text-[var(--info)] border-[var(--info)]/20",
        pass:      "bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent)]/20",
        partial:   "bg-[var(--warning-subtle)] text-[var(--warning)] border-[var(--warning)]/20",
        fail:      "bg-[var(--danger-subtle)] text-[var(--danger)] border-[var(--danger)]/20",
        // Connection / health states
        online:    "bg-[var(--success-subtle)] text-[var(--success)] border-[var(--success)]/20",
        degraded:  "bg-[var(--warning-subtle)] text-[var(--warning)] border-[var(--warning)]/20",
        offline:   "bg-[var(--danger-subtle)] text-[var(--danger)] border-[var(--danger)]/20",
        // Generic neutral
        default:   "bg-[var(--surface-raised)] text-[var(--text-secondary)] border-[var(--border)]",
        // Accent (profile tier: complete)
        accent:    "bg-[var(--accent-subtle)] text-[var(--accent)] border-[var(--accent)]/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };