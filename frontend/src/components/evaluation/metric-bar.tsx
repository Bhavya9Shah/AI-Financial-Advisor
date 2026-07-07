"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  scoreToColorToken,
  scoreToPercent,
} from "@/lib/utils";
import type { MetricDetail, MetricName } from "@/types/api";

export interface MetricBarProps {
  name: MetricName;
  metric: MetricDetail;
}

export function MetricBar({
  name,
  metric,
}: MetricBarProps) {
  const percentage = scoreToPercent(metric.score);
  const colorToken = scoreToColorToken(metric.score);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium capitalize text-[var(--text-primary)]">
            {name}
          </p>

          <p className="mt-0.5 text-[10px] text-[var(--text-tertiary)]">
            {metric.reasoning}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <span className="font-data text-xs font-semibold text-[var(--text-primary)]">
            {percentage}%
          </span>

          <Badge variant={colorToken}>
            {metric.label}
          </Badge>
        </div>
      </div>

      <Progress
        value={percentage}
        variant={colorToken}
      />

      {metric.evidence.length > 0 && (
        <div className="flex flex-col gap-1">
          {metric.evidence.map((item, index) => (
            <p
              key={`${name}-evidence-${index}`}
              className="font-data text-[10px] leading-4 text-[var(--text-tertiary)]"
            >
              • {item}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}