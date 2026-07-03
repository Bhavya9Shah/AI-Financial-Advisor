/**
 * src/types/api.ts
 * =================
 * TypeScript types mirroring the FinSight FastAPI backend's Pydantic
 * schemas field-for-field. Keeping these in sync with app/schemas.py
 * means a contract drift is caught at compile time, not at runtime.
 */

// ─────────────────────────────────────────────────────────────────────────
// Shared envelope
// ─────────────────────────────────────────────────────────────────────────

export interface BaseResponse {
  success: boolean;
  error: string | null;
  timestamp: string;
}

// ─────────────────────────────────────────────────────────────────────────
// GET /
// ─────────────────────────────────────────────────────────────────────────

export interface RootResponse extends BaseResponse {
  name: string;
  version: string;
  description: string;
  docs_url: string;
}

// ─────────────────────────────────────────────────────────────────────────
// GET /health
// ─────────────────────────────────────────────────────────────────────────

export type HealthStatus = "ok" | "degraded" | "down";

export interface HealthResponse extends BaseResponse {
  status: HealthStatus;
  dependencies: Record<string, string>;
}

// ─────────────────────────────────────────────────────────────────────────
// POST /chat
// ─────────────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface MessageRecord {
  role: MessageRole;
  content: string;
}

export interface ChatRequest {
  message: string;
  history: MessageRecord[];
  session_id: string;
}

export interface ToolCallRecord {
  tool_name: string;
  arguments: Record<string, unknown>;
  output: Record<string, unknown> | string;
  success: boolean;
  latency_ms: number | null;
}

export interface ChatResponse extends BaseResponse {
  answer: string;
  tool_calls: ToolCallRecord[];
  session_id: string;
  latency_ms: number;
  reasoning: string[];
}

// ─────────────────────────────────────────────────────────────────────────
// POST /evaluate
// ─────────────────────────────────────────────────────────────────────────

export interface EvaluateRequest {
  query: string;
  tool_outputs: Record<string, unknown>[];
  response: string;
  expected_numeric_values?: Record<string, number>;
  required_topics?: string[];
  required_caveats?: string[];
  forbidden_claims?: string[];
}

export type MetricLabel = "EXCELLENT" | "GOOD" | "PASS" | "PARTIAL" | "FAIL";

export interface MetricDetail {
  score: number;
  label: MetricLabel;
  passed: boolean;
  reasoning: string;
  evidence: string[];
}

/** The five evaluation dimensions FinSight's metrics.py always returns. */
export type MetricName =
  | "correctness"
  | "grounding"
  | "completeness"
  | "helpfulness"
  | "clarity"
  |  "hallucination";

export interface EvaluateResponse extends BaseResponse {
  weighted_total: number;
  passed: boolean;
  metrics: Partial<Record<MetricName, MetricDetail>>;
}

// ─────────────────────────────────────────────────────────────────────────
// POST /profile
// ─────────────────────────────────────────────────────────────────────────

export type ProfileFieldName =
  | "name"
  | "age"
  | "monthly_income"
  | "monthly_expenses"
  | "risk_tolerance"
  | "investment_horizon_years"
  | "financial_goals"
  | "emergency_fund_months"
  | "has_loans"
  | "favorite_stock"
  | "favorite_sector"
  | "financial_goal";

export interface ProfileField {
  field: ProfileFieldName;
  value: string | number | boolean | string[];
}

export interface ProfileRequest {
  updates: ProfileField[];
}

export interface ProfileCompleteness {
  is_complete: boolean;
  tier: "basic" | "intermediate" | "complete";
  completeness_pct: number;
  missing_required: { field: string; label: string }[];
  missing_optional: { field: string; label: string }[];
  filled_count: number;
  total_count: number;
}

export interface UserProfile {
  name?: string | null;
  age?: number | null;
  monthly_income?: number | null;
  monthly_expenses?: number | null;
  risk_tolerance?: string | null;
  investment_horizon_years?: number | null;
  financial_goals?: string[];
  emergency_fund_months?: number | null;
  has_loans?: boolean | null;
  favorite_stock?: string | null;
  favorite_sector?: string | null;
  financial_goal?: string | null;
}

export interface ProfileResponse extends BaseResponse {
  profile: UserProfile;
  updated_fields: string[];
  completeness: ProfileCompleteness;
}

// ─────────────────────────────────────────────────────────────────────────
// Client-side derived types (not from backend — used for UI state only)
// ─────────────────────────────────────────────────────────────────────────

/** A single rendered chat turn, including UI-only metadata. */
export interface ChatTurn {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls?: ToolCallRecord[];
  reasoning?: string[];
  latencyMs?: number;
  evaluation?: EvaluateResponse;
  isStreaming?: boolean;
  timestamp: number;
}

/** Reasoning timeline step, derived from ToolCallRecord + reasoning[] for display. */
export type ReasoningStepStatus = "pending" | "active" | "done" | "error";

export interface ReasoningStep {
  id: string;
  label: string;
  status: ReasoningStepStatus;
  detail?: string;
}

/** Connection state for the health/status indicator in the UI shell. */
export type ApiConnectionState = "checking" | "online" | "degraded" | "offline";