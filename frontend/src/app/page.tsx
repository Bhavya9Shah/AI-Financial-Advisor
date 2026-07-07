import {
  Activity,
  Bot,
  BrainCircuit,
  Network,
  UserRound,
  Wrench,
} from "lucide-react";

import { HealthIndicator } from "@/components/dashboard/health-indicator";
import { Card } from "@/components/ui/card";

const capabilities = [
  {
    title: "AI Financial Advisor",
    description:
      "Ask financial questions and receive responses powered by a tool-calling ReAct agent.",
    icon: Bot,
  },
  {
    title: "Tool Execution",
    description:
      "Inspect the tools selected by the agent, their arguments, outputs, and execution latency.",
    icon: Wrench,
  },
  {
    title: "Evaluation Engine",
    description:
      "Measure agent responses across correctness, grounding, completeness, helpfulness, and clarity.",
    icon: Activity,
  },
  {
    title: "Persistent Profile",
    description:
      "Maintain financial context that allows the agent to provide more personalized responses.",
    icon: UserRound,
  },
];

const architectureItems = [
  "Next.js frontend",
  "FastAPI backend",
  "LangChain ReAct agent",
  "Gemini 2.5 Flash",
  "Deterministic evaluation",
  "Persistent profile memory",
];

export default function DashboardPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 p-6 lg:p-8">
      <section>
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-4 w-4 text-[var(--accent)]" />

          <p className="text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
            FinSight Intelligence Platform
          </p>
        </div>

        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)]">
          AI-powered financial intelligence,
          <br />
          built for inspection.
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
          FinSight combines an AI financial advisor, structured tool execution,
          persistent user context, and deterministic evaluation in one
          inspectable system.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {capabilities.map((capability) => {
          const Icon = capability.icon;

          return (
            <Card key={capability.title} className="p-5">
              <div className="flex items-start gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
                  <Icon className="h-4 w-4 text-[var(--accent)]" />
                </div>

                <div>
                  <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                    {capability.title}
                  </h2>

                  <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">
                    {capability.description}
                  </p>
                </div>
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <HealthIndicator />

        <Card className="overflow-hidden">
          <div className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
              <Network className="h-4 w-4 text-[var(--accent)]" />
            </div>

            <div>
              <p className="text-xs font-semibold text-[var(--text-primary)]">
                System Architecture
              </p>

              <p className="text-[10px] text-[var(--text-tertiary)]">
                Core FinSight technology stack
              </p>
            </div>
          </div>

          <div className="grid gap-2 p-4">
            {architectureItems.map((item, index) => (
              <div
                key={item}
                className="flex items-center gap-3 rounded-[var(--radius-md)] bg-[var(--background)] px-3 py-2"
              >
                <span className="font-data text-[10px] text-[var(--accent)]">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span className="text-xs text-[var(--text-secondary)]">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}