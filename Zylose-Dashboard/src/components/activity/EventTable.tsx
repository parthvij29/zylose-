"use client";

import type { DetectionEvent } from "@/lib/types";
import { Zap, AlertCircle, Volume2, ChevronUp, ChevronDown } from "lucide-react";

const typeConfig = {
  zylose: {
    icon: Zap,
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
  },
  unknown: {
    icon: AlertCircle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  silence: {
    icon: Volume2,
    color: "text-zinc-400",
    bg: "bg-zinc-500/10",
  },
};

type SortField = "timestamp" | "type" | "confidence";
type SortDir = "asc" | "desc";

interface EventTableProps {
  events: DetectionEvent[];
  onRowClick: (event: DetectionEvent) => void;
  sortField: SortField;
  sortDir: SortDir;
  onSort: (field: SortField) => void;
}

function formatTimestamp(ts: string) {
  const d = new Date(ts);
  return {
    date: d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }),
    time: d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }),
  };
}

function SortIcon({
  field,
  current,
  dir,
}: {
  field: SortField;
  current: SortField;
  dir: SortDir;
}) {
  if (field !== current)
    return <ChevronUp className="w-3 h-3 text-zinc-600" />;
  return dir === "asc" ? (
    <ChevronUp className="w-3 h-3 text-indigo-400" />
  ) : (
    <ChevronDown className="w-3 h-3 text-indigo-400" />
  );
}

export function EventTable({
  events,
  onRowClick,
  sortField,
  sortDir,
  onSort,
}: EventTableProps) {
  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/[0.06] bg-white/[0.02]">
              <th
                className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 cursor-pointer hover:text-zinc-300 transition-colors"
                onClick={() => onSort("timestamp")}
              >
                <div className="flex items-center gap-1">
                  Timestamp
                  <SortIcon
                    field="timestamp"
                    current={sortField}
                    dir={sortDir}
                  />
                </div>
              </th>
              <th
                className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 cursor-pointer hover:text-zinc-300 transition-colors"
                onClick={() => onSort("type")}
              >
                <div className="flex items-center gap-1">
                  Classification
                  <SortIcon
                    field="type"
                    current={sortField}
                    dir={sortDir}
                  />
                </div>
              </th>
              <th
                className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 cursor-pointer hover:text-zinc-300 transition-colors"
                onClick={() => onSort("confidence")}
              >
                <div className="flex items-center gap-1">
                  Confidence
                  <SortIcon
                    field="confidence"
                    current={sortField}
                    dir={sortDir}
                  />
                </div>
              </th>
              <th className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 hidden md:table-cell">
                Silence Score
              </th>
              <th className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 hidden md:table-cell">
                Unknown Score
              </th>
              <th className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 hidden lg:table-cell">
                Device
              </th>
              <th className="text-left px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => {
              const config = typeConfig[event.type];
              const Icon = config.icon;
              const ts = formatTimestamp(event.timestamp);
              return (
                <tr
                  key={event.id}
                  onClick={() => onRowClick(event)}
                  className="border-b border-white/[0.04] hover:bg-white/[0.03] cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-[13px] text-zinc-300 font-mono">
                      {ts.time}
                    </div>
                    <div className="text-[11px] text-zinc-600">{ts.date}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-7 h-7 rounded-md ${config.bg} flex items-center justify-center`}
                      >
                        <Icon className={`w-3.5 h-3.5 ${config.color}`} />
                      </div>
                      <span
                        className={`text-[13px] font-semibold ${config.color}`}
                      >
                        {event.type.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[13px] font-mono text-white">
                      {event.confidence}%
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className="text-[13px] font-mono text-zinc-400">
                      {event.silenceScore}%
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className="text-[13px] font-mono text-zinc-400">
                      {event.unknownScore}%
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <span className="text-[12px] text-zinc-400">
                      {event.deviceId}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium capitalize ${
                        event.status === "confirmed"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : event.status === "rejected"
                          ? "bg-amber-500/10 text-amber-400"
                          : "bg-zinc-500/10 text-zinc-400"
                      }`}
                    >
                      {event.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {events.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-[13px] text-zinc-500">
            No events match your filters.
          </p>
        </div>
      )}
    </div>
  );
}
