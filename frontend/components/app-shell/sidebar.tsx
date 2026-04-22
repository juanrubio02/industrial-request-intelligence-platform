"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Blocks, CirclePlus, FileStack, LayoutDashboard, Users2, WandSparkles } from "lucide-react";

import { APP_NAME } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { useI18n } from "@/i18n/hooks";

export function Sidebar() {
  const pathname = usePathname();
  const currentPath = pathname ?? "";
  const { canManageMembers } = useAuth();
  const { messages } = useI18n();
  const navigation = [
    { href: "/dashboard", label: messages.shell.sidebar.navigation.dashboard, icon: LayoutDashboard },
    { href: "/requests", label: messages.shell.sidebar.navigation.requests, icon: FileStack },
    { href: "/requests/new", label: messages.shell.sidebar.navigation.newRequest, icon: CirclePlus },
    { href: "/demo-intake", label: messages.shell.sidebar.navigation.demoIntake, icon: WandSparkles },
    ...(canManageMembers
      ? [
          {
            href: "/settings/users",
            label: messages.shell.sidebar.navigation.settingsUsers,
            icon: Users2,
          },
        ]
      : []),
  ];

  return (
    <aside className="hidden bg-sidebar px-5 py-6 text-sidebarForeground lg:flex lg:flex-col">
      <div className="mb-10 flex items-center gap-3 px-1">
        <div className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-control)] bg-white/8 shadow-soft">
          <Blocks className="h-5 w-5" />
        </div>
        <div>
          <p className="text-[0.68rem] uppercase tracking-[0.18em] text-sidebarForeground/52">
            {messages.shell.sidebar.eyebrow}
          </p>
          <p className="text-base font-semibold tracking-[-0.02em]">{APP_NAME}</p>
        </div>
      </div>

      <nav className="space-y-1.5">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active =
            currentPath === item.href || currentPath.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "focus-ring flex items-center gap-3 rounded-[var(--radius-control)] px-3.5 py-3 text-sm font-medium transition",
                active
                  ? "bg-white text-slate-950 shadow-soft"
                  : "text-sidebarForeground/72 hover:bg-white/7 hover:text-sidebarForeground",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-[var(--radius-panel)] border border-white/10 bg-white/6 p-4">
        <p className="text-xs uppercase tracking-[0.18em] text-sidebarForeground/55">
          {messages.shell.sidebar.intelligence.eyebrow}
        </p>
        <p className="mt-2 text-sm leading-6 text-sidebarForeground/82">
          {messages.shell.sidebar.intelligence.description}
        </p>
      </div>
    </aside>
  );
}
