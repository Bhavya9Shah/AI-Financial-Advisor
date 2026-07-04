/**
 * src/components/ui/skeleton.tsx
 * ================================
 * Skeleton placeholder for loading states.
 *
 * Uses a CSS pulse animation (via Tailwind's `animate-pulse`) rather than
 * a shimmer gradient — shimmer gradients require absolute positioning and
 * overflow:hidden which complicates layout. Pulse is simpler, faster, and
 * sufficient for this use case.
 *
 * Usage:
 *   <Skeleton className="h-4 w-32" />           // single line
 *   <Skeleton className="h-10 w-full" />         // full-width block
 *   <Skeleton className="h-10 w-10 rounded-full" /> // avatar circle
 */

import * as React from "react";
import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-[var(--radius-md)] bg-[var(--surface-raised)]",
        className
      )}
      aria-hidden="true"
      {...props}
    />
  );
}

export { Skeleton };