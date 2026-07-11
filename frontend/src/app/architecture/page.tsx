import {
  Activity,
  ArrowDown,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  CircleDot,
  Code2,
  Database,
  FileJson,
  GitBranch,
  Globe2,
  Layers3,
  Network,
  Server,
  ShieldCheck,
  TestTube2,
  UserRound,
  Wrench,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";




const agentTools = [
  {
    name: "get_user_profile",
    detail: "Retrieves persistent financial context.",
  },
  {
    name: "update_user_profile",
    detail: "Validates and updates user profile fields.",
  },
  {
    name: "get_stock_info",
    detail: "Retrieves structured stock market information.",
  },
  {
    name: "calculate_sip_returns",
    detail: "Calculates future SIP investment value.",
  },
  {
    name: "calculate_cagr",
    detail: "Computes compound annual growth rate.",
  },
  {
    name: "get_financial_news",
    detail: "Retrieves financial headlines and sentiment context.",
  },
];

const evaluationMetrics = [
  {
    name: "Correctness",
    detail: "Checks numerical and factual accuracy.",
  },
  {
    name: "Grounding",
    detail: "Measures consistency with available tool outputs.",
  },
  {
    name: "Completeness",
    detail: "Checks whether required information is covered.",
  },
  {
    name: "Helpfulness",
    detail: "Measures practical usefulness of the final answer.",
  },
  {
    name: "Clarity",
    detail: "Evaluates readability and communication quality.",
  },
];

const requestLifecycle = [
  {
    number: "01",
    title: "User submits a financial query",
    detail:
      "The Next.js chat interface captures the message and builds conversation history from previous turns.",
  },
  {
    number: "02",
    title: "Frontend creates the API request",
    detail:
      "The Axios API boundary attaches a correlation request ID and sends the typed request to the FastAPI backend.",
  },
  {
    number: "03",
    title: "FastAPI validates the payload",
    detail:
      "The backend schema layer validates the message, history, and session identifier before agent execution.",
  },
  {
    number: "04",
    title: "The ReAct agent receives context",
    detail:
      "LangChain constructs the agent execution context using the user query, conversation history, model, and available tools.",
  },
  {
    number: "05",
    title: "Gemini reasons about the next action",
    detail:
      "The model decides whether it can answer directly or requires external information or deterministic calculation.",
  },
  {
    number: "06",
    title: "The agent selects a tool",
    detail:
      "When additional context is required, the ReAct loop chooses the appropriate financial or profile tool and generates its arguments.",
  },
  {
    number: "07",
    title: "The tool executes",
    detail:
      "The selected tool validates its inputs, performs its operation, and returns structured output to the agent.",
  },
  {
    number: "08",
    title: "The ReAct loop continues",
    detail:
      "Gemini inspects the tool result and can invoke another tool or proceed to final answer generation.",
  },
  {
    number: "09",
    title: "The final response is generated",
    detail:
      "The agent produces the user-facing answer together with tool-call records, reasoning events, latency, and session metadata.",
  },
  {
    number: "10",
    title: "The frontend receives the response",
    detail:
      "The chat hook replaces its optimistic typing placeholder with the completed assistant turn.",
  },
  {
    number: "11",
    title: "Tool-using responses are evaluated",
    detail:
      "The frontend sends the original query, structured tool outputs, and final answer to the deterministic evaluation endpoint.",
  },
  {
    number: "12",
    title: "Five quality metrics are calculated",
    detail:
      "Correctness, grounding, completeness, helpfulness, and clarity are scored independently and combined into a weighted result.",
  },
  {
    number: "13",
    title: "The complete execution becomes inspectable",
    detail:
      "The UI renders the final answer, reasoning timeline, tool executions, latency, and evaluation result as one traceable interaction.",
  },
];

const engineeringDecisions = [
  {
    title: "Single API Boundary",
    detail:
      "Only services/api.ts knows backend URLs and Axios configuration. UI components never construct endpoints directly.",
    icon: Network,
  },
  {
    title: "Typed Contracts",
    detail:
      "TypeScript interfaces mirror backend schemas so API contract drift can be detected during development.",
    icon: Code2,
  },
  {
    title: "Centralized Error Handling",
    detail:
      "Axios failures, network errors, timeouts, and backend errors are normalized into one ApiError shape.",
    icon: ShieldCheck,
  },
  {
    title: "Inspectable Agent Execution",
    detail:
      "Tool calls and reasoning events are preserved instead of exposing only the final LLM response.",
    icon: BrainCircuit,
  },
  {
    title: "Deterministic Evaluation",
    detail:
      "Response quality is measured through explicit engineering metrics rather than relying only on subjective LLM judging.",
    icon: Activity,
  },
  {
    title: "Persistent Context",
    detail:
      "Financial profile memory allows responses to use stored user context across interactions.",
    icon: Database,
  },
  {
    title: "Separation of Concerns",
    detail:
      "API transport, React state, reusable UI primitives, feature components, and pages live in separate architectural layers.",
    icon: Layers3,
  },
  {
    title: "Correlation IDs",
    detail:
      "Every frontend API request receives an X-Request-ID for cross-layer debugging and structured log correlation.",
    icon: GitBranch,
  },
];

const qualityPipeline = [
  "Unit tests validate deterministic evaluation behavior.",
  "61 automated tests currently verify the evaluation system.",
  "TypeScript strict checking validates frontend contracts.",
  "ESLint checks React and code-quality rules.",
  "GitHub Actions provides automated CI verification.",
  "Health checks expose backend dependency availability.",
  "Structured request IDs support cross-layer debugging.",
];

export default function ArchitecturePage() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 p-6 lg:p-8">
      <ArchitectureHero />

      <SystemOverview />

      <RequestLifecycle />

      <AgentArchitecture />

      <EvaluationArchitecture />

      <DataAndMemoryFlow />

      <EngineeringDecisions />

      <QualityAndObservability />

      <RepositoryStructure />

      <FinalSystemSummary />
    </div>
  );
}

