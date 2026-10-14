"use client";

import { Bell, Menu, User } from "lucide-react";

interface TopBarProps {
  title: string;
  onMenuClick: () => void;
}

export function TopBar({ title, onMenuClick }: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 h-16 flex items-center justify-between px-4 md:px-6 bg-[#0a0a0c]/80 backdrop-blur-xl border-b border-white/[0.06]">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden w-9 h-9 flex items-center justify-center rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          aria-label="Open navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-[15px] font-semibold text-white tracking-tight">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-2 mr-2 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06]">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[12px] font-medium text-zinc-300">
            Device Online
          </span>
        </div>

        <button
          className="relative w-9 h-9 flex items-center justify-center rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-indigo-400" />
        </button>

        <button
          className="w-8 h-8 rounded-full bg-white/[0.08] border border-white/[0.1] flex items-center justify-center hover:bg-white/[0.12] transition-colors"
          aria-label="User menu"
        >
          <User className="w-4 h-4 text-zinc-400" />
        </button>
      </div>
    </header>
  );
}
