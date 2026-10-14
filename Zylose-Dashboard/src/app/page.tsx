"use client";

import { Zap, AlertCircle, Volume2, Activity, AlertTriangle, RefreshCw } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { LiveDetection } from "@/components/dashboard/LiveDetection";
import { StatCard } from "@/components/dashboard/StatCard";
import { DetectionChart } from "@/components/dashboard/DetectionChart";
import { RecentDetections } from "@/components/dashboard/RecentDetections";
import { useApiData, usePolling } from "@/lib/hooks";
import { getDashboard } from "@/lib/api";
import { mapAnalytics, mapEvent, mapStats } from "@/lib/types";

export default function DashboardPage() {
  const dashboardResult = useApiData(
    () => getDashboard().then((data) => ({
      events: data.events.map(mapEvent),
      stats: mapStats(data.stats),
      analytics: mapAnalytics(data.analytics),
    })),
    []
  );

  usePolling(() => {
    dashboardResult.refetch();
  }, 5_000);

  const events = dashboardResult.data?.events || [];
  const latestEvent = events[0] || null;
  const stats = dashboardResult.data?.stats;
  const analytics = dashboardResult.data?.analytics || null;

  const isLoading = dashboardResult.loading;
  const hasError = dashboardResult.error;

  return (
    <AppLayout pathname="/">
      <div className="space-y-6">
        <div>
          <p className="text-[13px] text-zinc-500 mb-1">
            Edge AI that listens.
          </p>
        </div>

        {isLoading && <LoadingSkeleton />}

        {hasError && !isLoading && (
          <ErrorBanner
            message={dashboardResult.error || "Failed to load data"}
            onRetry={dashboardResult.refetch}
          />
        )}

        {!isLoading && (
          <>
            <LiveDetection latestEvent={latestEvent} />

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
              <StatCard
                icon={Zap}
                label="Zylose Detections"
                value={stats?.zyloseDetections ?? "—"}
                trend={stats ? `+${stats.todayZylose} today` : undefined}
                trendUp
              />
              <StatCard
                icon={AlertCircle}
                label="Unknown Detections"
                value={stats?.unknownDetections ?? "—"}
                trend={stats ? `+${stats.todayUnknown} today` : undefined}
                trendUp={false}
              />
              <StatCard
                icon={Volume2}
                label="Silence Detections"
                value={stats?.silenceDetections ?? "—"}
                trend={stats ? `+${stats.todaySilence} today` : undefined}
                trendUp
              />
              <StatCard
                icon={Activity}
                label="Total Inferences"
                value={stats?.totalInferences ?? "—"}
              />
            </div>

            <DetectionChart analytics={analytics} />

            <RecentDetections events={events} />
          </>
        )}
      </div>
    </AppLayout>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] h-64" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-32" />
        ))}
      </div>
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-64" />
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-80" />
    </div>
  );
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
        <div>
          <p className="text-[13px] text-red-400 font-medium">Unable to load data</p>
          <p className="text-[12px] text-zinc-500">{message}</p>
        </div>
      </div>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[12px] font-medium text-zinc-300 hover:bg-white/[0.06] transition-colors"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        Try again
      </button>
    </div>
  );
}
