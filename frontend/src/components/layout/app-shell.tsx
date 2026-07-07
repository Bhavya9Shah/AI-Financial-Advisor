"use client";

import { useEffect, useState } from "react";
import { Command, RefreshCw } from "lucide-react";

import { SidebarNav } from "@/components/layout/sidebar-nav";
import { CommandPalette } from "@/components/layout/command-palette";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useHealth } from "@/hooks/use-health";
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const {
    connectionState,
    isInitialChecking,
    recheck,
  } = useHealth();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen((current) => !current);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

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

  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <SidebarNav />

      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className={cn(
            "flex h-16 shrink-0 items-center justify-between",
            "border-b border-[var(--border)]",
            "bg-[var(--background)] px-6"
          )}
        >
          <div>
            <p className="text-xs text-[var(--text-tertiary)]">
              AI Financial Intelligence Platform
            </p>
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
              aria-label="Recheck API health"
              title="Recheck API health"
            >
              <RefreshCw
                className={cn(
                  "h-3.5 w-3.5",
                  isInitialChecking && "animate-spin"
                )}
              />
            </Button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCommandPaletteOpen(true)}
            >
              <Command className="h-3.5 w-3.5" />

              <span>Command</span>

              <kbd className="ml-1 rounded border border-[var(--border)] px-1.5 py-0.5 font-data text-[9px] text-[var(--text-tertiary)]">
                Ctrl K
              </kbd>
            </Button>
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-auto">
          {children}
        </main>
      </div>

      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />
    </div>
  );
}