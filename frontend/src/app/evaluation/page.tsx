"use client";

import { useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Play,
  RotateCcw,
  XCircle,
} from "lucide-react";

import { MetricBar } from "@/components/evaluation/metric-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useEvaluation } from "@/hooks/use-evaluation";
import { scoreToColorToken, scoreToPercent } from "@/lib/utils";
import type { EvaluateRequest, MetricName } from "@/types/api";

const METRIC_ORDER: MetricName[] = [
  "correctness",
  "grounding",
  "completeness",
  "helpfulness",
  "clarity",
];

const EXAMPLE_QUERY =
  "What will be the future value of a ₹10,000 monthly SIP after 10 years at 12% annual return?";

const EXAMPLE_RESPONSE =
  "A ₹10,000 monthly SIP invested for 10 years at an assumed 12% annual return can grow to approximately ₹23.2 lakh. Actual returns may vary because market returns are not guaranteed.";

const EXAMPLE_TOOL_OUTPUT = JSON.stringify(
  [
    {
      tool_name: "calculate_sip_returns",
      monthly_investment: 10000,
      annual_rate: 12,
      years: 10,
      future_value: 2323391,
    },
  ],
  null,
  2
);

export default function EvaluationPage() {
  const {
    result,
    isEvaluating,
    error,
    evaluate,
    clearResult,
  } = useEvaluation();

  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [toolOutputs, setToolOutputs] = useState("[]");
  const [inputError, setInputError] = useState<string | null>(null);

  async function handleEvaluate() {
    setInputError(null);

    if (!query.trim()) {
      setInputError("Enter the original user query.");
      return;
    }

    if (!response.trim()) {
      setInputError("Enter the agent response.");
      return;
    }

    let parsedToolOutputs: Record<string, unknown>[];

    try {
      const parsed = JSON.parse(toolOutputs) as unknown;

      if (!Array.isArray(parsed)) {
        setInputError("Tool outputs must be a JSON array.");
        return;
      }

      const allObjects = parsed.every(
        (item) =>
          typeof item === "object" &&
          item !== null &&
          !Array.isArray(item)
      );

      if (!allObjects) {
        setInputError(
          "Every tool output must be a JSON object."
        );
        return;
      }

      parsedToolOutputs = parsed as Record<string, unknown>[];
    } catch {
      setInputError("Tool outputs contain invalid JSON.");
      return;
    }

    const request: EvaluateRequest = {
      query: query.trim(),
      response: response.trim(),
      tool_outputs: parsedToolOutputs,
    };

    await evaluate(request);
  }

  function loadExample() {
    setQuery(EXAMPLE_QUERY);
    setResponse(EXAMPLE_RESPONSE);
    setToolOutputs(EXAMPLE_TOOL_OUTPUT);
    setInputError(null);
    clearResult();
  }

  function resetEvaluation() {
    setQuery("");
    setResponse("");
    setToolOutputs("[]");
    setInputError(null);
    clearResult();
  }

  const overallPercentage = result
    ? scoreToPercent(result.weighted_total)
    : 0;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-6 lg:p-8">
      <section className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-[var(--accent)]" />

            <p className="text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
              Deterministic Evaluation
            </p>
          </div>

          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--text-primary)]">
            Evaluation Harness
          </h1>

          <p className="mt-2 max-w-2xl text-xs leading-5 text-[var(--text-secondary)]">
            Evaluate an agent response across correctness, grounding,
            completeness, helpfulness, and clarity.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadExample}
            disabled={isEvaluating}
          >
            Load Example
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={resetEvaluation}
            disabled={isEvaluating}
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </Button>
        </div>
      </section>

      {(inputError || error) && (
        <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--danger)]/20 bg-[var(--danger-subtle)] px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-[var(--danger)]" />

          <p className="text-xs text-[var(--danger)]">
            {inputError ?? error}
          </p>
        </div>
      )}

      <section className="grid gap-4 lg:grid-cols-[1fr_1.15fr]">
        <Card className="h-fit overflow-hidden">
          <div className="border-b border-[var(--border)] px-5 py-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Evaluation Input
            </h2>

            <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
              Submit a completed agent interaction to the evaluation API.
            </p>
          </div>

          <div className="flex flex-col gap-5 p-5">
            <EvaluationField
              label="Original Query"
              description="The question originally asked by the user."
            >
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Enter the original user query"
              />
            </EvaluationField>

            <EvaluationField
              label="Agent Response"
              description="The final answer generated by the financial agent."
            >
              <textarea
                value={response}
                onChange={(event) => setResponse(event.target.value)}
                placeholder="Enter the agent response"
                rows={6}
                className={[
                  "w-full resize-y rounded-[var(--radius-md)]",
                  "border border-[var(--border)]",
                  "bg-[var(--surface)] px-3 py-2",
                  "text-sm text-[var(--text-primary)]",
                  "placeholder:text-[var(--text-tertiary)]",
                  "transition-colors duration-150",
                  "hover:border-[var(--border-strong)]",
                  "focus-visible:border-[var(--accent-muted)]",
                  "focus-visible:outline-none",
                  "focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
                ].join(" ")}
              />
            </EvaluationField>

            <EvaluationField
              label="Tool Outputs"
              description="JSON array containing the outputs used to ground the response."
            >
              <textarea
                value={toolOutputs}
                onChange={(event) =>
                  setToolOutputs(event.target.value)
                }
                rows={9}
                spellCheck={false}
                className={[
                  "font-data w-full resize-y",
                  "rounded-[var(--radius-md)]",
                  "border border-[var(--border)]",
                  "bg-[var(--background)] px-3 py-2",
                  "text-xs leading-5 text-[var(--text-secondary)]",
                  "transition-colors duration-150",
                  "hover:border-[var(--border-strong)]",
                  "focus-visible:border-[var(--accent-muted)]",
                  "focus-visible:outline-none",
                  "focus-visible:ring-2 focus-visible:ring-[var(--ring)]",
                ].join(" ")}
              />
            </EvaluationField>

            <Button
              size="lg"
              onClick={() => void handleEvaluate()}
              isLoading={isEvaluating}
              className="w-full"
            >
              <Play className="h-4 w-4" />
              Run Evaluation
            </Button>
          </div>
        </Card>

        <div className="flex min-w-0 flex-col gap-4">
          {result ? (
            <>
              <Card className="overflow-hidden">
                <div className="flex items-center justify-between gap-4 border-b border-[var(--border)] px-5 py-4">
                  <div>
                    <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                      Evaluation Result
                    </h2>

                    <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
                      Weighted aggregate performance
                    </p>
                  </div>

                  <Badge
                    variant={scoreToColorToken(
                      result.weighted_total
                    )}
                  >
                    {result.passed ? "PASSED" : "FAILED"}
                  </Badge>
                </div>

                <div className="flex items-center gap-5 p-5">
                  <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--background)]">
                    <span className="font-data text-lg font-semibold text-[var(--text-primary)]">
                      {overallPercentage}%
                    </span>
                  </div>

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      {result.passed ? (
                        <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
                      ) : (
                        <XCircle className="h-4 w-4 text-[var(--danger)]" />
                      )}

                      <p className="text-sm font-medium text-[var(--text-primary)]">
                        {result.passed
                          ? "Evaluation passed"
                          : "Evaluation failed"}
                      </p>
                    </div>

                    <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">
                      The weighted score is calculated from the five
                      deterministic FinSight evaluation dimensions.
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="overflow-hidden">
                <div className="border-b border-[var(--border)] px-5 py-4">
                  <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                    Metric Breakdown
                  </h2>

                  <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
                    Detailed scoring evidence for each evaluation dimension
                  </p>
                </div>

                <div className="flex flex-col gap-6 p-5">
                  {METRIC_ORDER.map((name) => {
                    const metric = result.metrics[name];

                    if (!metric) return null;

                    return (
                      <MetricBar
                        key={name}
                        name={name}
                        metric={metric}
                      />
                    );
                  })}
                </div>
              </Card>
            </>
          ) : (
            <EmptyEvaluationState />
          )}
        </div>
      </section>
    </div>
  );
}

interface EvaluationFieldProps {
  label: string;
  description: string;
  children: React.ReactNode;
}

function EvaluationField({
  label,
  description,
  children,
}: EvaluationFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <div>
        <p className="text-xs font-medium text-[var(--text-primary)]">
          {label}
        </p>

        <p className="mt-0.5 text-[10px] leading-4 text-[var(--text-tertiary)]">
          {description}
        </p>
      </div>

      {children}
    </div>
  );
}

function EmptyEvaluationState() {
  return (
    <Card className="flex min-h-[500px] items-center justify-center p-8">
      <div className="flex max-w-sm flex-col items-center text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--accent-subtle)]">
          <Activity className="h-6 w-6 text-[var(--accent)]" />
        </div>

        <h2 className="mt-4 text-sm font-semibold text-[var(--text-primary)]">
          No evaluation result
        </h2>

        <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">
          Enter an agent interaction or load the example, then run the
          deterministic evaluation harness to inspect its performance.
        </p>
      </div>
    </Card>
  );
}