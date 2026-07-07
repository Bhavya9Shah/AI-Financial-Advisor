"use client";

import { Bot, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  formatLatency,
  formatRelativeTime,
  scoreToColorToken,
} from "@/lib/utils";
import type { ChatTurn } from "@/types/api";

export interface ChatMessageProps {
  turn: ChatTurn;
}

const TYPING_CONTENT = "__typing__";

export function ChatMessage({ turn }: ChatMessageProps) {
  const isUser = turn.role === "user";
  const isTyping = turn.content === TYPING_CONTENT;

  if (isTyping) {
    return (
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
          <Bot className="h-4 w-4 text-[var(--accent)]" />
        </div>

        <Card className="flex items-center gap-1.5 px-4 py-3">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-tertiary)]" />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-tertiary)] [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-tertiary)] [animation-delay:300ms]" />

          <span className="ml-2 text-xs text-[var(--text-tertiary)]">
            FinSight is thinking
          </span>
        </Card>
      </div>
    );
  }

  const weightedTotal = turn.evaluation?.weighted_total;

  const evaluationVariant =
    weightedTotal !== undefined
      ? scoreToColorToken(weightedTotal)
      : undefined;

  return (
    <article
      className={
        isUser
          ? "flex flex-row-reverse items-start gap-3"
          : "flex items-start gap-3"
      }
    >
      <div
        className={
          isUser
            ? "flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-raised)]"
            : "flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]"
        }
      >
        {isUser ? (
          <UserRound className="h-4 w-4 text-[var(--text-secondary)]" />
        ) : (
          <Bot className="h-4 w-4 text-[var(--accent)]" />
        )}
      </div>

      <div
        className={
          isUser
            ? "flex max-w-[75%] flex-col items-end gap-2"
            : "flex max-w-[85%] flex-col gap-2"
        }
      >
        <Card
          className={
            isUser
              ? "bg-[var(--surface-raised)] px-4 py-3"
              : "px-4 py-3"
          }
        >
          <p className="whitespace-pre-wrap text-sm leading-6 text-[var(--text-primary)]">
            {turn.content}
          </p>
        </Card>

        <div className="flex flex-wrap items-center gap-2 px-1">
          <span className="text-[10px] text-[var(--text-tertiary)]">
            {formatRelativeTime(turn.timestamp)}
          </span>

          {!isUser && turn.latencyMs !== undefined && (
            <span className="font-data text-[10px] text-[var(--text-tertiary)]">
              {formatLatency(turn.latencyMs)}
            </span>
          )}

          {!isUser &&
            weightedTotal !== undefined &&
            evaluationVariant !== undefined && (
              <Badge variant={evaluationVariant}>
                Eval {Math.round(weightedTotal * 100)}%
              </Badge>
            )}

          {!isUser &&
            turn.toolCalls !== undefined &&
            turn.toolCalls.length > 0 && (
              <Badge variant="default">
                {turn.toolCalls.length}{" "}
                {turn.toolCalls.length === 1 ? "tool call" : "tool calls"}
              </Badge>
            )}
        </div>
      </div>
    </article>
  );
}