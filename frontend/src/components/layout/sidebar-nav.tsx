"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  Bot,
  BrainCircuit,
  LayoutDashboard,
  Network,
  UserRound,
} from "lucide-react";

import { cn } from "@/lib/utils";

const navigationItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "AI Advisor",
    href: "/chat",
    icon: Bot,
  },
  {
    label: "Profile",
    href: "/profile",
    icon: UserRound,
  },
  {
    label: "Evaluation",
    href: "/evaluation",
    icon: Activity,
  },
  {
    label: "Architecture",
    href: "/architecture",
    icon: Network,
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex h-screen w-60 shrink-0 flex-col",
        "border-r border-[var(--border)]",
        "bg-[var(--surface)]"
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-[var(--border)] px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-subtle)]">
          <BrainCircuit className="h-4 w-4 text-[var(--accent)]" />
        </div>

        <div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">
            FinSight
          </p>

          <p className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">
            AI Financial Advisor
          </p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex h-9 items-center gap-3 rounded-[var(--radius-md)] px-3",
                "text-sm transition-colors duration-150",
                isActive
                  ? "bg-[var(--accent-subtle)] text-[var(--accent)]"
                  : [
                      "text-[var(--text-secondary)]",
                      "hover:bg-[var(--surface-hover)]",
                      "hover:text-[var(--text-primary)]",
                    ]
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />

              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] p-4">
        <p className="font-data text-[10px] text-[var(--text-tertiary)]">
          FinSight v1.0
        </p>

        <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
          LangChain · Gemini · FastAPI
        </p>
      </div>
    </aside>
  );
}