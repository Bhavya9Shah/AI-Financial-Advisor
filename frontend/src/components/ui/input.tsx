/**
 * src/components/ui/input.tsx
 * ============================
 * Text input component.
 *
 * Design decisions:
 * - Background is var(--surface) not var(--background) — inputs sit slightly
 *   above the page surface so they're visually distinct from the canvas.
 * - Focus ring uses var(--ring) (accent-muted) at reduced opacity — visible
 *   enough for accessibility, subtle enough not to dominate the layout.
 * - Error state adds a danger-colored border without changing layout — no
 *   icons or extra wrappers needed at the primitive level.
 * - `font-data` class is NOT applied by default — numbers-only inputs
 *   (age, income) should add it themselves via className.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Applies danger border color when true. */
  hasError?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, hasError, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-9 w-full rounded-[var(--radius-md)] px-3 py-2",
          "bg-[var(--surface)] text-sm text-[var(--text-primary)]",
          "border border-[var(--border)]",
          "placeholder:text-[var(--text-tertiary)]",
          "transition-colors duration-150",
          "focus-visible:outline-none focus-visible:ring-2",
          "focus-visible:ring-[var(--ring)] focus-visible:ring-offset-1",
          "focus-visible:ring-offset-[var(--background)]",
          "focus-visible:border-[var(--accent-muted)]",
          "disabled:cursor-not-allowed disabled:opacity-40",
          "hover:border-[var(--border-strong)]",
          hasError && "border-[var(--danger)] focus-visible:ring-[var(--danger)]/50",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };