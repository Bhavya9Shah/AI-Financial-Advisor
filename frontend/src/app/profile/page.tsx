"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Save,
  UserRound,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useProfile } from "@/hooks/use-profile";
import type {
  ProfileFieldName,
  UserProfile,
} from "@/types/api";

type EditableProfileField = {
  field: ProfileFieldName;
  label: string;
  description: string;
  type: "text" | "number";
  placeholder: string;
};

const PROFILE_FIELDS: EditableProfileField[] = [
  {
    field: "name",
    label: "Name",
    description: "Used to personalize your financial advice.",
    type: "text",
    placeholder: "Enter your name",
  },
  {
    field: "age",
    label: "Age",
    description: "Helps determine investment horizon and risk capacity.",
    type: "number",
    placeholder: "Enter your age",
  },
  {
    field: "monthly_income",
    label: "Monthly Income",
    description: "Your approximate monthly income in INR.",
    type: "number",
    placeholder: "e.g. 100000",
  },
  {
    field: "monthly_expenses",
    label: "Monthly Expenses",
    description: "Your approximate monthly expenses in INR.",
    type: "number",
    placeholder: "e.g. 50000",
  },
  {
    field: "risk_tolerance",
    label: "Risk Tolerance",
    description: "Your preferred investment risk level.",
    type: "text",
    placeholder: "e.g. low, moderate, high",
  },
  {
    field: "investment_horizon_years",
    label: "Investment Horizon",
    description: "How many years you plan to remain invested.",
    type: "number",
    placeholder: "e.g. 10",
  },
  {
    field: "emergency_fund_months",
    label: "Emergency Fund",
    description: "Number of months of expenses covered by your emergency fund.",
    type: "number",
    placeholder: "e.g. 6",
  },
  {
    field: "favorite_stock",
    label: "Favorite Stock",
    description: "A stock you frequently track or invest in.",
    type: "text",
    placeholder: "e.g. RELIANCE",
  },
  {
    field: "favorite_sector",
    label: "Favorite Sector",
    description: "The market sector you are most interested in.",
    type: "text",
    placeholder: "e.g. Technology",
  },
  {
    field: "financial_goal",
    label: "Primary Financial Goal",
    description: "The main financial objective you are currently working toward.",
    type: "text",
    placeholder: "e.g. Build long-term wealth",
  },
];

