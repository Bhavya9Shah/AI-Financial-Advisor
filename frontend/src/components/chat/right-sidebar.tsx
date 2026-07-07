"use client";

import { Activity, BrainCircuit, Wrench } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ReasoningTimeline } from "@/components/chat/reasoning-timeline";
import { ToolExecutionCard } from "@/components/chat/tool-execution-card";
import { scoreToColorToken } from "@/lib/utils";
import type { ChatTurn, ReasoningStep } from "@/types/api";

export interface RightSidebarProps {
  turn: (ChatTurn & { reasoningSteps?: ReasoningStep[] }) | null;
}

export function RightSidebar({ turn }: RightSidebarProps) {
  const reasoningSteps = turn?.reasoningSteps ?? [];
  const toolCalls = turn?.toolCalls ?? [];
  const evaluation = turn?.evaluation;

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-l border-[var(--border)] bg-[var(--surface)]">
      <div className="flex h-14 shrink-0 items-center border-b border-[var(--border)] px-4">
        <div>
          <p className="text-xs font-semibold text-[var(--text-primary)]">
            Agent Inspector
          </p>

          <p className="text-[10px] text-[var(--text-tertiary)]">
            Reasoning, tools and evaluation
          </p>
        </div>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        {!turn ? (
          <EmptyState />
        ) : (
          <div className="flex flex-col gap-5 p-4">
            <section>
              <SectionHeading
                icon={BrainCircuit}
                title="Reasoning Timeline"
              />

              <Card className="mt-3 p-4">
                {reasoningSteps.length > 0 ? (
                  <ReasoningTimeline steps={reasoningSteps} />
                ) : (
                  <p className="text-xs text-[var(--text-tertiary)]">
                    No reasoning trace available for this response.
                  </p>
                )}
              </Card>
            </section>

            <section>
              <SectionHeading
                icon={Wrench}
                title="Tool Executions"
                count={toolCalls.length}
              />

              <div className="mt-3 flex flex-col gap-3">
                {toolCalls.length > 0 ? (
                  toolCalls.map((toolCall, index) => (
                    <ToolExecutionCard
                      key={`${toolCall.tool_name}-${index}`}
                      toolCall={toolCall}
                    />
                  ))
                ) : (
                  <Card className="p-4">
                    <p className="text-xs text-[var(--text-tertiary)]">
                      No tools were used for this response.
                    </p>
                  </Card>
                )}
              </div>
            </section>

            <section>
              <SectionHeading
                icon={Activity}
                title="Evaluation"
              />

              <Card className="mt-3 p-4">
                {evaluation ? (
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">
                        Weighted score
                      </p>

                      <p className="mt-1 font-data text-xl font-semibold text-[var(--text-primary)]">
                        {Math.round(evaluation.weighted_total * 100)}%
                      </p>
                    </div>

                    <Badge
                      variant={scoreToColorToken(
                        evaluation.weighted_total
                      )}
                    >
                      {evaluation.passed ? "Passed" : "Failed"}
                    </Badge>
                  </div>
                ) : (
                  <p className="text-xs text-[var(--text-tertiary)]">
                    Evaluation is available for responses that use tools.
                  </p>
                )}
              </Card>
            </section>
          </div>
        )}
      </ScrollArea>
    </aside>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-72 flex-col items-center justify-center px-6 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
        <BrainCircuit className="h-5 w-5 text-[var(--accent)]" />
      </div>

      <p className="mt-3 text-xs font-medium text-[var(--text-primary)]">
        No response selected
      </p>

      <p className="mt-1 max-w-48 text-[10px] leading-4 text-[var(--text-tertiary)]">
        Agent reasoning, tool executions and evaluation results will appear
        here.
      </p>
    </div>
  );
}

interface SectionHeadingProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  count?: number;
}

function SectionHeading({
  icon: Icon,
  title,
  count,
}: SectionHeadingProps) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />

      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
        {title}
      </p>

      {count !== undefined && (
        <Badge variant="default" className="ml-auto">
          {count}
        </Badge>
      )}
    </div>
  );
}