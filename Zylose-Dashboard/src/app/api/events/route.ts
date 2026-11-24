import { NextRequest, NextResponse } from "next/server";
import { supabase, isSchemaMissingError } from "@/lib/supabase-server";
import type { ApiEvent, ApiDetectionType, ApiDetectionStatus } from "@/lib/types";
import { updateTelemetry, getTelemetry } from "@/lib/telemetry-store";

// ── GET /api/events ──────────────────────────────────────────────────────

export async function GET(request: NextRequest) {
  try {
    if (!supabase) {
      return NextResponse.json(
        { error: "Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local." },
        { status: 503 }
      );
    }

    const { searchParams } = new URL(request.url);
    const page = Math.max(1, parseInt(searchParams.get("page") || "1", 10));
    const limit = Math.min(100, Math.max(1, parseInt(searchParams.get("limit") || "20", 10)));
    const result = searchParams.get("result") || undefined;
    const deviceId = searchParams.get("device_id") || undefined;
    const from = searchParams.get("from") || undefined;
    const to = searchParams.get("to") || undefined;
    const includeTotal = searchParams.get("include_total") !== "false";

    let query = supabase
      .from("events")
      .select(
        "id, device_id, timestamp, result, confidence, unknown_score, silence_score, status, query, response, intent, urgency",
        includeTotal ? { count: "exact" } : undefined
      );

    if (result) {
      query = query.eq("result", result);
    }
    if (deviceId) {
      query = query.eq("device_id", deviceId);
    }
    if (from) {
      query = query.gte("timestamp", from);
    }
    if (to) {
      query = query.lte("timestamp", to + "T23:59:59Z");
    }

    const offset = (page - 1) * limit;
    query = query
      .order("timestamp", { ascending: false })
      .range(offset, offset + limit - 1);

    let { data, error, count } = await query;

    // Fallback if query/response columns haven't been added yet
    if (error && error.message?.includes("column")) {
      let fallbackQuery = supabase
        .from("events")
        .select(
          "id, device_id, timestamp, result, confidence, unknown_score, silence_score, status",
          includeTotal ? { count: "exact" } : undefined
        );
      if (result) fallbackQuery = fallbackQuery.eq("result", result);
      if (deviceId) fallbackQuery = fallbackQuery.eq("device_id", deviceId);
      if (from) fallbackQuery = fallbackQuery.gte("timestamp", from);
      if (to) fallbackQuery = fallbackQuery.lte("timestamp", to + "T23:59:59Z");
      fallbackQuery = fallbackQuery.order("timestamp", { ascending: false }).range(offset, offset + limit - 1);
      const fallbackRes = await fallbackQuery;
      data = fallbackRes.data;
      error = fallbackRes.error;
      count = fallbackRes.count;
    }

    if (error) {
      console.error("Supabase GET /api/events error:", error);
      if (isSchemaMissingError(error)) {
        return NextResponse.json(
          { error: "Database table 'events' not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      return NextResponse.json(
        { error: "Failed to fetch events" },
        { status: 500 }
      );
    }

    const total = includeTotal ? count ?? 0 : data?.length ?? 0;
    const totalPages = Math.ceil(total / limit);

    return NextResponse.json({
      events: (data || []) as ApiEvent[],
      pagination: {
        page,
        limit,
        total,
        total_pages: totalPages,
      },
    });
  } catch (err) {
    console.error("GET /api/events unexpected error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

// ── POST /api/events ─────────────────────────────────────────────────────

const VALID_RESULTS: ApiDetectionType[] = ["zylose", "unknown", "silence"];
const STATUS_MAP: Record<ApiDetectionType, ApiDetectionStatus> = {
  zylose: "confirmed",
  unknown: "rejected",
  silence: "detected",
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      device_id = "ZYLOSE-ESP32-01",
      result = "zylose",
      confidence = 0.99,
      unknown_score = 0.01,
      silence_score = 0.0,
      query,
      response,
      intent,
      intent_confidence,
      urgency,
      urgency_confidence,
      oled_text,
      state,
      speaker_verified,
      speaker_confidence,
      speaker_name,
      asr_confidence,
    } = body;

    // Update real-time conversational AI telemetry store immediately
    updateTelemetry({
      deviceId: device_id,
      state: state || (query && response ? "RESPONDING" : query ? "PROCESSING" : "IDLE"),
      ...(query ? { lastQuery: query } : {}),
      ...(response ? { lastResponse: response } : {}),
      ...(intent ? { intent } : {}),
      ...(intent_confidence ? { intentConfidence: Math.round(intent_confidence * 10) / 10 } : {}),
      ...(urgency ? { urgency } : {}),
      ...(urgency_confidence ? { urgencyConfidence: Math.round(urgency_confidence * 10) / 10 } : {}),
      ...(oled_text ? { oledText: oled_text } : {}),
      ...(speaker_verified !== undefined ? { speakerVerified: Boolean(speaker_verified) } : {}),
      ...(speaker_confidence !== undefined ? { speakerConfidence: Math.round(speaker_confidence * 10) / 10 } : {}),
      ...(speaker_name ? { speakerName: speaker_name } : {}),
      ...(asr_confidence !== undefined ? { asrConfidence: Math.round(asr_confidence * 10) / 10 } : {}),
      wakeConfidence: Math.round((confidence > 1 ? confidence : confidence * 100) * 10) / 10,
    });

    const typedResult = (VALID_RESULTS.includes(result) ? result : "zylose") as ApiDetectionType;
    const status = STATUS_MAP[typedResult] || "confirmed";
    const now = new Date().toISOString();

    // Persist to Supabase in background so HTTP response is instant (<5ms)
    if (supabase) {
      void (async () => {
        try {
          // Attempt inserting with full conversational fields
          const { error: insertErr } = await supabase
            .from("events")
            .insert({
              device_id,
              timestamp: now,
              result: typedResult,
              confidence: confidence > 1 ? confidence / 100 : confidence,
              unknown_score: unknown_score ?? 0,
              silence_score: silence_score ?? 0,
              status,
              query: query || null,
              response: response || null,
              intent: intent || null,
              urgency: urgency || null,
            });

          // If columns do not exist yet in Supabase, fallback to basic schema
          if (insertErr && insertErr.message?.includes("column")) {
            await supabase
              .from("events")
              .insert({
                device_id,
                timestamp: now,
                result: typedResult,
                confidence: confidence > 1 ? confidence / 100 : confidence,
                unknown_score: unknown_score ?? 0,
                silence_score: silence_score ?? 0,
                status,
              });
          }

          await supabase
            .from("devices")
            .update({ last_seen: now, status: "online" })
            .eq("id", device_id);
        } catch (dbErr) {
          // Non-critical background sync
        }
      })();
    }

    return NextResponse.json(
      {
        id: `evt_${Date.now()}`,
        timestamp: now,
        status,
        telemetry: getTelemetry(),
      },
      { status: 201 }
    );
  } catch (err) {
    console.error("POST /api/events unexpected error:", err);
    return NextResponse.json(
      { error: "Invalid request body" },
      { status: 400 }
    );
  }
}
