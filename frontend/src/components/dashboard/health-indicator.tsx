"use client";

import { RefreshCw, Server } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useHealth } from "@/hooks/use-health";
import { cn } from "@/lib/utils";

export function HealthIndicator() {
  const {
    connectionState,
    health,
    isInitialChecking,
    recheck,
  } = useHealth();

  const badgeVariant =
    connectionState === "online"
      ? "online"
      : connectionState === "degraded"
        ? "degraded"
        : connectionState === "offline"
          ? "offline"
          : "default";

  const connectionLabel =
    connectionState === "checking"
      ? "Checking"
      : connectionState.charAt(0).toUpperCase() +
        connectionState.slice(1);

  const dependencies = health
    ? Object.entries(health.dependencies)
    : [];

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
            <Server className="h-4 w-4 text-[var(--accent)]" />
          </div>

          <div>
            <p className="text-xs font-semibold text-[var(--text-primary)]">
              System Health
            </p>

            <p className="text-[10px] text-[var(--text-tertiary)]">
              FastAPI backend dependencies
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={badgeVariant}>
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                connectionState === "online" &&
                  "bg-[var(--success)]",
                connectionState === "degraded" &&
                  "bg-[var(--warning)]",
                connectionState === "offline" &&
                  "bg-[var(--danger)]",
                connectionState === "checking" &&
                  "bg-[var(--text-tertiary)]"
              )}
            />

            {connectionLabel}
          </Badge>

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={recheck}
            disabled={isInitialChecking}
            aria-label="Recheck system health"
            title="Recheck system health"
          >
            <RefreshCw
              className={cn(
                "h-3.5 w-3.5",
                isInitialChecking && "animate-spin"
              )}
            />
          </Button>
        </div>
      </div>

      <div className="p-4">
        {isInitialChecking && dependencies.length === 0 ? (
          <p className="text-xs text-[var(--text-tertiary)]">
            Checking backend dependencies...
          </p>
        ) : dependencies.length > 0 ? (
          <div className="flex flex-col gap-2">
            {dependencies.map(([name, status]) => (
              <DependencyRow
                key={name}
                name={name}
                status={status}
              />
            ))}
          </div>
        ) : (
          <p className="text-xs text-[var(--text-tertiary)]">
            Backend health information is currently unavailable.
          </p>
        )}
      </div>
    </Card>
  );
}

interface DependencyRowProps {
  name: string;
  status: string;
}

function DependencyRow({
  name,
  status,
}: DependencyRowProps) {
  const normalizedStatus = status.toLowerCase();

  const isHealthy =
    normalizedStatus === "ok" ||
    normalizedStatus === "healthy" ||
    normalizedStatus === "available";

  return (
    <div className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] bg-[var(--background)] px-3 py-2">
      <span className="font-data text-[10px] text-[var(--text-secondary)]">
        {name}
      </span>

      <div className="flex items-center gap-2">
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            isHealthy
              ? "bg-[var(--success)]"
              : "bg-[var(--warning)]"
          )}
        />

        <span className="font-data text-[10px] text-[var(--text-tertiary)]">
          {status}
        </span>
      </div>
    </div>
  );
}