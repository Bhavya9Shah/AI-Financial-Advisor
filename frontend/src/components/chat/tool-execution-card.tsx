"use client";

import {
  CheckCircle2,
  Clock3,
  Wrench,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  formatLatency,
  stringifyToolOutput,
} from "@/lib/utils";
import type { ToolCallRecord } from "@/types/api";

export interface ToolExecutionCardProps {
  toolCall: ToolCallRecord;
}

export function ToolExecutionCard({
  toolCall,
}: ToolExecutionCardProps) {
  const argumentsText = JSON.stringify(toolCall.arguments, null, 2);
  const outputText = stringifyToolOutput(toolCall.output);

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
            <Wrench className="h-3.5 w-3.5 text-[var(--accent)]" />
          </div>

          <div className="min-w-0">
            <p className="truncate font-data text-xs font-medium text-[var(--text-primary)]">
              {toolCall.tool_name}
            </p>

            <p className="text-[10px] text-[var(--text-tertiary)]">
              Tool execution
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {toolCall.latency_ms !== null && (
            <span className="flex items-center gap-1 font-data text-[10px] text-[var(--text-tertiary)]">
              <Clock3 className="h-3 w-3" />

              {formatLatency(toolCall.latency_ms)}
            </span>
          )}

          <Badge variant={toolCall.success ? "online" : "offline"}>
            {toolCall.success ? (
              <CheckCircle2 className="h-3 w-3" />
            ) : (
              <XCircle className="h-3 w-3" />
            )}

            {toolCall.success ? "Success" : "Failed"}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 p-4">
        <section>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
            Arguments
          </p>

          <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-[var(--radius-md)] bg-[var(--background)] p-3 font-data text-[10px] leading-5 text-[var(--text-secondary)]">
            {argumentsText}
          </pre>
        </section>

        <section>
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
            Output
          </p>

          <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-[var(--radius-md)] bg-[var(--background)] p-3 font-data text-[10px] leading-5 text-[var(--text-secondary)]">
            {outputText}
          </pre>
        </section>
      </div>
    </Card>
  );
}