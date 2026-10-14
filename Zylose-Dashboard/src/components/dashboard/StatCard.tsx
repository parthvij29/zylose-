import { type LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  trend?: string;
  trendUp?: boolean;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  trendUp,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 md:p-5 hover:bg-white/[0.04] transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-white/[0.04] flex items-center justify-center">
          <Icon className="w-[18px] h-[18px] text-zinc-400" />
        </div>
        {trend && (
          <span
            className={`text-[12px] font-medium ${
              trendUp ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {trend} today
          </span>
        )}
      </div>
      <p className="text-[11px] uppercase tracking-[0.1em] font-medium text-zinc-500 mb-1">
        {label}
      </p>
      <p className="text-2xl md:text-3xl font-bold tracking-tight text-white">
        {value}
      </p>
    </div>
  );
}
