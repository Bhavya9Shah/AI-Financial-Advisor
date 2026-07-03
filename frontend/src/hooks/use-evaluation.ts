/**
 * src/hooks/use-evaluation.ts
 * ============================
 * Manages a single /evaluate API call.
 *
 * Design decisions:
 * - Stores only the most recent evaluation result. The chat hook triggers
 *   evaluate() after each agent turn and attaches the result to the turn
 *   object — this hook is the transport, not the store.
 * - `isEvaluating` is separate from the chat's `isLoading` so the UI
 *   can show "Evaluating…" after the agent answers, not during it.
 * - Errors are non-fatal — a failed evaluation does not block the chat.
 *   The result will simply be null for that turn.
 */

"use client";

import { useCallback, useState } from "react";
import { postEvaluate } from "@/services/api";
import { isApiError } from "@/services/api";
import type { EvaluateRequest, EvaluateResponse } from "@/types/api";

export interface UseEvaluationReturn {
  result: EvaluateResponse | null;
  isEvaluating: boolean;
  error: string | null;
  /**
   * Run the evaluation harness. Returns the result so callers can
   * attach it to a chat turn without relying on the state update timing.
   */
  evaluate: (request: EvaluateRequest) => Promise<EvaluateResponse | null>;
  clearResult: () => void;
}

export function useEvaluation(): UseEvaluationReturn {
  const [result, setResult] = useState<EvaluateResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const evaluate = useCallback(
    async (request: EvaluateRequest): Promise<EvaluateResponse | null> => {
      // Don't kick off a second eval while one is already running
      if (isEvaluating) return null;

      setIsEvaluating(true);
      setError(null);

      try {
        const data = await postEvaluate(request);
        setResult(data);
        return data;
      } catch (err) {
        const msg = isApiError(err) ? err.message : "Evaluation failed.";
        setError(msg);
        return null;
      } finally {
        setIsEvaluating(false);
      }
    },
    [isEvaluating]
  );

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, isEvaluating, error, evaluate, clearResult };
}