export default function ProfilePage() {
  const {
    profile,
    completeness,
    isLoading,
    error,
    updateField,
    fetchProfile,
    clearError,
  } = useProfile();

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-6 lg:p-8">
      <section className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <UserRound className="h-4 w-4 text-[var(--accent)]" />

            <p className="text-xs font-medium uppercase tracking-wider text-[var(--accent)]">
              Persistent Context
            </p>
          </div>

          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--text-primary)]">
            Financial Profile
          </h1>

          <p className="mt-2 max-w-2xl text-xs leading-5 text-[var(--text-secondary)]">
            FinSight uses your profile to provide more personalized financial
            responses and recommendations.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => void fetchProfile()}
          disabled={isLoading}
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </section>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[var(--radius-md)] border border-[var(--danger)]/20 bg-[var(--danger-subtle)] px-4 py-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-[var(--danger)]" />

            <p className="text-xs text-[var(--danger)]">
              {error}
            </p>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={clearError}
          >
            Dismiss
          </Button>
        </div>
      )}

      <section className="grid gap-4 lg:grid-cols-[1fr_2fr]">
        <ProfileCompletenessCard
          completeness={completeness}
          isLoading={isLoading}
        />

        <Card className="overflow-hidden">
          <div className="border-b border-[var(--border)] px-5 py-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Profile Information
            </h2>

            <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
              Edit a field and save it individually.
            </p>
          </div>

          <div className="grid gap-5 p-5 md:grid-cols-2">
            {PROFILE_FIELDS.map((config) => (
              <ProfileFieldEditor
                key={config.field}
                config={config}
                profile={profile}
                updateField={updateField}
              />
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}

interface ProfileCompletenessCardProps {
  completeness: ReturnType<typeof useProfile>["completeness"];
  isLoading: boolean;
}

function ProfileCompletenessCard({
  completeness,
  isLoading,
}: ProfileCompletenessCardProps) {
  const percentage = completeness?.completeness_pct ?? 0;

  const tierVariant =
    completeness?.tier === "complete"
      ? "accent"
      : completeness?.tier === "intermediate"
        ? "good"
        : "default";

  return (
    <Card className="h-fit overflow-hidden">
      <div className="border-b border-[var(--border)] px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">
              Profile Completeness
            </h2>

            <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
              Financial context available to the agent
            </p>
          </div>

          {completeness && (
            <Badge variant={tierVariant}>
              {completeness.tier}
            </Badge>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-5 p-5">
        <div>
          <div className="mb-2 flex items-end justify-between">
            <span className="font-data text-2xl font-semibold text-[var(--text-primary)]">
              {isLoading ? "—" : `${Math.round(percentage)}%`}
            </span>

            {completeness && (
              <span className="font-data text-[10px] text-[var(--text-tertiary)]">
                {completeness.filled_count}/{completeness.total_count} fields
              </span>
            )}
          </div>

          <Progress
            value={percentage}
            variant={
              percentage >= 80
                ? "excellent"
                : percentage >= 50
                  ? "good"
                  : "partial"
            }
          />
        </div>

        {completeness?.is_complete && (
          <div className="flex items-start gap-2 rounded-[var(--radius-md)] bg-[var(--success-subtle)] p-3">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[var(--success)]" />

            <p className="text-xs leading-5 text-[var(--success)]">
              Your financial profile contains all required information.
            </p>
          </div>
        )}

        {completeness &&
          completeness.missing_required.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                Missing Required
              </p>

              <div className="mt-2 flex flex-wrap gap-2">
                {completeness.missing_required.map((item) => (
                  <Badge
                    key={item.field}
                    variant="partial"
                  >
                    {item.label}
                  </Badge>
                ))}
              </div>
            </div>
          )}

        {completeness &&
          completeness.missing_optional.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                Missing Optional
              </p>

              <div className="mt-2 flex flex-wrap gap-2">
                {completeness.missing_optional.map((item) => (
                  <Badge
                    key={item.field}
                    variant="default"
                  >
                    {item.label}
                  </Badge>
                ))}
              </div>
            </div>
          )}
      </div>
    </Card>
  );
}

interface ProfileFieldEditorProps {
  config: EditableProfileField;
  profile: UserProfile;
  updateField: ReturnType<typeof useProfile>["updateField"];
}

function ProfileFieldEditor({
  config,
  profile,
  updateField,
}: ProfileFieldEditorProps) {
  const profileValue = profile[config.field];

  const initialValue = Array.isArray(profileValue)
    ? profileValue.join(", ")
    : profileValue === null || profileValue === undefined
      ? ""
      : String(profileValue);

  const [value, setValue] = useState(initialValue);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);
  async function handleSave() {
    setIsSaving(true);
    setSaved(false);

    let parsedValue: string | number = value;

    if (config.type === "number") {
      const numericValue = Number(value);

      if (Number.isNaN(numericValue)) {
        setIsSaving(false);
        return;
      }

      parsedValue = numericValue;
    }

    try {
      await updateField(config.field, parsedValue);
      setSaved(true);

      window.setTimeout(() => {
        setSaved(false);
      }, 2000);
    } catch {
      // useProfile already exposes and displays the error.
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div>
        <label
          htmlFor={`profile-${config.field}`}
          className="text-xs font-medium text-[var(--text-primary)]"
        >
          {config.label}
        </label>

        <p className="mt-0.5 text-[10px] leading-4 text-[var(--text-tertiary)]">
          {config.description}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <Input
          id={`profile-${config.field}`}
          type={config.type}
          value={value}
          placeholder={config.placeholder}
          onChange={(event) => {
            setValue(event.target.value);
            setSaved(false);
          }}
          className={config.type === "number" ? "font-data" : undefined}
        />

        <Button
          variant={saved ? "secondary" : "default"}
          size="icon"
          onClick={() => void handleSave()}
          isLoading={isSaving}
          aria-label={`Save ${config.label}`}
          title={`Save ${config.label}`}
        >
          {saved ? (
            <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />
          ) : (
            <Save className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}