/**
 * src/components/ui/dialog.tsx
 * ==============================
 * Accessible modal dialog built on the native <dialog> element.
 *
 * Why native <dialog> instead of a div portal?
 * - Native dialog has built-in focus trapping, Escape key handling,
 *   and backdrop click via the ::backdrop pseudo-element.
 * - No need for focus-trap-react or aria-modal workarounds.
 * - The showModal()/close() API is available in all modern browsers.
 *
 * The dialog appearance overrides ::backdrop with our dark overlay
 * via the `backdrop:` Tailwind variant (Tailwind v4 supports this natively).
 *
 * Framer Motion handles the content enter/exit animation — the dialog
 * element itself is always mounted (React controls visibility via the
 * open/close ref calls), and AnimatePresence handles the content scale.
 *
 * Usage:
 *   <Dialog open={isOpen} onClose={() => setIsOpen(false)}>
 *     <DialogHeader>
 *       <DialogTitle>Clear conversation?</DialogTitle>
 *       <DialogDescription>This cannot be undone.</DialogDescription>
 *     </DialogHeader>
 *     <DialogFooter>
 *       <Button variant="secondary" onClick={() => setIsOpen(false)}>Cancel</Button>
 *       <Button variant="danger" onClick={handleConfirm}>Clear</Button>
 *     </DialogFooter>
 *   </Dialog>
 */

"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  /** Max width of the dialog panel. Defaults to "max-w-md". */
  maxWidthClass?: string;
}

function Dialog({ open, onClose, children, maxWidthClass = "max-w-md" }: DialogProps) {
  const dialogRef = React.useRef<HTMLDialogElement>(null);

  // Sync open state with native dialog API
  React.useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Handle backdrop click (native dialog fires "cancel" on Escape)
  React.useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const handleCancel = (e: Event) => {
      e.preventDefault(); // prevent default close so React state stays in sync
      onClose();
    };
    dialog.addEventListener("cancel", handleCancel);
    return () => dialog.removeEventListener("cancel", handleCancel);
  }, [onClose]);

  // Handle click outside the panel (on the backdrop)
  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className={cn(
        // Remove all native dialog styles
        "m-0 max-h-none max-w-none border-0 bg-transparent p-0",
        // Full-viewport positioning
        "fixed inset-0 z-50 flex items-center justify-center",
        // Backdrop
        "backdrop:bg-black/60 backdrop:backdrop-blur-sm",
      )}
      onClick={handleBackdropClick}
    >
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className={cn(
              "relative w-full rounded-[var(--radius-xl)]",
              "border border-[var(--border)] bg-[var(--surface-raised)]",
              "p-0 shadow-2xl",
              maxWidthClass
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
            <button
              onClick={onClose}
              className={cn(
                "absolute right-4 top-4",
                "rounded-sm p-0.5 text-[var(--text-tertiary)]",
                "hover:text-[var(--text-primary)] transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
              )}
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </dialog>
  );
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 border-b border-[var(--border)] px-5 pb-4 pt-5", className)}
      {...props}
    />
  );
}

function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-sm font-semibold text-[var(--text-primary)]", className)}
      {...props}
    />
  );
}

function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-xs text-[var(--text-secondary)] leading-relaxed", className)}
      {...props}
    />
  );
}

function DialogBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}

function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex items-center justify-end gap-2 border-t border-[var(--border)] px-5 py-4",
        className
      )}
      {...props}
    />
  );
}

export { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogBody, DialogFooter };