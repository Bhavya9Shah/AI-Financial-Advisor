/**
 * src/hooks/use-chat.ts
 * ======================
 * Owns the entire chat conversation lifecycle.
 *
 * Responsibilities:
 * 1. Maintain ordered conversation turns (ChatTurn[]).
 * 2. Build the history array for each /chat POST (all prior turns).
 * 3. Call /chat and parse the response into a ChatTurn.
 * 4. Auto-evaluate the response via /evaluate and attach the result.
 * 5. Derive a ReasoningStep[] timeline from raw reasoning strings
 *    for the animated reasoning panel.
 * 6. Detect profile tool calls and invoke onProfileUpdate().
 * 7. Expose clearChat(), regenerate(), and sendMessage() utilities.
 *
 * Design decisions:
 * - sessionId uses useState lazy initializer (not useRef().current)
 *   to comply with react-hooks/refs.
 * - turnsRef is updated via useEffect (not during render) to comply
 *   with react-hooks/refs.
 * - Auto-evaluation runs only for tool-using turns — pure LLM responses
 *   have no tool outputs to ground against and score trivially.
 * - isSending gates submission — double-submits are impossible.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { postChat, postEvaluate, isApiError } from "@/services/api";
import { generateId } from "@/lib/utils";
import type {
  ChatTurn,
  EvaluateResponse,
  MessageRecord,
  ReasoningStep,
  ReasoningStepStatus,
  ToolCallRecord,
} from "@/types/api";

export interface UseChatOptions {
  sessionId?: string;
  onProfileUpdate?: () => void;
}

export interface UseChatReturn {
  turns: ChatTurn[];
  isSending: boolean;
  error: string | null;
  sessionId: string;
  sendMessage: (message: string) => Promise<void>;
  regenerate: () => Promise<void>;
  clearChat: () => void;
  clearError: () => void;
}

// ── Reasoning step derivation ───────────────────────────────────────────

function deriveReasoningSteps(reasoning: string[]): ReasoningStep[] {
  if (reasoning.length === 0) {
    return [{ id: generateId("step"), label: "Generating answer", status: "done" }];
  }

  return reasoning.map((raw): ReasoningStep => {
    const id = generateId("step");

    if (raw.includes("[model] → calling")) {
      const toolMatch = raw.match(/calling ([a-z_]+)/);
      const argsMatch = raw.match(/args: (.+)$/);
      let args = "";
      try {
        if (argsMatch?.[1]) {
          const parsed = JSON.parse(argsMatch[1]) as Record<string, unknown>;
          args = Object.entries(parsed)
            .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
            .join(", ");
        }
      } catch {
        args = argsMatch?.[1] ?? "";
      }
      return {
        id,
        label: `Calling ${toolMatch?.[1] ?? "tool"}`,
        status: "done" as ReasoningStepStatus,
        detail: args || undefined,
      };
    }

    if (raw.includes("[tool:")) {
      const toolMatch = raw.match(/\[tool:([^\]]+)\]/);
      const success = raw.includes("✓ success");
      return {
        id,
        label: `${toolMatch?.[1] ?? "Tool"} returned`,
        status: success ? "done" : "error",
        detail: success ? undefined : "Tool execution failed",
      };
    }

    if (raw.includes("[model] → final answer")) {
      return { id, label: "Generating answer", status: "done" };
    }

    return {
      id,
      label: raw.replace(/^\[.*?\]\s*→\s*/, "").slice(0, 60),
      status: "done",
    };
  });
}

function hasProfileToolCall(toolCalls: ToolCallRecord[]): boolean {
  return toolCalls.some(
    (tc) =>
      tc.tool_name === "get_user_profile" ||
      tc.tool_name === "update_user_profile"
  );
}

// ── ChatTurn extension for UI ───────────────────────────────────────────
// We attach reasoningSteps directly to the turn object rather than
// maintaining a parallel map — it keeps state in one place.
export type ChatTurnWithSteps = ChatTurn & {
  reasoningSteps?: ReasoningStep[];
};

// ── Hook ─────────────────────────────────────────────────────────────────

const TYPING_CONTENT = "__typing__";

