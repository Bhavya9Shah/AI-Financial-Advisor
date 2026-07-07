"use client";

import { useState } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface ChatInputProps {
  onSend: (message: string) => Promise<void>;
  isSending: boolean;
}

export function ChatInput({ onSend, isSending }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = async () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || isSending) return;

    setMessage("");

    await onSend(trimmedMessage);
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  return (
    <div className="border-t border-[var(--border)] bg-[var(--background)] p-4">
      <div className="mx-auto flex max-w-4xl items-end gap-3">
        <div className="min-w-0 flex-1">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            rows={1}
            placeholder="Ask FinSight about investments, SIPs, stocks, or your financial profile..."
            aria-label="Message FinSight"
            className={[
              "min-h-11 max-h-40 w-full resize-none",
              "rounded-[var(--radius-md)] px-4 py-3",
              "border border-[var(--border)]",
              "bg-[var(--surface)]",
              "text-sm text-[var(--text-primary)]",
              "placeholder:text-[var(--text-tertiary)]",
              "transition-colors duration-150",
              "hover:border-[var(--border-strong)]",
              "focus-visible:outline-none focus-visible:ring-2",
              "focus-visible:ring-[var(--ring)]",
              "focus-visible:ring-offset-1",
              "focus-visible:ring-offset-[var(--background)]",
              "disabled:cursor-not-allowed disabled:opacity-50",
            ].join(" ")}
          />
        </div>

        <Button
          type="button"
          size="icon"
          onClick={() => void handleSubmit()}
          disabled={!message.trim()}
          isLoading={isSending}
          aria-label="Send message"
          title="Send message"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      <p className="mx-auto mt-2 max-w-4xl text-center text-[10px] text-[var(--text-tertiary)]">
        Enter to send · Shift + Enter for a new line
      </p>
    </div>
  );
}