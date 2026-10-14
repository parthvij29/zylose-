import { NextResponse } from "next/server";
import { supabase, isSchemaMissingError } from "@/lib/supabase-server";

export async function GET() {
  try {
    if (!supabase) {
      return NextResponse.json(
        { error: "Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local." },
        { status: 503 }
      );
    }

    const { data: events, error: eventsError } = await supabase
      .from("events")
      .select("result, confidence, timestamp");

    if (eventsError) {
      console.error("Supabase stats query error:", eventsError);
      if (isSchemaMissingError(eventsError)) {
        return NextResponse.json(
          { error: "Database tables not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      return NextResponse.json({ error: "Failed to fetch stats" }, { status: 500 });
    }

    const todayStart = new Date();
    todayStart.setUTCHours(0, 0, 0, 0);
    const todayIso = todayStart.toISOString();
    const totals = { zylose: 0, unknown: 0, silence: 0 };
    let todayZylose = 0;
    let todayUnknown = 0;
    let todaySilence = 0;
    let confidenceSum = 0;
    let confidenceCount = 0;
    let lastDetection: string | null = null;

    for (const event of events || []) {
      totals[event.result as keyof typeof totals]++;
      if (event.timestamp >= todayIso) {
        if (event.result === "zylose") todayZylose++;
        if (event.result === "unknown") todayUnknown++;
        if (event.result === "silence") todaySilence++;
      }
      if (event.result === "zylose") {
        confidenceSum += Number(event.confidence);
        confidenceCount++;
      }
      if (!lastDetection || event.timestamp > lastDetection) {
        lastDetection = event.timestamp;
      }
    }

    return NextResponse.json({
      total_zylose: totals.zylose,
      total_unknown: totals.unknown,
      total_silence: totals.silence,
      total_inferences: (events || []).length,
      today_zylose: todayZylose,
      today_unknown: todayUnknown,
      today_silence: todaySilence,
      average_confidence: confidenceCount
        ? Math.round((confidenceSum / confidenceCount) * 1000) / 1000
        : 0,
      last_detection: lastDetection,
    });
  } catch (err) {
    console.error("GET /api/stats unexpected error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
