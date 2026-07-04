/**
 * src/components/ui/button.tsx
 * =============================
 * Polymorphic Button component built with class-variance-authority.
 *
 * Variants:
 *   default   — accent-filled, primary action (Send, Update, Evaluate)
 *   secondary — surface-raised, secondary action (Clear, Cancel)
 *   ghost     — transparent, no border; nav items, icon buttons
 *   outline   — border only, no fill; tertiary actions
 *   danger    — danger-coloured fill; destructive actions
 *
 * Sizes:
 *   sm   — 28px tall, compact; toolbar buttons, inline actions
 *   md   — 36px tall, default
 *   lg   — 44px tall; primary CTAs
 *   icon — square, equal width/height; icon-only buttons
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  // Base — shared across all variants
  [
    "inline-flex items-center justify-center gap-2",
    "rounded-[var(--radius-md)] text-sm font-medium",
    "transition-colors duration-150",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-1 focus-visible:ring-offset-[var(--background)]",
    "disabled:pointer-events-none disabled:opacity-40",
    "select-none whitespace-nowrap",
  ],
  {
    variants: {
      variant: {
        default: [
          "bg-[var(--accent)] text-[var(--primary-foreground)]",
          "hover:bg-[var(--accent-muted)]",
          "active:brightness-95",
        ],
        secondary: [
          "bg-[var(--surface-raised)] text-[var(--text-primary)]",
          "border border-[var(--border)] hover:border-[var(--border-strong)]",
          "hover:bg-[var(--surface-hover)]",
        ],
        ghost: [
          "text-[var(--text-secondary)]",
          "hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)]",
        ],
        outline: [
          "border border-[var(--border)] bg-transparent text-[var(--text-primary)]",
          "hover:bg-[var(--surface-hover)] hover:border-[var(--border-strong)]",
        ],
        danger: [
          "bg-[var(--danger)] text-white",
          "hover:brightness-110 active:brightness-95",
        ],
      },
      size: {
        sm: "h-7 px-3 text-xs",
        md: "h-9 px-4",
        lg: "h-11 px-6 text-base",
        icon: "h-9 w-9 p-0",
        "icon-sm": "h-7 w-7 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Shows a spinning loader in place of children. Implies disabled. */
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <svg
              className="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span className="sr-only">Loading</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };