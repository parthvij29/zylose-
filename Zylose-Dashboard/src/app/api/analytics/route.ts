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
      .select("timestamp, result, confidence");

    if (eventsError) {
      console.error("Supabase analytics query error:", eventsError);
      if (isSchemaMissingError(eventsError)) {
        return NextResponse.json(
          { error: "Database tables not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      return NextResponse.json({ error: "Failed to fetch analytics" }, { status: 500 });
    }

    const distribution = { zylose: 0, unknown: 0, silence: 0 };
    const confidences: number[] = [];
    const hourlyMap: Record<string, { zylose: number; unknown: number; silence: number }> = {};
    for (let h = 0; h < 24; h++) {
      const key = String(h).padStart(2, "0") + ":00";
      hourlyMap[key] = { zylose: 0, unknown: 0, silence: 0 };
    }

    for (const event of events || []) {
      const result = event.result as keyof typeof distribution;
      distribution[result]++;
      if (result === "zylose") confidences.push(Number(event.confidence));

      const hour = String(new Date(event.timestamp).getUTCHours()).padStart(2, "0") + ":00";
      hourlyMap[hour][result]++;
    }

    const distZylose = distribution.zylose;
    const distUnknown = distribution.unknown;
    const distSilence = distribution.silence;
    const totalEvents = distZylose + distUnknown + distSilence;

    let avgConf = 0;
    let highConf = 0;
    let lowConf = 0;

    if (confidences.length > 0) {
      avgConf = confidences.reduce((a, b) => a + b, 0) / confidences.length;
      highConf = Math.max(...confidences);
      lowConf = Math.min(...confidences);
    }

    // Detection rate = zylose / total
    const detectionRate = totalEvents > 0 ? distZylose / totalEvents : 0;

    const hourly_activity = Object.entries(hourlyMap).map(([hour, counts]) => ({
      hour,
      ...counts,
    }));

    return NextResponse.json({
      distribution: {
        zylose: distZylose,
        unknown: distUnknown,
        silence: distSilence,
      },
      average_zylose_confidence: Math.round(avgConf * 1000) / 1000,
      highest_zylose_confidence: Math.round(highConf * 1000) / 1000,
      lowest_zylose_confidence: Math.round(lowConf * 1000) / 1000,
      hourly_activity,
      detection_rate: Math.round(detectionRate * 1000) / 1000,
    });
  } catch (err) {
    console.error("GET /api/analytics unexpected error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
