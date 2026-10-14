"use client";

import type { AnalyticsData } from "@/lib/types";

export function DetectionChart({ analytics }: { analytics: AnalyticsData | null }) {

  const hourly = analytics?.hourlyActivity || [];
  const maxVal = Math.max(
    ...hourly.map((d) => d.zylose + d.unknown + d.silence),
    1
  );

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[14px] font-semibold text-white tracking-tight">
          Detection Activity
        </h3>
      </div>

      <div className="flex items-center gap-4 mb-4 text-[11px] text-zinc-500">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-sm bg-indigo-400" />
          ZYLOSE
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-sm bg-amber-400" />
          UNKNOWN
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-sm bg-zinc-500" />
          SILENCE
        </div>
      </div>

      {hourly.length === 0 ? (
        <div className="h-48 flex items-center justify-center">
          <div className="text-[13px] text-zinc-500">Loading chart data...</div>
        </div>
      ) : (
        <div className="relative">
          <div className="flex items-end gap-[3px] h-48 overflow-x-auto pb-6">
            {hourly.map((d, i) => {
              return (
                <div
                  key={i}
                  className="flex flex-col items-center gap-0 min-w-[8px] flex-1 group relative"
                  style={{ height: "100%" }}
                >
                  <div className="flex-1 w-full flex flex-col justify-end gap-px">
                    <div
                      className="w-full bg-indigo-400/80 rounded-t-sm transition-all hover:bg-indigo-400"
                      style={{
                        height: `${(d.zylose / maxVal) * 140}px`,
                      }}
                    />
                    <div
                      className="w-full bg-amber-400/80 transition-all hover:bg-amber-400"
                      style={{
                        height: `${(d.unknown / maxVal) * 140}px`,
                      }}
                    />
                    <div
                      className="w-full bg-zinc-500/80 rounded-b-sm transition-all hover:bg-zinc-500"
                      style={{
                        height: `${(d.silence / maxVal) * 140}px`,
                      }}
                    />
                  </div>

                  <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    <div className="bg-[#1a1a1e] border border-white/[0.1] rounded-lg px-2.5 py-1.5 text-[10px] text-zinc-300 whitespace-nowrap shadow-xl">
                      <div className="text-zinc-500 mb-0.5">{d.hour}</div>
                      <div>
                        <span className="text-indigo-400">{d.zylose}</span>{" "}
                        <span className="text-zinc-500">·</span>{" "}
                        <span className="text-amber-400">{d.unknown}</span>{" "}
                        <span className="text-zinc-500">·</span>{" "}
                        <span className="text-zinc-400">{d.silence}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
