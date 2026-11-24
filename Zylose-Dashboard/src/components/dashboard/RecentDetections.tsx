"use client";

import type { DetectionEvent, ConversationItem } from "@/lib/types";
import { MessageSquare, Cpu, CheckCircle2, ArrowRight } from "lucide-react";

interface RecentDetectionsProps {
  events: DetectionEvent[];
  conversations?: ConversationItem[];
}

export function RecentDetections({ events, conversations = [] }: RecentDetectionsProps) {
  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      });
    } catch {
      return "now";
    }
  };

  const hasConversations = conversations.length > 0;

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <h3 className="text-[14px] font-semibold text-white tracking-tight">
            Conversational Inference Log & Telemetry
          </h3>
        </div>
        <span className="text-[11px] font-mono text-zinc-400">
          Edge Hardware Synchronized
        </span>
      </div>

      <div className="space-y-2">
        {hasConversations ? (
          conversations.slice(0, 6).map((item) => (
            <div
              key={item.id}
              className="p-3 rounded-lg border border-white/[0.04] bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {item.intent}
                  </span>
                  <span className="text-[11px] font-mono text-zinc-400">
                    {item.confidence}% conf
                  </span>
                  <span className="text-[10px] text-purple-300 font-mono bg-purple-500/10 px-1.5 py-0.5 rounded">
                    {item.urgency}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-zinc-400">
                  {formatTime(item.timestamp)}
                </span>
              </div>

              <div className="space-y-1 mt-2">
                <div className="flex items-start gap-1.5 text-[13px] text-white font-medium">
                  <span className="text-indigo-400 font-mono font-bold">&gt;</span>
                  <span>{item.query}</span>
                </div>
                <div className="flex items-start gap-1.5 text-[12px] text-zinc-300 pl-4">
                  <ArrowRight className="w-3 h-3 text-emerald-400 mt-1 flex-shrink-0" />
                  <span>{item.response}</span>
                </div>
              </div>
            </div>
          ))
        ) : (
          events.slice(0, 5).map((event) => (
            <div
              key={event.id}
              className="flex items-center justify-between p-3 rounded-lg border border-white/[0.04] bg-white/[0.02]"
            >
              <div className="flex items-center gap-3">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <div>
                  <p className="text-[13px] font-semibold text-white uppercase">
                    {event.type}
                  </p>
                  <p className="text-[11px] text-zinc-400">{event.deviceId}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[12px] font-mono text-indigo-400">{event.confidence}%</p>
                <p className="text-[11px] font-mono text-zinc-400">{formatTime(event.timestamp)}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
