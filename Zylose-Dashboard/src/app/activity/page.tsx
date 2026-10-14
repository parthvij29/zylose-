"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { EventFilters } from "@/components/activity/EventFilters";
import { EventTable } from "@/components/activity/EventTable";
import { EventDetail } from "@/components/activity/EventDetail";
import { getEvents } from "@/lib/api";
import type { DetectionEvent, DetectionType } from "@/lib/types";
import { mapEventsResponse } from "@/lib/types";
import type { EventQueryParams } from "@/lib/api";

function useEvents(
  page: number,
  perPage: number,
  filters: {
    classification: DetectionType | "all";
    device: string;
    search: string;
    minConfidence: number;
    maxConfidence: number;
  }
) {
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: EventQueryParams = {
        page,
        limit: perPage,
      };
      if (filters.classification !== "all") params.result = filters.classification;
      if (filters.device !== "all") params.device_id = filters.device;

      const raw = await getEvents(params);
      const mapped = mapEventsResponse(raw);

      let filtered = mapped.events;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        filtered = filtered.filter(
          (e) =>
            e.id.toLowerCase().includes(q) ||
            e.type.toLowerCase().includes(q) ||
            e.deviceId.toLowerCase().includes(q) ||
            e.status.toLowerCase().includes(q)
        );
      }
      if (filters.minConfidence > 0) {
        filtered = filtered.filter((e) => e.confidence >= filters.minConfidence);
      }
      if (filters.maxConfidence < 100) {
        filtered = filtered.filter((e) => e.confidence <= filters.maxConfidence);
      }

      setEvents(filtered);
      setTotalPages(mapped.pagination.totalPages);
      setTotal(mapped.pagination.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load events");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, filters.classification, filters.device, filters.search, filters.minConfidence, filters.maxConfidence]);

  useEffect(() => {
    const id = setTimeout(() => { fetchEvents(); }, 0);
    return () => clearTimeout(id);
  }, [fetchEvents]);

  return { events, loading, error, totalPages, total, refetch: fetchEvents };
}

export default function ActivityPage() {
  const [selectedEvent, setSelectedEvent] = useState<DetectionEvent | null>(null);
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState<"timestamp" | "type" | "confidence">("timestamp");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [filters, setFilters] = useState({
    search: "",
    classification: "all" as DetectionType | "all",
    device: "all",
    minConfidence: 0,
    maxConfidence: 100,
  });
  const perPage = 10;

  const { events, loading, error, totalPages, total, refetch } = useEvents(page, perPage, filters);

  const sortedEvents = useMemo(() => {
    const sorted = [...events];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (sortField === "timestamp")
        cmp = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      else if (sortField === "type") cmp = a.type.localeCompare(b.type);
      else cmp = a.confidence - b.confidence;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [events, sortField, sortDir]);

  const handleSort = (field: "timestamp" | "type" | "confidence") => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <AppLayout pathname="/activity">
      <div className="space-y-6">
        <div>
          <p className="text-[13px] text-zinc-500">
            Explore and inspect detection events.
          </p>
        </div>

        <EventFilters onFilterChange={handleFilterChange} />

        {loading && (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-16 text-center">
            <div className="text-[13px] text-zinc-500 animate-pulse">Loading events...</div>
          </div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div>
                <p className="text-[13px] text-red-400 font-medium">Unable to load events</p>
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

        {!loading && !error && (
          <>
            <EventTable
              events={sortedEvents}
              onRowClick={setSelectedEvent}
              sortField={sortField}
              sortDir={sortDir}
              onSort={handleSort}
            />

            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-[12px] text-zinc-500">
                  Page {page} of {totalPages} ({total} events)
                </p>
                <div className="flex gap-1">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeftIcon />
                  </button>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRightIcon />
                  </button>
                </div>
              </div>
            )}

            {events.length === 0 && !loading && (
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-16 text-center">
                <p className="text-[13px] text-zinc-500">No detection events yet.</p>
              </div>
            )}
          </>
        )}

        <EventDetail
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      </div>
    </AppLayout>
  );
}

function ChevronLeftIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}
