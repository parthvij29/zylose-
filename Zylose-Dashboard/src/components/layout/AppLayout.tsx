"use client";

import { useState, createContext, useContext } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const SidebarContext = createContext<{
  collapsed: boolean;
  toggle: () => void;
}>({ collapsed: false, toggle: () => {} });

export function useSidebar() {
  return useContext(SidebarContext);
}

const pageTitles: Record<string, string> = {
  "/": "Overview",
  "/activity": "Activity",
  "/analytics": "Analytics",
  "/devices": "Devices",
  "/settings": "Settings",
};

export function AppLayout({
  children,
  pathname,
}: {
  children: React.ReactNode;
  pathname: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const title = pageTitles[pathname] || "ZYLOSE";

  return (
    <SidebarContext.Provider
      value={{ collapsed, toggle: () => setCollapsed(!collapsed) }}
    >
      <div className="flex h-screen bg-[#0a0a0c] text-zinc-100 overflow-hidden">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />

        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <TopBar
            title={title}
            onMenuClick={() => setMobileOpen(true)}
          />

          <main className="flex-1 overflow-y-auto">
            <div className="p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto w-full">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SidebarContext.Provider>
  );
}