function ArchitectureHero() {
  return (
    <section>
      <div className="flex items-center gap-2">
        <Network className="h-4 w-4 text-[var(--accent)]" />

        <p className="text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
          System Design
        </p>
      </div>

      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text-primary)]">
        FinSight Architecture
      </h1>

      <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
        An inspectable AI financial advisory system combining a typed Next.js
        frontend, FastAPI service layer, LangChain ReAct agent, Gemini model,
        deterministic financial tools, persistent profile memory, structured
        execution traces, and an automated response evaluation framework.
      </p>

      <div className="mt-5 flex flex-wrap gap-2">
        <Badge variant="accent">Next.js</Badge>
        <Badge variant="accent">TypeScript</Badge>
        <Badge variant="accent">FastAPI</Badge>
        <Badge variant="accent">LangChain</Badge>
        <Badge variant="accent">Gemini 2.5 Flash</Badge>
        <Badge variant="accent">ReAct Agent</Badge>
        <Badge variant="accent">Deterministic Evaluation</Badge>
      </div>
    </section>
  );
}

function SystemOverview() {
  return (
    <ArchitectureSection
      icon={Layers3}
      eyebrow="High-Level Architecture"
      title="System Overview"
      description="FinSight is organized as independent layers with explicit responsibilities and typed boundaries."
    >
      <div className="flex flex-col items-center gap-3">
        <ArchitectureLayer
          icon={Globe2}
          label="Presentation Layer"
          title="Next.js Frontend"
          detail="App Router · React 19 · TypeScript · Tailwind CSS · Axios"
        />

        <FlowArrow />

        <ArchitectureLayer
          icon={Network}
          label="Transport Boundary"
          title="Typed API Client"
          detail="Request IDs · Error normalization · Endpoint functions · API contracts"
        />

        <FlowArrow />

        <ArchitectureLayer
          icon={Server}
          label="Application Layer"
          title="FastAPI Backend"
          detail="Schema validation · Endpoint orchestration · Health checks · Structured responses"
        />

        <FlowArrow />

        <ArchitectureLayer
          icon={BrainCircuit}
          label="Intelligence Layer"
          title="LangChain ReAct Agent"
          detail="Gemini reasoning · Tool selection · Iterative execution · Final synthesis"
        />

        <FlowArrow />

        <div className="grid w-full gap-3 md:grid-cols-3">
          <ArchitectureLayer
            icon={Wrench}
            label="Capability Layer"
            title="Financial Tools"
            detail="Profile · Stocks · SIP · CAGR · Financial News"
          />

          <ArchitectureLayer
            icon={Database}
            label="Memory Layer"
            title="Persistent Profile"
            detail="Financial context · Completeness · Derived state"
          />

          <ArchitectureLayer
            icon={Activity}
            label="Quality Layer"
            title="Evaluation Engine"
            detail="Five metrics · Weighted score · Evidence · Pass/fail"
          />
        </div>

        <FlowArrow />

        <ArchitectureLayer
          icon={Activity}
          label="Inspection Layer"
          title="Observable User Interface"
          detail="Answer · Reasoning timeline · Tool executions · Latency · Evaluation"
        />
      </div>
    </ArchitectureSection>
  );
}

