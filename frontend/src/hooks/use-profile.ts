/**
 * src/hooks/use-profile.ts
 * =========================
 * Manages the persistent user financial profile.
 *
 * Design decisions:
 * - Optimistic updates: updateField writes to local state immediately,
 *   then calls the API. On failure the state rolls back and the error
 *   surfaces — the form never blocks for the round-trip latency.
 * - The profile and completeness metadata are stored together because
 *   they are always fetched together and always rendered together.
 * - profileRef is updated inside a useEffect (not during render) to
 *   satisfy React 19's react-hooks/refs rule.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { postProfile, isApiError } from "@/services/api";
import type {
  ProfileCompleteness,
  ProfileFieldName,
  ProfileResponse,
  UserProfile,
} from "@/types/api";

export interface UseProfileReturn {
  profile: UserProfile;
  completeness: ProfileCompleteness | null;
  isLoading: boolean;
  error: string | null;
  updateField: (
    field: ProfileFieldName,
    value: string | number | boolean | string[]
  ) => Promise<void>;
  fetchProfile: () => Promise<void>;
  clearError: () => void;
}

const EMPTY_PROFILE: UserProfile = {};

const DEFAULT_COMPLETENESS: ProfileCompleteness = {
  is_complete: false,
  tier: "basic",
  completeness_pct: 0,
  missing_required: [],
  missing_optional: [],
  filled_count: 0,
  total_count: 0,
};

export function useProfile(): UseProfileReturn {
  const [profile, setProfile] = useState<UserProfile>(EMPTY_PROFILE);
  const [completeness, setCompleteness] = useState<ProfileCompleteness | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref for stable access inside callbacks — updated via useEffect,
  // not during render, to satisfy react-hooks/refs.
  const profileRef = useRef<UserProfile>(EMPTY_PROFILE);
  const completenessRef = useRef<ProfileCompleteness | null>(null);

  useEffect(() => {
    profileRef.current = profile;
  }, [profile]);

  useEffect(() => {
    completenessRef.current = completeness;
  }, [completeness]);

  const applyResponse = useCallback((data: ProfileResponse) => {
    setProfile(data.profile ?? EMPTY_PROFILE);
    setCompleteness(data.completeness ?? DEFAULT_COMPLETENESS);
  }, []);

  const fetchProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // No dedicated GET /profile endpoint on the backend — read current
      // state by posting the name field with its current value (a no-op
      // that still returns the full profile + completeness in the response).
      // If you add GET /profile to the backend, replace this with getProfile().
      const res = await postProfile({
        updates: [{ field: "name", value: profileRef.current.name ?? "" }],
      });
      applyResponse(res);
    } catch (err) {
      const msg = isApiError(err)
        ? err.message
        : "Failed to load profile. Is the server running?";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [applyResponse]);

  useEffect(() => {
    const run = async () => {
      await fetchProfile();
    };
    void run();
    // Run once on mount — fetchProfile is stable (wrapped in useCallback
    // with no changing deps), so this effect fires exactly once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateField = useCallback(
    async (
      field: ProfileFieldName,
      value: string | number | boolean | string[]
    ): Promise<void> => {
      // Snapshot for rollback using refs (stable, no stale closure risk)
      const previousProfile = profileRef.current;
      const previousCompleteness = completenessRef.current;

      // Optimistic local update — UI responds immediately
      setProfile((prev) => ({ ...prev, [field]: value }));
      setError(null);

      try {
        const res = await postProfile({ updates: [{ field, value }] });
        applyResponse(res);
      } catch (err) {
        // Roll back to the pre-update snapshot
        setProfile(previousProfile);
        setCompleteness(previousCompleteness);
        const msg = isApiError(err)
          ? err.message
          : `Failed to update ${field}.`;
        setError(msg);
        throw err;
      }
    },
    [applyResponse]
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    profile,
    completeness,
    isLoading,
    error,
    updateField,
    fetchProfile,
    clearError,
  };
}