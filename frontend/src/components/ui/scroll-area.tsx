/**
 * src/components/ui/scroll-area.tsx
 * ===================================
 * Custom-scrollbar scroll container.
 *
 * Uses CSS-only custom scrollbars (already defined in globals.css for
 * webkit) rather than a JS scrollbar library. This avoids the layout
 * shifts and reflow costs of virtualised scrollbars, and the webkit
 * styles in globals.css already match the terminal aesthetic.
 *
 * The `maxHeight` prop lets callers set a height constraint without
 * needing to wrap in another div — common pattern in sidebars and panels
 * where the scroll area fills remaining vertical space.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Optional max-height. If omitted, the component fills its parent (h-full). */
  maxHeight?: string;
  /** Axis to scroll. Defaults to "vertical". */
  orientation?: "vertical" | "horizontal" | "both";
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, maxHeight, orientation = "vertical", children, ...props }, ref) => {
    const overflowClass = {
      vertical:   "overflow-y-auto overflow-x-hidden",
      horizontal: "overflow-x-auto overflow-y-hidden",
      both:       "overflow-auto",
    }[orientation];

    return (
      <div
        ref={ref}
        className={cn(
          overflowClass,
          "scrollbar-thin",
          !maxHeight && "h-full",
          className
        )}
        style={maxHeight ? { maxHeight } : undefined}
        {...props}
      >
        {children}
      </div>
    );
  }
);
ScrollArea.displayName = "ScrollArea";

export { ScrollArea };