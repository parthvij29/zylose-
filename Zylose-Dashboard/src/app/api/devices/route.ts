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

    const { data, error } = await supabase
      .from("devices")
      .select("*")
      .order("created_at", { ascending: true });

    if (error) {
      console.error("Supabase GET /api/devices error:", error);
      if (isSchemaMissingError(error)) {
        return NextResponse.json(
          { error: "Database table 'devices' not found. Please run schema.sql in Supabase SQL editor." },
          { status: 503 }
        );
      }
      return NextResponse.json(
        { error: "Failed to fetch devices" },
        { status: 500 }
      );
    }

    return NextResponse.json({ devices: data || [] });
  } catch (err) {
    console.error("GET /api/devices unexpected error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
