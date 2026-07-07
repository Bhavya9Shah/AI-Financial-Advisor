"use client";

import { useMemo } from "react";
import { Bot, RotateCcw, Trash2 } from "lucide-react";

import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessage } from "@/components/chat/chat-message";
import { RightSidebar } from "@/components/chat/right-sidebar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/hooks/use-chat";
import type { ChatTurn, ReasoningStep } from "@/types/api";

type ChatTurnWithSteps = ChatTurn & {
  reasoningSteps?: ReasoningStep[];
};

export default function ChatPage() {
  const {
    turns,
    isSending,
    error,
    sendMessage,
    regenerate,
    clearChat,
    clearError,
  } = useChat();

  const latestAssistantTurn = useMemo<ChatTurnWithSteps | null>(() => {
    const assistantTurns = turns.filter(
      (turn) =>
        turn.role === "assistant" &&
        turn.content !== "__typing__"
    );

    return assistantTurns.length > 0
      ? assistantTurns[assistantTurns.length - 1]
      : null;
  }, [turns]);

  return (
    <div className="flex h-[calc(100vh-4rem)] min-h-0">
      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--border)] px-5">
          <div>
            <h1 className="text-sm font-semibold text-[var(--text-primary)]">
              AI Financial Advisor
            </h1>

            <p className="text-[10px] text-[var(--text-tertiary)]">
              LangChain ReAct agent · tool execution · automatic evaluation
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void regenerate()}
              disabled={isSending || turns.length === 0}
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Regenerate
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              disabled={isSending || turns.length === 0}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </Button>
          </div>
        </header>

        {error && (
          <div className="flex shrink-0 items-center justify-between gap-4 border-b border-[var(--danger)]/20 bg-[var(--danger-subtle)] px-5 py-3">
            <p className="text-xs text-[var(--danger)]">
              {error}
            </p>

            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
            >
              Dismiss
            </Button>
          </div>
        )}

        <ScrollArea className="min-h-0 flex-1">
          {turns.length === 0 ? (
            <EmptyChat onSuggestion={sendMessage} />
          ) : (
            <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-8">
              {turns.map((turn) => (
                <ChatMessage
                  key={turn.id}
                  turn={turn}
                />
              ))}
            </div>
          )}
        </ScrollArea>

        <ChatInput
          onSend={sendMessage}
          isSending={isSending}
        />
      </section>

      <RightSidebar turn={latestAssistantTurn} />
    </div>
  );
}

interface EmptyChatProps {
  onSuggestion: (message: string) => Promise<void>;
}

const suggestions = [
  "What can you help me with?",
  "Calculate SIP returns for ₹10,000 per month.",
  "Show me the latest financial news.",
  "What information is missing from my financial profile?",
];

function EmptyChat({
  onSuggestion,
}: EmptyChatProps) {
  return (
    <div className="flex min-h-full items-center justify-center px-6 py-12">
      <div className="flex max-w-xl flex-col items-center text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--accent-subtle)]">
          <Bot className="h-6 w-6 text-[var(--accent)]" />
        </div>

        <h2 className="mt-4 text-lg font-semibold text-[var(--text-primary)]">
          Ask FinSight
        </h2>

        <p className="mt-2 max-w-md text-xs leading-5 text-[var(--text-secondary)]">
          Ask a financial question. FinSight can inspect your profile, calculate
          investment returns, retrieve stock information, and analyze financial
          news using its tools.
        </p>

        <div className="mt-6 grid w-full gap-2 sm:grid-cols-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => void onSuggestion(suggestion)}
              className={[
                "rounded-[var(--radius-md)]",
                "border border-[var(--border)]",
                "bg-[var(--surface)] px-4 py-3",
                "text-left text-xs leading-5",
                "text-[var(--text-secondary)]",
                "transition-colors duration-150",
                "hover:border-[var(--border-strong)]",
                "hover:bg-[var(--surface-hover)]",
                "hover:text-[var(--text-primary)]",
              ].join(" ")}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}