"use client";

import type { AnalyticsData } from "@/lib/types";

const typeConfig = {
  zylose: { color: "#818cf8", label: "ZYLOSE" },
  unknown: { color: "#fbbf24", label: "UNKNOWN" },
  silence: { color: "#71717a", label: "SILENCE" },
};

function DonutChart({
  data,
}: {
  data: { type: string; percentage: number; count: number }[];
}) {
  const total = data.reduce((s, d) => s + d.count, 0);

  const segments = data.reduce<
    { type: string; percentage: number; count: number; start: number; end: number }[]
  >((acc, d) => {
    const start = acc.length > 0 ? acc[acc.length - 1].end : 0;
    return [...acc, { ...d, start, end: start + d.percentage }];
  }, []);

  const createArc = (start: number, end: number, radius: number): string => {
    if (end - start >= 100) {
      return `M ${100} ${100 - radius} A ${radius} ${radius} 0 1 1 ${99.99} ${100 - radius}`;
    }
    const startAngle = (start / 100) * 360 - 90;
    const endAngle = (end / 100) * 360 - 90;
    const largeArc = end - start > 50 ? 1 : 0;
    const x1 = 100 + radius * Math.cos((startAngle * Math.PI) / 180);
    const y1 = 100 + radius * Math.sin((startAngle * Math.PI) / 180);
    const x2 = 100 + radius * Math.cos((endAngle * Math.PI) / 180);
    const y2 = 100 + radius * Math.sin((endAngle * Math.PI) / 180);
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <svg viewBox="0 0 200 200" className="w-40 h-40 flex-shrink-0">
        {segments.map((seg) => (
          <path
            key={seg.type}
            d={createArc(seg.start, seg.end, 75)}
            fill="none"
            stroke={typeConfig[seg.type as keyof typeof typeConfig]?.color || "#666"}
            strokeWidth="24"
            strokeLinecap="round"
          />
        ))}
        <text x="100" y="96" textAnchor="middle" className="fill-white text-2xl font-bold">
          {total}
        </text>
        <text x="100" y="114" textAnchor="middle" className="fill-zinc-500 text-[10px] font-medium uppercase tracking-wider">
          Total
        </text>
      </svg>

      <div className="space-y-3">
        {data.map((d) => {
          const cfg = typeConfig[d.type as keyof typeof typeConfig];
          return (
            <div key={d.type} className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: cfg?.color }} />
              <div className="flex-1">
                <span className="text-[13px] text-zinc-300 font-medium">{cfg?.label}</span>
              </div>
              <span className="text-[13px] text-zinc-500 font-mono">{d.percentage}%</span>
              <span className="text-[12px] text-zinc-600">({d.count})</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function HourlyChart({
  data,
}: {
  data: { hour: string; zylose: number; unknown: number; silence: number }[];
}) {
  const maxVal = Math.max(...data.map((d) => d.zylose + d.unknown + d.silence), 1);

  return (
    <div className="flex items-end gap-[3px] h-32">
      {data.map((d, i) => {
        const total = d.zylose + d.unknown + d.silence;
        const height = (total / maxVal) * 100;
        const hourNum = parseInt(d.hour, 10);
        return (
          <div key={i} className="flex-1 flex flex-col justify-end h-full group relative">
            <div
              className="w-full rounded-t-sm transition-all hover:opacity-100 opacity-80"
              style={{
                height: `${height}%`,
                background: `linear-gradient(to top, #71717a ${total > 0 ? (d.silence / total) * 100 : 0}%, #fbbf24 ${total > 0 ? ((d.silence + d.unknown) / total) * 100 : 0}%, #818cf8 100%)`,
              }}
            />
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              <div className="bg-[#1a1a1e] border border-white/[0.1] rounded-lg px-2 py-1 text-[10px] text-zinc-300 whitespace-nowrap shadow-xl">
                {d.hour} — {total}
              </div>
            </div>
            {hourNum % 3 === 0 && (
              <span className="text-[9px] text-zinc-600 text-center mt-1">{d.hour}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface AnalyticsPageProps {
  analytics: AnalyticsData;
}

export function AnalyticsContent({ analytics }: AnalyticsPageProps) {
  const totalInferences = analytics.distribution.reduce(
    (total, item) => total + item.count,
    0
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
          <h3 className="text-[14px] font-semibold text-white tracking-tight mb-6">
            Detection Distribution
          </h3>
          <DonutChart data={analytics.distribution} />
        </div>

        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
          <h3 className="text-[14px] font-semibold text-white tracking-tight mb-6">
            Confidence Overview
          </h3>
          <div className="space-y-5">
            <ConfidenceMetric
              label="Average Zylose Confidence"
              value={`${(analytics.confidence.average * 100).toFixed(1)}%`}
              bar={analytics.confidence.average * 100}
              color="bg-indigo-400"
            />
            <ConfidenceMetric
              label="Highest Confidence"
              value={`${(analytics.confidence.highest * 100).toFixed(1)}%`}
              bar={analytics.confidence.highest * 100}
              color="bg-emerald-400"
            />
            <ConfidenceMetric
              label="Lowest Confidence"
              value={`${(analytics.confidence.lowest * 100).toFixed(1)}%`}
              bar={analytics.confidence.lowest * 100}
              color="bg-amber-400"
            />
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
        <div className="flex items-center justify-between gap-3 mb-6">
          <h3 className="text-[14px] font-semibold text-white tracking-tight">
            Observed Model Output
          </h3>
          <span className="text-[11px] uppercase tracking-[0.12em] text-zinc-500">
            calculated from stored events
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <PerformanceItem
            label="Total Inferences"
            value={totalInferences.toLocaleString()}
          />
          <PerformanceItem
            label="Zylose Events"
            value={analytics.distribution.find((item) => item.type === "zylose")?.count.toLocaleString() ?? "0"}
          />
          <PerformanceItem
            label="Unknown Events"
            value={analytics.distribution.find((item) => item.type === "unknown")?.count.toLocaleString() ?? "0"}
          />
          <PerformanceItem
            label="Silence Events"
            value={analytics.distribution.find((item) => item.type === "silence")?.count.toLocaleString() ?? "0"}
          />
        </div>
        <p className="mt-4 text-[12px] text-zinc-500">
          Precision and recall require ground-truth labels. They are not inferred from confidence scores.
        </p>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 md:p-6">
        <h3 className="text-[14px] font-semibold text-white tracking-tight mb-6">
          Hourly Activity
        </h3>
        <HourlyChart data={analytics.hourlyActivity} />
      </div>

    </div>
  );
}

function ConfidenceMetric({
  label,
  value,
  bar,
  color,
}: {
  label: string;
  value: string;
  bar: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[12px] text-zinc-500 font-medium">{label}</span>
        <span className="text-[14px] font-bold text-white font-mono">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.06]">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${bar}%` }} />
      </div>
    </div>
  );
}

function PerformanceItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
      <div>
        <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium mb-1">{label}</p>
        <p className="text-[15px] font-bold text-white">{value}</p>
      </div>
    </div>
  );
}
