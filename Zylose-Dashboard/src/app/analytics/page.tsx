"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { AnalyticsContent } from "@/components/analytics/AnalyticsContent";
import { useApiData } from "@/lib/hooks";
import { getAnalytics } from "@/lib/api";
import { mapAnalytics } from "@/lib/types";

export default function AnalyticsPage() {
  const { data: analytics, loading, error, refetch } = useApiData(
    () => getAnalytics().then(mapAnalytics),
    []
  );

  return (
    <AppLayout pathname="/analytics">
      <div className="space-y-6">
        <div>
          <p className="text-[13px] text-zinc-500">
            Deeper insights into detection patterns and performance.
          </p>
        </div>

        {loading && (
          <div className="space-y-6 animate-pulse">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-72" />
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-72" />
            </div>
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-48" />
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] h-48" />
          </div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div>
                <p className="text-[13px] text-red-400 font-medium">Unable to load analytics</p>
                <p className="text-[12px] text-zinc-500">{error}</p>
              </div>
            </div>
            <button
              onClick={refetch}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06] text-[12px] font-medium text-zinc-300 hover:bg-white/[0.06] transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try again
            </button>
          </div>
        )}

        {!loading && !error && analytics && (
          <AnalyticsContent analytics={analytics} />
        )}

        {!loading && !error && !analytics && (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-16 text-center">
            <p className="text-[13px] text-zinc-500">No analytics data available.</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
