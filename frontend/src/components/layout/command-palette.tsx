"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Bot,
  LayoutDashboard,
  Network,
  Search,
  UserRound,
} from "lucide-react";

import { Dialog, DialogBody } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const commands = [
  {
    label: "Open Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Open AI Advisor",
    href: "/chat",
    icon: Bot,
  },
  {
    label: "Open Profile",
    href: "/profile",
    icon: UserRound,
  },
  {
    label: "Open Evaluation",
    href: "/evaluation",
    icon: Activity,
  },
  {
    label: "Open Architecture",
    href: "/architecture",
    icon: Network,
  },
];

export interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({
  open,
  onClose,
}: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  const filteredCommands = commands.filter((command) =>
    command.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleNavigate = (href: string) => {
    router.push(href);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidthClass="max-w-lg">
      <DialogBody className="p-2">
        <div className="flex items-center gap-2 border-b border-[var(--border)] px-2 pb-2">
          <Search className="h-4 w-4 shrink-0 text-[var(--text-tertiary)]" />

          <Input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search FinSight..."
            className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>

        <div className="mt-2 flex max-h-72 flex-col gap-1 overflow-y-auto">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((command) => {
              const Icon = command.icon;

              return (
                <button
                  key={command.href}
                  type="button"
                  onClick={() => handleNavigate(command.href)}
                  className={cn(
                    "flex w-full items-center gap-3",
                    "rounded-[var(--radius-md)] px-3 py-2.5",
                    "text-left text-sm text-[var(--text-secondary)]",
                    "transition-colors duration-150",
                    "hover:bg-[var(--surface-hover)]",
                    "hover:text-[var(--text-primary)]"
                  )}
                >
                  <Icon className="h-4 w-4 text-[var(--text-tertiary)]" />

                  <span>{command.label}</span>
                </button>
              );
            })
          ) : (
            <div className="px-3 py-8 text-center text-sm text-[var(--text-tertiary)]">
              No commands found.
            </div>
          )}
        </div>
      </DialogBody>
    </Dialog>
  );
}