export function useChat({
  sessionId: initialSessionId,
  onProfileUpdate,
}: UseChatOptions = {}): UseChatReturn {
  // useState lazy initializer — stable ID without accessing .current during render
  const [sessionId] = useState<string>(
    () => initialSessionId ?? generateId("session")
  );

  const [turns, setTurns] = useState<ChatTurnWithSteps[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref for stable access in async callbacks — mutated via useEffect only
  const turnsRef = useRef<ChatTurnWithSteps[]>([]);
  useEffect(() => {
    turnsRef.current = turns;
  }, [turns]);

  // ── History builder ──────────────────────────────────────────────────

  function buildHistory(currentTurns: ChatTurnWithSteps[]): MessageRecord[] {
    return currentTurns
      .filter((t) => t.content !== TYPING_CONTENT)
      .map((t) => ({ role: t.role, content: t.content }));
  }

  // ── Turn mutation helpers ─────────────────────────────────────────────

  function appendTurn(turn: ChatTurnWithSteps): void {
    setTurns((prev) => [...prev, turn]);
  }

  function replaceTurn(id: string, replacement: ChatTurnWithSteps): void {
    setTurns((prev) => prev.map((t) => (t.id === id ? replacement : t)));
  }

  function removeTurn(id: string): void {
    setTurns((prev) => prev.filter((t) => t.id !== id));
  }

  // ── Auto-evaluation (non-fatal) ───────────────────────────────────────

  async function runEvaluation(
    query: string,
    toolCalls: ToolCallRecord[],
    answer: string
  ): Promise<EvaluateResponse | null> {
    if (toolCalls.length === 0) return null;
    try {
      return await postEvaluate({
        query,
        tool_outputs: toolCalls.map((tc) =>
          typeof tc.output === "string"
            ? { tool_name: tc.tool_name, raw: tc.output }
            : { tool_name: tc.tool_name, ...tc.output }
        ),
        response: answer,
      });
    } catch {
      return null;
    }
  }

  // ── sendMessage ───────────────────────────────────────────────────────

  const sendMessage = useCallback(
    async (message: string): Promise<void> => {
      if (isSending || !message.trim()) return;

      setIsSending(true);
      setError(null);

      const history = buildHistory(turnsRef.current);

      const userTurn: ChatTurnWithSteps = {
        id: generateId("turn"),
        role: "user",
        content: message.trim(),
        timestamp: Date.now(),
      };
      appendTurn(userTurn);

      const typingId = generateId("turn");
      const typingTurn: ChatTurnWithSteps = {
        id: typingId,
        role: "assistant",
        content: TYPING_CONTENT,
        isStreaming: true,
        timestamp: Date.now(),
      };
      appendTurn(typingTurn);

      try {
        const response = await postChat({
          message: message.trim(),
          history,
          session_id: sessionId,
        });

        const evalResult = await runEvaluation(
          message,
          response.tool_calls ?? [],
          response.answer
        );

        const assistantTurn: ChatTurnWithSteps = {
          id: generateId("turn"),
          role: "assistant",
          content: response.answer,
          toolCalls: response.tool_calls ?? [],
          reasoning: response.reasoning ?? [],
          latencyMs: response.latency_ms,
          evaluation: evalResult ?? undefined,
          timestamp: Date.now(),
          reasoningSteps: deriveReasoningSteps(response.reasoning ?? []),
        };

        replaceTurn(typingId, assistantTurn);

        if (hasProfileToolCall(response.tool_calls ?? []) && onProfileUpdate) {
          onProfileUpdate();
        }
      } catch (err) {
        removeTurn(typingId);
        const msg = isApiError(err)
          ? err.message
          : "Something went wrong. Please try again.";
        setError(msg);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, sessionId, onProfileUpdate]
  );

  // ── regenerate ────────────────────────────────────────────────────────

  const regenerate = useCallback(async (): Promise<void> => {
    if (isSending) return;
    const currentTurns = turnsRef.current;
    const lastUserTurn = [...currentTurns].reverse().find((t) => t.role === "user");
    if (!lastUserTurn) return;

    // Remove the last assistant turn (the one we are regenerating)
    const lastAssistantIndex = currentTurns.reduceRight(
      (found, t, i) => (found === -1 && t.role === "assistant" ? i : found),
      -1
    );
    if (lastAssistantIndex !== -1) {
      setTurns((prev) => prev.slice(0, lastAssistantIndex));
    }

    await sendMessage(lastUserTurn.content);
  }, [isSending, sendMessage]);

  // ── clearChat / clearError ────────────────────────────────────────────

  const clearChat = useCallback(() => {
    setTurns([]);
    setError(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    turns,
    isSending,
    error,
    sessionId,
    sendMessage,
    regenerate,
    clearChat,
    clearError,
  };
}