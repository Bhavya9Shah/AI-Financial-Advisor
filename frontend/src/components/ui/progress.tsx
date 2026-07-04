/**
 * src/components/ui/progress.tsx
 * ================================
 * Animated horizontal progress bar.
 *
 * Used exclusively in the evaluation panel to show metric scores (0–100).
 * The fill color is driven by the `variant` prop so the bar communicates
 * semantic meaning (green = excellent, red = fail) without extra wrappers.
 *
 * The fill width animates via a CSS transition on the `style` prop —
 * no Framer Motion needed for this simple case, keeping the component
 * dependency-free and fast.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export type ProgressVariant =
  | "excellent"
  | "good"
  | "pass"
  | "partial"
  | "fail"
  | "default";

const variantFill: Record<ProgressVariant, string> = {
  excellent: "bg-[var(--success)]",
  good:      "bg-[var(--info)]",
  pass:      "bg-[var(--accent)]",
  partial:   "bg-[var(--warning)]",
  fail:      "bg-[var(--danger)]",
  default:   "bg-[var(--accent)]",
};

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Score value 0–100. */
  value: number;
  variant?: ProgressVariant;
  /** Height class, defaults to "h-1.5". */
  heightClass?: string;
  /** Show the numeric label to the right of the bar. */
  showLabel?: boolean;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  (
    {
      className,
      value,
      variant = "default",
      heightClass = "h-1.5",
      showLabel = false,
      ...props
    },
    ref
  ) => {
    const clamped = Math.max(0, Math.min(100, value));
    return (
      <div
        ref={ref}
        className={cn("flex items-center gap-2", className)}
        {...props}
      >
        <div
          className={cn(
            "flex-1 rounded-full bg-[var(--border)]",
            heightClass
          )}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={cn(
              "h-full rounded-full transition-all duration-700 ease-out",
              variantFill[variant]
            )}
            style={{ width: `${clamped}%` }}
          />
        </div>
        {showLabel && (
          <span className="font-data w-8 text-right text-xs text-[var(--text-secondary)]">
            {clamped}%
          </span>
        )}
      </div>
    );
  }
);
Progress.displayName = "Progress";

export { Progress };