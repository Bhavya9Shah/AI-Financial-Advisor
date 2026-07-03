/**
 * src/hooks/use-health.ts
 * ========================
 * Polls GET /health on mount and every 30 seconds thereafter.
 * Derives a single ApiConnectionState value for the status pill
 * in the app shell — the UI never needs to inspect raw dependency
 * data to decide which color to show.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealth } from "@/services/api";
import type { ApiConnectionState, HealthResponse } from "@/types/api";

const POLL_INTERVAL_MS = 30_000;

export interface UseHealthReturn {
  connectionState: ApiConnectionState;
  health: HealthResponse | null;
  isInitialChecking: boolean;
  recheck: () => void;
}

export function useHealth(): UseHealthReturn {
  const [connectionState, setConnectionState] =
    useState<ApiConnectionState>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isInitialChecking, setIsInitialChecking] = useState(true);

  const check = useCallback(async () => {
    try {
      const data = await getHealth();
      setHealth(data);
      if (data.status === "ok") {
        setConnectionState("online");
      } else if (data.status === "degraded") {
        setConnectionState("degraded");
      } else {
        setConnectionState("offline");
      }
    } catch {
      setHealth(null);
      setConnectionState("offline");
    } finally {
      setIsInitialChecking(false);
    }
  }, []);

  useEffect(() => {
    // React 19 react-hooks/set-state-in-effect: call async fn from
    // inside a nested async IIFE so the effect body itself is synchronous.
    const run = async () => {
      await check();
    };
    void run();

    const intervalId = setInterval(() => {
      void check();
    }, POLL_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [check]);

  return {
    connectionState,
    health,
    isInitialChecking,
    recheck: check,
  };
}