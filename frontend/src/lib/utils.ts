/**
 * src/lib/utils.ts
 * ================
 * Shared, pure utility functions used across the FinSight frontend.
 * No component-specific logic lives here — only generic formatting
 * and the shadcn/ui standard className merger.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class strings safely, resolving conflicts (e.g.
 * "px-2 px-4" → "px-4") via tailwind-merge, and handling conditional
 * classes via clsx. This is the standard shadcn/ui pattern — every
 * shadcn component imports this.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as Indian Rupees with lakh/crore-aware grouping.
 * 90000 -> "₹90,000"   1161695 -> "₹11,61,695"
 */
export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format a plain number with Indian digit grouping, no currency symbol.
 */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-IN").format(value);
}

/**
 * Format a latency value in milliseconds for display.
 * < 1000ms -> "342ms"   >= 1000ms -> "2.1s"
 */
export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || Number.isNaN(ms)) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * Format a timestamp (epoch ms) as a short relative time string.
 * Falls back to a locale time string beyond 24 hours.
 */
export function formatRelativeTime(epochMs: number): string {
  const diffSec = Math.floor((Date.now() - epochMs) / 1000);
  if (diffSec < 5) return "just now";
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return new Date(epochMs).toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric",
  });
}

/**
 * Round a 0–1 metric score to a 0–100 percentage for progress bars.
 */
export function scoreToPercent(score: number): number {
  return Math.round(Math.max(0, Math.min(1, score)) * 100);
}

/**
 * Generate a short, sufficiently-unique client-side ID for React keys
 * and session correlation. Not cryptographically secure — UI use only.
 */
export function generateId(prefix = "id"): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Truncate a string to a maximum length, appending an ellipsis if cut.
 * Used for long JSON values or tool arguments in compact UI contexts.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

/**
 * Safely stringify a tool output value for display, whether it's
 * already a string or a JSON-serialisable object.
 */
export function stringifyToolOutput(
  output: Record<string, unknown> | string
): string {
  if (typeof output === "string") return output;
  try {
    return JSON.stringify(output, null, 2);
  } catch {
    return String(output);
  }
}

/**
 * Map a metric score (0-1) to a semantic CSS color token name.
 * Used by progress bars and pills to color-code evaluation results.
 */
export function scoreToColorToken(
  score: number
): "excellent" | "good" | "pass" | "partial" | "fail" {
  if (score >= 0.85) return "excellent";
  if (score >= 0.7) return "good";
  if (score >= 0.6) return "pass";
  if (score >= 0.4) return "partial";
  return "fail";
}