"use client";

export function ZyloseLogo({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative flex-shrink-0 w-8 h-8 flex items-center justify-center">
        <svg viewBox="0 0 32 32" fill="none" className="w-8 h-8">
          <rect width="32" height="32" rx="8" fill="url(#zylose-gradient)" />
          <path
            d="M8 16 Q10 10 12 16 Q14 22 16 16 Q18 10 20 16 Q22 22 24 16"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />
          <circle cx="16" cy="16" r="2" fill="white" opacity="0.9" />
          <defs>
            <linearGradient id="zylose-gradient" x1="0" y1="0" x2="32" y2="32">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      {!collapsed && (
        <span className="text-[15px] font-semibold tracking-tight text-white">
          ZYLOSE
        </span>
      )}
    </div>
  );
}