function RequestLifecycle() {
  return (
    <ArchitectureSection
      icon={Zap}
      eyebrow="End-to-End Execution"
      title="Complete Request Lifecycle"
      description="Every user interaction moves through a traceable thirteen-step pipeline."
    >
      <div className="grid gap-3 lg:grid-cols-2">
        {requestLifecycle.map((step) => (
          <Card key={step.number} className="p-4">
            <div className="flex items-start gap-4">
              <span className="font-data text-xs font-semibold text-[var(--accent)]">
                {step.number}
              </span>

              <div>
                <h3 className="text-xs font-semibold text-[var(--text-primary)]">
                  {step.title}
                </h3>

                <p className="mt-1.5 text-[10px] leading-5 text-[var(--text-secondary)]">
                  {step.detail}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </ArchitectureSection>
  );
}

function AgentArchitecture() {
  return (
    <ArchitectureSection
      icon={Bot}
      eyebrow="Agent Intelligence"
      title="ReAct Agent Execution"
      description="The agent follows an iterative reasoning and tool-execution loop instead of generating every answer directly."
    >
      <Card className="overflow-hidden">
        <div className="grid gap-px bg-[var(--border)] lg:grid-cols-5">
          <AgentStage
            number="01"
            title="Observe"
            detail="Receive query, history, and available context."
          />

          <AgentStage
            number="02"
            title="Reason"
            detail="Gemini determines the information required."
          />

          <AgentStage
            number="03"
            title="Act"
            detail="Select a tool and generate validated arguments."
          />

          <AgentStage
            number="04"
            title="Inspect"
            detail="Consume structured tool output and continue reasoning."
          />

          <AgentStage
            number="05"
            title="Answer"
            detail="Synthesize the final grounded response."
          />
        </div>
      </Card>

      <div className="mt-4">
        <SubsectionTitle
          title="Agent Tool Registry"
          description="Six specialized capabilities are exposed to the ReAct agent."
        />

        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {agentTools.map((tool) => (
            <Card key={tool.name} className="p-4">
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
                  <Wrench className="h-3.5 w-3.5 text-[var(--accent)]" />
                </div>

                <div className="min-w-0">
                  <p className="font-data break-all text-[11px] font-semibold text-[var(--text-primary)]">
                    {tool.name}
                  </p>

                  <p className="mt-1.5 text-[10px] leading-4 text-[var(--text-secondary)]">
                    {tool.detail}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </ArchitectureSection>
  );
}

function EvaluationArchitecture() {
  return (
    <ArchitectureSection
      icon={Activity}
      eyebrow="Quality Engineering"
      title="Deterministic Evaluation Pipeline"
      description="Tool-using responses are evaluated independently from the chat endpoint so evaluation remains reusable and testable."
    >
      <div className="grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr] lg:items-center">
        <PipelineCard
          icon={FileJson}
          title="Evaluation Input"
          items={[
            "Original query",
            "Structured tool outputs",
            "Final agent response",
            "Optional expected values",
            "Required topics and caveats",
          ]}
        />

        <HorizontalArrow />

        <PipelineCard
          icon={TestTube2}
          title="Metric Engine"
          items={[
            "Deterministic checks",
            "Evidence extraction",
            "Individual scores",
            "Semantic labels",
            "Pass/fail decisions",
          ]}
        />

        <HorizontalArrow />

        <PipelineCard
          icon={Activity}
          title="Evaluation Output"
          items={[
            "Five metric results",
            "Weighted total",
            "Overall pass/fail",
            "Reasoning",
            "Supporting evidence",
          ]}
        />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {evaluationMetrics.map((metric, index) => (
          <Card key={metric.name} className="p-4">
            <span className="font-data text-[10px] text-[var(--accent)]">
              METRIC {String(index + 1).padStart(2, "0")}
            </span>

            <h3 className="mt-2 text-xs font-semibold text-[var(--text-primary)]">
              {metric.name}
            </h3>

            <p className="mt-1.5 text-[10px] leading-4 text-[var(--text-secondary)]">
              {metric.detail}
            </p>
          </Card>
        ))}
      </div>
    </ArchitectureSection>
  );
}

function DataAndMemoryFlow() {
  return (
    <ArchitectureSection
      icon={Database}
      eyebrow="State & Persistence"
      title="Profile Memory and Data Flow"
      description="Persistent profile context is separated from temporary frontend conversation state."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <CardHeader
            icon={UserRound}
            title="Persistent Financial Profile"
            subtitle="Long-lived user context"
          />

          <div className="flex flex-col gap-3 p-5">
            <FlowItem
              title="Profile fields"
              detail="Income, expenses, risk tolerance, investment horizon, goals, preferences, and other financial context."
            />

            <FlowItem
              title="Validation"
              detail="Profile updates pass through the same backend tool logic used by the AI agent."
            />

            <FlowItem
              title="Completeness tracking"
              detail="Required and optional fields produce a completeness percentage and profile tier."
            />

            <FlowItem
              title="Agent access"
              detail="The ReAct agent can retrieve or update profile context through dedicated tools."
            />
          </div>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader
            icon={Bot}
            title="Conversation State"
            subtitle="Session-scoped interaction context"
          />

          <div className="flex flex-col gap-3 p-5">
            <FlowItem
              title="Chat turns"
              detail="User and assistant messages are maintained by the useChat hook."
            />

            <FlowItem
              title="Conversation history"
              detail="Prior turns are transformed into typed MessageRecord objects for each chat request."
            />

            <FlowItem
              title="Session correlation"
              detail="A stable client-generated session ID identifies the current conversation."
            />

            <FlowItem
              title="Execution metadata"
              detail="Tool calls, reasoning events, latency, and evaluation results are attached to assistant turns."
            />
          </div>
        </Card>
      </div>
    </ArchitectureSection>
  );
}

function EngineeringDecisions() {
  return (
    <ArchitectureSection
      icon={Code2}
      eyebrow="Design Principles"
      title="Key Engineering Decisions"
      description="The system is designed to demonstrate production-oriented separation, observability, and maintainability."
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {engineeringDecisions.map((decision) => {
          const Icon = decision.icon;

          return (
            <Card key={decision.title} className="p-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
                <Icon className="h-4 w-4 text-[var(--accent)]" />
              </div>

              <h3 className="mt-3 text-xs font-semibold text-[var(--text-primary)]">
                {decision.title}
              </h3>

              <p className="mt-1.5 text-[10px] leading-5 text-[var(--text-secondary)]">
                {decision.detail}
              </p>
            </Card>
          );
        })}
      </div>
    </ArchitectureSection>
  );
}

function QualityAndObservability() {
  return (
    <ArchitectureSection
      icon={ShieldCheck}
      eyebrow="Reliability"
      title="Testing, CI, Health, and Observability"
      description="FinSight includes explicit verification and debugging mechanisms across the application lifecycle."
    >
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <Card className="overflow-hidden">
          <CardHeader
            icon={TestTube2}
            title="Quality Pipeline"
            subtitle="Automated engineering verification"
          />

          <div className="flex flex-col gap-3 p-5">
            {qualityPipeline.map((item) => (
              <div key={item} className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--success)]" />

                <p className="text-xs leading-5 text-[var(--text-secondary)]">
                  {item}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader
            icon={Activity}
            title="Observable Execution"
            subtitle="What can be inspected after an agent turn"
          />

          <div className="grid gap-2 p-5">
            {[
              "Final user-facing response",
              "Selected tool names",
              "Generated tool arguments",
              "Structured tool outputs",
              "Tool success or failure",
              "Per-tool execution latency",
              "Agent reasoning timeline",
              "Total response latency",
              "Five evaluation scores",
              "Weighted evaluation result",
            ].map((item, index) => (
              <div
                key={item}
                className="flex items-center gap-3 rounded-[var(--radius-md)] bg-[var(--background)] px-3 py-2"
              >
                <span className="font-data text-[10px] text-[var(--accent)]">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span className="text-[10px] text-[var(--text-secondary)]">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </ArchitectureSection>
  );
}

function RepositoryStructure() {
  return (
    <ArchitectureSection
      icon={GitBranch}
      eyebrow="Code Organization"
      title="Repository Architecture"
      description="Frontend and backend responsibilities are organized into explicit modules rather than concentrated inside page components."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <CardHeader
            icon={Globe2}
            title="Frontend"
            subtitle="Next.js application architecture"
          />

          <div className="p-5">
            <CodeTree
              lines={[
                "frontend/",
                "├── src/app/               # Routes and pages",
                "├── src/components/ui/     # Reusable primitives",
                "├── src/components/layout/ # Application shell",
                "├── src/components/chat/   # Chat inspection UI",
                "├── src/components/dashboard/",
                "├── src/components/evaluation/",
                "├── src/hooks/             # Feature state logic",
                "├── src/services/api.ts    # API boundary",
                "├── src/types/api.ts       # Typed contracts",
                "└── src/lib/utils.ts       # Shared utilities",
              ]}
            />
          </div>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader
            icon={Server}
            title="Backend"
            subtitle="Agent and evaluation architecture"
          />

          <div className="p-5">
            <CodeTree
              lines={[
                "FinSight backend/",
                "├── FastAPI application",
                "├── Pydantic request/response schemas",
                "├── LangChain ReAct agent",
                "├── Financial tool registry",
                "├── Persistent profile storage",
                "├── Evaluation cases",
                "├── Deterministic metrics",
                "├── Automated metric tests",
                "├── requirements.txt",
                "└── GitHub Actions CI workflow",
              ]}
            />
          </div>
        </Card>
      </div>
    </ArchitectureSection>
  );
}

function FinalSystemSummary() {
  return (
    <Card className="overflow-hidden border-[var(--accent)]/20">
      <div className="grid gap-6 p-6 lg:grid-cols-[auto_1fr] lg:items-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--accent-subtle)]">
          <BrainCircuit className="h-7 w-7 text-[var(--accent)]" />
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
            Complete System
          </p>

          <h2 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">
            More than an LLM wrapper
          </h2>

          <p className="mt-2 max-w-4xl text-xs leading-6 text-[var(--text-secondary)]">
            FinSight combines typed frontend engineering, API contracts,
            centralized transport logic, agentic tool execution, persistent
            context, deterministic financial capabilities, response evaluation,
            automated testing, CI verification, health monitoring, correlation
            IDs, and execution inspection into one end-to-end AI engineering
            project.
          </p>
        </div>
      </div>
    </Card>
  );
}

interface ArchitectureSectionProps {
  icon: React.ComponentType<{ className?: string }>;
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}

function ArchitectureSection({
  icon: Icon,
  eyebrow,
  title,
  description,
  children,
}: ArchitectureSectionProps) {
  return (
    <section>
      <div className="mb-4">
        <div className="flex items-center gap-2">
          <Icon className="h-3.5 w-3.5 text-[var(--accent)]" />

          <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--accent)]">
            {eyebrow}
          </p>
        </div>

        <h2 className="mt-2 text-lg font-semibold text-[var(--text-primary)]">
          {title}
        </h2>

        <p className="mt-1 max-w-3xl text-xs leading-5 text-[var(--text-secondary)]">
          {description}
        </p>
      </div>

      {children}
    </section>
  );
}

interface ArchitectureLayerProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  title: string;
  detail: string;
}

function ArchitectureLayer({
  icon: Icon,
  label,
  title,
  detail,
}: ArchitectureLayerProps) {
  return (
    <Card className="w-full p-4">
      <div className="flex items-center gap-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
          <Icon className="h-4 w-4 text-[var(--accent)]" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-[9px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
            {label}
          </p>

          <p className="mt-0.5 text-xs font-semibold text-[var(--text-primary)]">
            {title}
          </p>

          <p className="mt-1 text-[10px] leading-4 text-[var(--text-secondary)]">
            {detail}
          </p>
        </div>
      </div>
    </Card>
  );
}

function FlowArrow() {
  return (
    <div className="flex h-5 items-center justify-center">
      <ArrowDown className="h-4 w-4 text-[var(--text-tertiary)]" />
    </div>
  );
}

function HorizontalArrow() {
  return (
    <div className="hidden items-center justify-center lg:flex">
      <ArrowRight className="h-4 w-4 text-[var(--text-tertiary)]" />
    </div>
  );
}

interface AgentStageProps {
  number: string;
  title: string;
  detail: string;
}

function AgentStage({
  number,
  title,
  detail,
}: AgentStageProps) {
  return (
    <div className="bg-[var(--surface)] p-4">
      <span className="font-data text-[10px] text-[var(--accent)]">
        {number}
      </span>

      <h3 className="mt-2 text-xs font-semibold text-[var(--text-primary)]">
        {title}
      </h3>

      <p className="mt-1.5 text-[10px] leading-4 text-[var(--text-secondary)]">
        {detail}
      </p>
    </div>
  );
}

interface PipelineCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  items: string[];
}

function PipelineCard({
  icon: Icon,
  title,
  items,
}: PipelineCardProps) {
  return (
    <Card className="h-full p-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
        <Icon className="h-4 w-4 text-[var(--accent)]" />
      </div>

      <h3 className="mt-3 text-xs font-semibold text-[var(--text-primary)]">
        {title}
      </h3>

      <div className="mt-3 flex flex-col gap-2">
        {items.map((item) => (
          <div key={item} className="flex items-start gap-2">
            <CircleDot className="mt-0.5 h-3 w-3 shrink-0 text-[var(--text-tertiary)]" />

            <span className="text-[10px] leading-4 text-[var(--text-secondary)]">
              {item}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

interface CardHeaderProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle: string;
}

function CardHeader({
  icon: Icon,
  title,
  subtitle,
}: CardHeaderProps) {
  return (
    <div className="flex items-center gap-3 border-b border-[var(--border)] px-5 py-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
        <Icon className="h-4 w-4 text-[var(--accent)]" />
      </div>

      <div>
        <h3 className="text-xs font-semibold text-[var(--text-primary)]">
          {title}
        </h3>

        <p className="mt-0.5 text-[10px] text-[var(--text-tertiary)]">
          {subtitle}
        </p>
      </div>
    </div>
  );
}

interface FlowItemProps {
  title: string;
  detail: string;
}

function FlowItem({
  title,
  detail,
}: FlowItemProps) {
  return (
    <div className="rounded-[var(--radius-md)] bg-[var(--background)] p-3">
      <p className="text-xs font-medium text-[var(--text-primary)]">
        {title}
      </p>

      <p className="mt-1 text-[10px] leading-4 text-[var(--text-secondary)]">
        {detail}
      </p>
    </div>
  );
}

interface SubsectionTitleProps {
  title: string;
  description: string;
}

function SubsectionTitle({
  title,
  description,
}: SubsectionTitleProps) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-[var(--text-primary)]">
        {title}
      </h3>

      <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
        {description}
      </p>
    </div>
  );
}

interface CodeTreeProps {
  lines: string[];
}

function CodeTree({
  lines,
}: CodeTreeProps) {
  return (
    <div className="overflow-x-auto rounded-[var(--radius-md)] bg-[var(--background)] p-4">
      <pre className="font-data text-[10px] leading-5 text-[var(--text-secondary)]">
        {lines.join("\n")}
      </pre>
    </div>
  );
}