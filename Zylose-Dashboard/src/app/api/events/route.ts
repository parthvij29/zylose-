import { NextRequest, NextResponse } from "next/server";
import { supabase, isSchemaMissingError } from "@/lib/supabase-server";
import type { ApiEvent, ApiDetectionType, ApiDetectionStatus } from "@/lib/types";

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
        "id, device_id, timestamp, result, confidence, unknown_score, silence_score, status",
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

    const { data, error, count } = await query;

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
    if (!supabase) {
      return NextResponse.json(
        { error: "Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local." },
        { status: 503 }
      );
    }

    const body = await request.json();
    const { device_id, result, confidence, unknown_score, silence_score } = body;

    // Validation
    if (!device_id || typeof device_id !== "string") {
      return NextResponse.json(
        { error: "device_id is required and must be a string" },
        { status: 400 }
      );
    }
    if (!result || !VALID_RESULTS.includes(result)) {
      return NextResponse.json(
        { error: `result must be one of: ${VALID_RESULTS.join(", ")}` },
        { status: 400 }
      );
    }
    if (confidence === undefined || typeof confidence !== "number" || confidence < 0 || confidence > 1) {
      return NextResponse.json(
        { error: "confidence is required and must be a number between 0 and 1" },
        { status: 400 }
      );
    }

    const typedResult = result as ApiDetectionType;
    const status = STATUS_MAP[typedResult];
    const now = new Date().toISOString();

    // Insert event
    const { data: event, error: insertError } = await supabase
      .from("events")
      .insert({
        device_id,
        timestamp: now,
        result: typedResult,
        confidence,
        unknown_score: unknown_score ?? 0,
        silence_score: silence_score ?? 0,
        status,
      })
      .select("id, timestamp, status")
      .single();

    if (insertError) {
      console.error("Supabase POST /api/events insert error:", insertError);
      if (isSchemaMissingError(insertError)) {
        return NextResponse.json(
          { error: "Database tables not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      const errorMessage = `${insertError.message} ${insertError.details || ""}`;
      const isConnectionError = /fetch failed|connect timeout|timed out|ECONNRESET|ENOTFOUND/i.test(errorMessage);

      return NextResponse.json(
        {
          error: isConnectionError
            ? "Database temporarily unavailable; retry the event"
            : "Failed to save event",
        },
        isConnectionError
          ? { status: 503, headers: { "Retry-After": "2" } }
          : { status: 500 }
      );
    }

    // Update device last_seen
    await supabase
      .from("devices")
      .update({ last_seen: now, status: "online" })
      .eq("id", device_id);

    return NextResponse.json(
      { id: event.id, timestamp: event.timestamp, status: event.status },
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
