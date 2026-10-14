import { NextResponse } from "next/server";
import { supabase, isSchemaMissingError } from "@/lib/supabase-server";
import type { ApiDetectionType } from "@/lib/types";

export async function GET() {
  try {
    if (!supabase) {
      return NextResponse.json(
        { error: "Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local." },
        { status: 503 }
      );
    }

    const [recentResult, aggregateResult] = await Promise.all([
      supabase
        .from("events")
        .select("id, device_id, timestamp, result, confidence, unknown_score, silence_score, status")
        .order("timestamp", { ascending: false })
        .limit(20),
      supabase
        .from("events")
        .select("timestamp, result, confidence"),
    ]);

    if (recentResult.error || aggregateResult.error) {
      const err = recentResult.error || aggregateResult.error;
      console.error("Supabase dashboard query error:", err);
      if (isSchemaMissingError(err)) {
        return NextResponse.json(
          { error: "Database tables ('devices' and 'events') not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      return NextResponse.json({ error: "Failed to fetch dashboard data" }, { status: 500 });
    }

    const events = aggregateResult.data || [];
    const recentEvents = recentResult.data || [];
    const todayIso = new Date().toISOString().slice(0, 10);
    const distribution = { zylose: 0, unknown: 0, silence: 0 };
    const hourlyMap: Record<string, { zylose: number; unknown: number; silence: number }> = {};
    const zyloseConfidences: number[] = [];
    let todayZylose = 0;
    let todayUnknown = 0;
    let todaySilence = 0;

    for (let hour = 0; hour < 24; hour++) {
      hourlyMap[`${String(hour).padStart(2, "0")}:00`] = {
        zylose: 0,
        unknown: 0,
        silence: 0,
      };
    }

    for (const event of events) {
      const result = event.result as ApiDetectionType;
      distribution[result]++;
      if (result === "zylose") zyloseConfidences.push(Number(event.confidence));

      if (event.timestamp.slice(0, 10) === todayIso) {
        if (result === "zylose") todayZylose++;
        if (result === "unknown") todayUnknown++;
        if (result === "silence") todaySilence++;
      }

      const hour = `${String(new Date(event.timestamp).getUTCHours()).padStart(2, "0")}:00`;
      hourlyMap[hour][result]++;
    }

    const total = events.length;
    const averageConfidence = zyloseConfidences.length
      ? zyloseConfidences.reduce((sum, value) => sum + value, 0) / zyloseConfidences.length
      : 0;

    return NextResponse.json({
      events: recentEvents,
      stats: {
        total_zylose: distribution.zylose,
        total_unknown: distribution.unknown,
        total_silence: distribution.silence,
        total_inferences: total,
        today_zylose: todayZylose,
        today_unknown: todayUnknown,
        today_silence: todaySilence,
        average_confidence: Math.round(averageConfidence * 1000) / 1000,
        last_detection: events[0]?.timestamp ?? null,
      },
      analytics: {
        distribution,
        average_zylose_confidence: Math.round(averageConfidence * 1000) / 1000,
        highest_zylose_confidence: zyloseConfidences.length ? Math.max(...zyloseConfidences) : 0,
        lowest_zylose_confidence: zyloseConfidences.length ? Math.min(...zyloseConfidences) : 0,
        hourly_activity: Object.entries(hourlyMap).map(([hour, counts]) => ({ hour, ...counts })),
        detection_rate: total ? Math.round((distribution.zylose / total) * 1000) / 1000 : 0,
      },
    });
  } catch (err) {
    console.error("GET /api/dashboard unexpected error:", err);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}