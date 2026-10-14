"use client";

import type { DetectionEvent } from "@/lib/types";
import { X, Zap, AlertCircle, Volume2 } from "lucide-react";

const typeConfig = {
  zylose: {
    icon: Zap,
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    label: "ZYLOSE CONFIRMED",
  },
  unknown: {
    icon: AlertCircle,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    label: "UNKNOWN REJECTED",
  },
  silence: {
    icon: Volume2,
    color: "text-zinc-400",
    bg: "bg-zinc-500/10",
    label: "SILENCE DETECTED",
  },
};

interface EventDetailProps {
  event: DetectionEvent | null;
  onClose: () => void;
}

export function EventDetail({ event, onClose }: EventDetailProps) {
  if (!event) return null;

  const config = typeConfig[event.type];
  const Icon = config.icon;

  const ts = new Date(event.timestamp);

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#111113] border-l border-white/[0.06] overflow-y-auto animate-in slide-in-from-right">
        <div className="p-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-[15px] font-semibold text-white tracking-tight">
              Detection Event
            </h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
              aria-label="Close detail panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-6">
            <div
              className={`flex items-center gap-3 p-4 rounded-xl ${config.bg} border border-white/[0.06]`}
            >
              <div className="w-10 h-10 rounded-lg bg-white/[0.06] flex items-center justify-center">
                <Icon className={`w-5 h-5 ${config.color}`} />
              </div>
              <div>
                <p
                  className={`text-lg font-bold ${config.color}`}
                >
                  {event.type.toUpperCase()}
                </p>
                <p className="text-[12px] text-zinc-500 uppercase tracking-wider">
                  {config.label}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <DetailRow label="Confidence" value={`${event.confidence}%`} />
              <DetailRow
                label="Silence Score"
                value={`${event.silenceScore}%`}
              />
              <DetailRow
                label="Unknown Score"
                value={`${event.unknownScore}%`}
              />
              <div className="h-px bg-white/[0.06]" />
              <DetailRow
                label="Timestamp"
                value={ts.toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
                sub={ts.toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                  hour12: false,
                })}
              />
              <DetailRow label="Device" value={event.deviceId} />
              <DetailRow
                label="Event ID"
                value={event.id}
                mono
              />
              <DetailRow label="Status" value={event.status} capitalize />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function DetailRow({
  label,
  value,
  sub,
  mono,
  capitalize,
}: {
  label: string;
  value: string;
  sub?: string;
  mono?: boolean;
  capitalize?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-[12px] text-zinc-500 font-medium uppercase tracking-wider">
        {label}
      </span>
      <div className="text-right">
        <span
          className={`text-[13px] text-zinc-200 ${
            mono ? "font-mono" : ""
          } ${capitalize ? "capitalize" : ""}`}
        >
          {value}
        </span>
        {sub && (
          <p className="text-[12px] text-zinc-500 font-mono mt-0.5">
            {sub}
          </p>
        )}
      </div>
    </div>
  );
}
