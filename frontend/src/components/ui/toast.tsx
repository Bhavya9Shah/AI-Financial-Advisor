/**
 * src/components/ui/toast.tsx
 * ============================
 * Lightweight toast notification system.
 *
 * Architecture:
 * - ToastProvider wraps the app (in layout.tsx) and owns the toast queue state.
 * - useToast() hook returns addToast() — call it from any component or hook.
 * - ToastContainer renders the live region and animates toasts in/out.
 *
 * Design decisions:
 * - No external library (sonner, react-hot-toast) — the requirements are
 *   simple enough that a ~100-line implementation is cleaner than a dep.
 * - Auto-dismiss after `duration` ms (default 4000). Error toasts stay
 *   for 6000ms by default. Manual dismiss via the X button.
 * - Framer Motion handles enter/exit animations — consistent with the
 *   rest of the UI's animation layer.
 * - ARIA live region ensures screen readers announce toasts.
 */

"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, CheckCheck, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { generateId } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────

export type ToastVariant = "success" | "error" | "info" | "default";

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
  duration: number;
}

export interface AddToastOptions {
  variant?: ToastVariant;
  duration?: number;
}

// ── Context ────────────────────────────────────────────────────────────────

interface ToastContextValue {
  addToast: (message: string, options?: AddToastOptions) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

// ── Provider ───────────────────────────────────────────────────────────────

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback(
    (message: string, options: AddToastOptions = {}) => {
      const { variant = "default", duration } = options;
      const resolvedDuration = duration ?? (variant === "error" ? 6000 : 4000);
      const id = generateId("toast");
      setToasts((prev) => [...prev, { id, message, variant, duration: resolvedDuration }]);
    },
    []
  );

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useToast(): ToastContextValue {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }
  return ctx;
}

// ── Individual toast ────────────────────────────────────────────────────────

const variantStyles: Record<ToastVariant, string> = {
  success: "border-[var(--success)]/30 bg-[var(--success-subtle)] text-[var(--success)]",
  error:   "border-[var(--danger)]/30 bg-[var(--danger-subtle)] text-[var(--danger)]",
  info:    "border-[var(--info)]/30 bg-[var(--info-subtle)] text-[var(--info)]",
  default: "border-[var(--border)] bg-[var(--surface-raised)] text-[var(--text-primary)]",
};

const variantIcon: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCheck className="h-4 w-4 shrink-0" />,
  error:   <AlertCircle className="h-4 w-4 shrink-0" />,
  info:    <Info className="h-4 w-4 shrink-0" />,
  default: null,
};

function ToastItem({
  toast,
  onRemove,
}: {
  toast: Toast;
  onRemove: (id: string) => void;
}) {
  React.useEffect(() => {
    const timer = setTimeout(() => onRemove(toast.id), toast.duration);
    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.96 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "flex items-start gap-3 rounded-[var(--radius-lg)] border px-4 py-3",
        "text-sm font-medium shadow-lg backdrop-blur-sm",
        "min-w-[260px] max-w-[400px]",
        variantStyles[toast.variant]
      )}
      role="alert"
      aria-live="polite"
    >
      {variantIcon[toast.variant]}
      <span className="flex-1 leading-snug">{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        className="ml-1 shrink-0 rounded-sm opacity-60 hover:opacity-100 transition-opacity focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-current"
        aria-label="Dismiss notification"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </motion.div>
  );
}

// ── Container ────────────────────────────────────────────────────────────────

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2"
      aria-label="Notifications"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>
  );
}