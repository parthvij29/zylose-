"use client";

import { useEffect, useState } from "react";
import type { DetectionEvent } from "@/lib/types";
import { Mic, Zap, AlertCircle, Volume2 } from "lucide-react";

function ListeningIndicator() {
  return (
    <div className="flex items-center gap-1.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-1 rounded-full bg-indigo-400 animate-listening-bar"
          style={{
            height: "12px",
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

function TypeIcon({ type }: { type: string }) {
  switch (type) {
    case "zylose":
      return <Zap className="w-5 h-5" />;
    case "unknown":
      return <AlertCircle className="w-5 h-5" />;
    default:
      return <Volume2 className="w-5 h-5" />;
  }
}

interface LiveDetectionProps {
  latestEvent: DetectionEvent | null;
}

export function LiveDetection({ latestEvent }: LiveDetectionProps) {
  const [timeAgo, setTimeAgo] = useState("just now");

  useEffect(() => {
    if (!latestEvent) return;
    const update = () => {
      const diff = Date.now() - new Date(latestEvent.timestamp).getTime();
      const secs = Math.floor(diff / 1000);
      if (secs < 5) setTimeAgo("just now");
      else if (secs < 60) setTimeAgo(`${secs}s ago`);
      else setTimeAgo(`${Math.floor(secs / 60)}m ago`);
    };
    update();
    const interval = setInterval(update, 5000);
    return () => clearInterval(interval);
  }, [latestEvent]);

  const typeConfig = {
    zylose: {
      bg: "from-indigo-500/10 to-violet-500/10",
      border: "border-indigo-500/20",
      accent: "text-indigo-400",
      statusBg: "bg-indigo-500/10",
      statusText: "text-indigo-400",
      label: "ZYLOSE ACTIVATED",
      ring: "bg-indigo-500",
    },
    unknown: {
      bg: "from-amber-500/10 to-orange-500/10",
      border: "border-amber-500/20",
      accent: "text-amber-400",
      statusBg: "bg-amber-500/10",
      statusText: "text-amber-400",
      label: "UNKNOWN DETECTED",
      ring: "bg-amber-500",
    },
    silence: {
      bg: "from-zinc-500/10 to-zinc-600/10",
      border: "border-zinc-500/20",
      accent: "text-zinc-400",
      statusBg: "bg-zinc-500/10",
      statusText: "text-zinc-400",
      label: "SILENCE DETECTED",
      ring: "bg-zinc-500",
    },
  };

  const event = latestEvent;
  const config = event ? typeConfig[event.type] : typeConfig.silence;

  const signalBreakdown = event
    ? [
        { label: `${event.type} confidence`, value: event.confidence, color: "bg-indigo-400" },
        { label: "Silence", value: event.silenceScore, color: "bg-zinc-400" },
        { label: "Unknown", value: event.unknownScore, color: "bg-amber-400" },
      ]
    : [];

  return (
    <div className="relative">
      <div
        className={`relative overflow-hidden rounded-2xl border ${config.border} bg-gradient-to-br ${config.bg} p-6 md:p-8 transition-all duration-500`}
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div
                  className={`w-3 h-3 rounded-full ${config.ring} animate-pulse-ring`}
                />
                <div
                  className={`absolute inset-0 w-3 h-3 rounded-full ${config.ring} animate-pulse`}
                />
              </div>
              <span className="text-[11px] uppercase tracking-[0.15em] font-semibold text-zinc-400">
                Live Detection
              </span>
            </div>

            {event ? (
              <>
                <div className="flex items-center gap-3">
                  <TypeIcon type={event.type} />
                  <h2
                    className={`text-2xl md:text-3xl font-bold tracking-tight ${config.accent}`}
                  >
                    {event.type.toUpperCase()}
                  </h2>
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-5xl md:text-6xl font-bold tracking-tighter text-white">
                    {event.confidence}
                  </span>
                  <span className="text-xl text-zinc-400">%</span>
                </div>

                <p className="text-[13px] text-zinc-500 font-medium uppercase tracking-wider">
                  {config.label}
                </p>

                <div className="flex items-center gap-4 text-[13px] text-zinc-400">
                  <span>Detected {timeAgo}</span>
                  <span className="text-zinc-600">·</span>
                  <span>Device: {event.deviceId}</span>
                </div>
              </>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Mic className="w-5 h-5 text-zinc-500" />
                  <span className="text-2xl font-bold text-zinc-500">
                    WAITING
                  </span>
                </div>
                <p className="text-[13px] text-zinc-500">
                  No detections yet. Start the device to begin monitoring.
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col items-start md:items-end gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06]">
              <ListeningIndicator />
              <span className="text-[12px] font-medium text-zinc-400 uppercase tracking-wider">
                Listening
              </span>
            </div>

            {event && (
              <div className="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <span className="text-[12px] font-medium text-emerald-400">
                  Event Logged
                </span>
              </div>
            )}
          </div>
        </div>

        {event && (
          <div className="mt-6 rounded-xl border border-white/[0.06] bg-black/10 p-4 md:p-5">
            <div className="flex items-center justify-between gap-3 mb-3">
              <p className="text-[12px] uppercase tracking-[0.12em] text-zinc-500 font-medium">
                Model output scores
              </p>
              <span className="text-[11px] text-zinc-400">reported by device</span>
            </div>

            <div className="space-y-3">
              {signalBreakdown.map((signal) => (
                <div key={signal.label}>
                  <div className="flex items-center justify-between mb-1.5 text-[11px] text-zinc-400">
                    <span>{signal.label}</span>
                    <span>{signal.value}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${signal.color}`}
                      style={{ width: `${Math.min(100, signal.value)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <p className="mt-4 text-[12px] leading-5 text-zinc-500">
              Confidence scores describe the model output; they are not a measurement of validated accuracy.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
