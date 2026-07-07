"use client";

import {
  Check,
  Circle,
  LoaderCircle,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { ReasoningStep } from "@/types/api";

export interface ReasoningTimelineProps {
  steps: ReasoningStep[];
}

export function ReasoningTimeline({
  steps,
}: ReasoningTimelineProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;

        return (
          <div
            key={step.id}
            className="relative flex gap-3"
          >
            {!isLast && (
              <div
                className={cn(
                  "absolute left-[11px] top-6 h-[calc(100%-8px)] w-px",
                  "bg-[var(--border)]"
                )}
              />
            )}

            <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--surface-raised)]">
              <StepIcon status={step.status} />
            </div>

            <div className={cn("min-w-0 flex-1", !isLast && "pb-5")}>
              <p
                className={cn(
                  "text-xs font-medium",
                  step.status === "error"
                    ? "text-[var(--danger)]"
                    : step.status === "active"
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-primary)]"
                )}
              >
                {step.label}
              </p>

              {step.detail && (
                <p className="mt-1 break-words font-data text-[10px] leading-4 text-[var(--text-tertiary)]">
                  {step.detail}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StepIcon({
  status,
}: {
  status: ReasoningStep["status"];
}) {
  if (status === "done") {
    return (
      <Check
        className="h-3 w-3 text-[var(--success)]"
        aria-hidden="true"
      />
    );
  }

  if (status === "error") {
    return (
      <X
        className="h-3 w-3 text-[var(--danger)]"
        aria-hidden="true"
      />
    );
  }

  if (status === "active") {
    return (
      <LoaderCircle
        className="h-3 w-3 animate-spin text-[var(--accent)]"
        aria-hidden="true"
      />
    );
  }

  return (
    <Circle
      className="h-2.5 w-2.5 text-[var(--text-tertiary)]"
      aria-hidden="true"
    />
  );
}