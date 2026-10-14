"use client";

import type { DetectionEvent } from "@/lib/types";
import { Zap, AlertCircle, Volume2 } from "lucide-react";

const typeConfig = {
  zylose: {
    icon: Zap,
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    statusColor: "text-emerald-400",
  },
  unknown: {
    icon: AlertCircle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    statusColor: "text-amber-400",
  },
  silence: {
    icon: Volume2,
    color: "text-zinc-400",
    bg: "bg-zinc-500/10",
    statusColor: "text-zinc-400",
  },
};

interface RecentDetectionsProps {
  events: DetectionEvent[];
}

export function RecentDetections({ events }: RecentDetectionsProps) {
  const formatTime = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-[14px] font-semibold text-white tracking-tight">
          Recent Detections
        </h3>
        <a
          href="/activity"
          className="text-[12px] font-medium text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          View all
        </a>
      </div>

      <div className="space-y-1">
        {events.slice(0, 8).map((event) => {
          const config = typeConfig[event.type];
          const Icon = config.icon;
          return (
            <div
              key={event.id}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/[0.03] transition-colors group"
            >
              <div
                className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center flex-shrink-0`}
              >
                <Icon className={`w-4 h-4 ${config.color}`} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[13px] font-semibold ${config.color}`}
                  >
                    {event.type.toUpperCase()}
                  </span>
                  <span className="text-[12px] text-zinc-500">
                    {event.confidence}%
                  </span>
                </div>
                <p className="text-[11px] text-zinc-500 truncate">
                  {event.deviceId}
                </p>
              </div>

              <div className="text-right flex-shrink-0">
                <p className="text-[12px] text-zinc-400 font-mono">
                  {formatTime(event.timestamp)}
                </p>
                <p className={`text-[11px] capitalize ${config.statusColor}`}>
                  {event.status}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
