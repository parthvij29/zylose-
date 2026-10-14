"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  Cpu,
  Settings,
  ChevronLeft,
  X,
} from "lucide-react";
import { ZyloseLogo } from "@/components/ui/ZyloseLogo";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/devices", label: "Devices", icon: Cpu },
];

const bottomItems = [
  { href: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 z-50 h-full bg-[#0c0c0e] border-r border-white/[0.06]
          transition-all duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${collapsed ? "w-[68px]" : "w-[240px]"}
          ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="flex flex-col h-full">
          <div
            className={`flex items-center h-16 px-4 border-b border-white/[0.06] ${
              collapsed ? "justify-center" : "justify-between"
            }`}
          >
            <ZyloseLogo collapsed={collapsed} />
            {collapsed ? (
              <button
                onClick={onToggle}
                className="hidden lg:flex w-7 h-7 items-center justify-center rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.06] transition-colors"
                aria-label="Expand sidebar"
              >
                <ChevronLeft className="w-4 h-4 rotate-180" />
              </button>
            ) : (
              <>
                <button
                  onClick={onToggle}
                  className="hidden lg:flex w-7 h-7 items-center justify-center rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.06] transition-colors"
                  aria-label="Collapse sidebar"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={onMobileClose}
                  className="lg:hidden w-7 h-7 flex items-center justify-center rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.06] transition-colors"
                  aria-label="Close menu"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            )}
          </div>

          <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onMobileClose}
                  className={`
                    flex items-center gap-3 px-3 h-9 rounded-lg text-[13px] font-medium transition-all
                    ${
                      isActive
                        ? "bg-white/[0.08] text-white"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
                    }
                    ${collapsed ? "justify-center px-0" : ""}
                  `}
                  aria-current={isActive ? "page" : undefined}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-white/[0.06] py-3 px-2 space-y-0.5">
            {bottomItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onMobileClose}
                  className={`
                    flex items-center gap-3 px-3 h-9 rounded-lg text-[13px] font-medium transition-all
                    ${
                      isActive
                        ? "bg-white/[0.08] text-white"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
                    }
                    ${collapsed ? "justify-center px-0" : ""}
                  `}
                  aria-current={isActive ? "page" : undefined}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </div>

          <div
            className={`border-t border-white/[0.06] p-3 ${collapsed ? "px-2" : ""}`}
          >
            <div
              className={`flex items-center gap-2.5 ${
                collapsed ? "justify-center" : ""
              }`}
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0 animate-pulse" />
              {!collapsed && (
                <div className="min-w-0">
                  <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">
                    Online
                  </p>
                  <p className="text-[12px] text-zinc-300 font-medium truncate">
                    ZYLOSE-ESP32-01
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
