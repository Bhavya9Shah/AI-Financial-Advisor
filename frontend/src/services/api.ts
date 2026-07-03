/**
 * src/services/api.ts
 * ====================
 * The single Axios client for the FinSight FastAPI backend.
 *
 * Architecture decisions:
 *
 * 1. One client, one base URL. All five endpoints live here.
 *    Nothing outside this file constructs URLs or uses Axios directly.
 *
 * 2. Request interceptor stamps every call with a X-Request-ID so
 *    your FastAPI structured logs and the browser's Network tab show
 *    the same ID — makes debugging cross-layer much faster.
 *
 * 3. Response interceptor unwraps the BaseResponse envelope. Hooks
 *    receive {answer, tool_calls, …} directly instead of nesting
 *    through .data.data everywhere, while still detecting non-success
 *    responses that the backend returns with HTTP 200 (e.g. partial
 *    profile updates where some fields failed).
 *
 * 4. handleApiError normalises all error shapes into a single ApiError
 *    type so every hook has one catch branch, not three.
 */

import axios, { AxiosError, type AxiosInstance } from "axios";
import type {
  ChatRequest,
  ChatResponse,
  EvaluateRequest,
  EvaluateResponse,
  HealthResponse,
  ProfileRequest,
  ProfileResponse,
  RootResponse,
} from "@/types/api";
import { generateId } from "@/lib/utils";

// ─────────────────────────────────────────────────────────────────────────
// Error type
// ─────────────────────────────────────────────────────────────────────────

export interface ApiError {
  message: string;
  status: number | null;
  requestId: string | null;
}

function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === "object" &&
    value !== null &&
    "message" in value &&
    "status" in value
  );
}

export { isApiError };

// ─────────────────────────────────────────────────────────────────────────
// Client factory
// ─────────────────────────────────────────────────────────────────────────

function createApiClient(): AxiosInstance {
  const baseURL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  const client = axios.create({
    baseURL,
    timeout: 120_000, // 120 s — LLM calls can be slow
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  // ── Request: stamp each call with a correlation ID ───────────────────
  client.interceptors.request.use((config) => {
    config.headers["X-Request-ID"] = generateId("req");
    return config;
  });

  // ── Response: unwrap BaseResponse envelope ───────────────────────────
  // The backend always returns {success, error, timestamp, ...data}.
  // We surface the error field as an exception so hooks only have one
  // code path (the happy path) and one catch branch (any error).
  client.interceptors.response.use(
    (response) => {
      const body = response.data as Record<string, unknown>;
      if (body?.success === false) {
        const msg =
          typeof body.error === "string"
            ? body.error
            : "The server returned an error.";
        const err: ApiError = {
          message: msg,
          status: response.status,
          requestId: response.config.headers?.["X-Request-ID"] as
            | string
            | null,
        };
        return Promise.reject(err);
      }
      return response;
    },
    (error: AxiosError) => {
      return Promise.reject(handleAxiosError(error));
    }
  );

  return client;
}

function handleAxiosError(error: AxiosError): ApiError {
  const requestId = error.config?.headers?.["X-Request-ID"] as
    | string
    | null;

  if (error.response) {
    // Server replied with a non-2xx status
    const body = error.response.data as Record<string, unknown> | undefined;
    const serverMsg =
      typeof body?.error === "string"
        ? body.error
        : typeof body?.detail === "string"
          ? body.detail
          : `Server error ${error.response.status}`;
    return { message: serverMsg, status: error.response.status, requestId };
  }

  if (error.request) {
    // Request was made but no response received (network / timeout)
    return {
      message:
        error.code === "ECONNABORTED"
          ? "Request timed out — the agent may still be processing."
          : "Cannot reach the FinSight API. Is the server running?",
      status: null,
      requestId,
    };
  }

  // Unexpected client-side error building the request
  return {
    message: error.message ?? "An unexpected error occurred.",
    status: null,
    requestId,
  };
}

// Module-level singleton — one instance for the whole app
const apiClient = createApiClient();

// ─────────────────────────────────────────────────────────────────────────
// Endpoint functions
// ─────────────────────────────────────────────────────────────────────────

/**
 * GET /
 * Connectivity ping. Use to test if the server is reachable at all before
 * calling /health (which checks individual dependencies).
 */
export async function getRootInfo(): Promise<RootResponse> {
  const res = await apiClient.get<RootResponse>("/");
  return res.data;
}

/**
 * GET /health
 * Returns the status of each backend dependency independently:
 * google_api_key, agent_module, metrics_module, profile_file.
 * Status is "ok" | "degraded" | "down".
 */
export async function getHealth(): Promise<HealthResponse> {
  const res = await apiClient.get<HealthResponse>("/health");
  return res.data;
}

/**
 * POST /chat
 * Invoke the LangChain ReAct agent with a message and conversation history.
 * Returns the agent's final answer, the tool call trace, the reasoning
 * steps, and the total latency.
 *
 * The caller is responsible for managing history across turns — append
 * the previous messages yourself and pass the full array each time.
 */
export async function postChat(request: ChatRequest): Promise<ChatResponse> {
  const res = await apiClient.post<ChatResponse>("/chat", request);
  return res.data;
}

/**
 * POST /evaluate
 * Run the deterministic evaluation harness over a completed agent turn.
 * Pass the original query, the tool outputs from that turn, and the
 * agent's final response. Returns five metric scores plus a weighted total.
 *
 * Decoupled from /chat so you can evaluate saved transcripts offline.
 */
export async function postEvaluate(
  request: EvaluateRequest
): Promise<EvaluateResponse> {
  const res = await apiClient.post<EvaluateResponse>("/evaluate", request);
  return res.data;
}

/**
 * POST /profile
 * Apply one or more field updates to the persistent user profile JSON.
 * Uses the same update_user_profile tool the agent calls internally, so
 * validation and completeness-tier logic are shared — not duplicated.
 *
 * Returns the full updated profile and completeness metadata.
 */
export async function postProfile(
  request: ProfileRequest
): Promise<ProfileResponse> {
  const res = await apiClient.post<ProfileResponse>("/profile", request);
  return res.data;
}

// Export the raw client for edge cases (e.g. streaming endpoints in future)
export { apiClient };