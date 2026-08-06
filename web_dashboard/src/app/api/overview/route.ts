import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

const GUILD_ID = process.env.DISCORD_GUILD_ID || process.env.GUILD_ID || "default";

export async function GET() {
  try {
    // Song song lấy dữ liệu từ các bảng
    const [corebank, blacklist, logs, siphoned] = await Promise.all([
      supabase.from("corebank_config").select("*").eq("guild_id", GUILD_ID).maybeSingle(),
      supabase.from("blacklist").select("id", { count: "exact" }).eq("guild_id", GUILD_ID),
      supabase.from("logs").select("*").order("created_at", { ascending: false }).limit(8),
      supabase.from("siphoned_energy").select("*", { count: "exact" }).eq("guild_id", GUILD_ID),
    ]);

    const stats = {
      members: 1284, // placeholder: thay bằng API Discord thực tế nếu có
      corebank_total: corebank.data?.total_silver ?? 0,
      blacklist_count: blacklist.count ?? 0,
      ai_today: logs.data?.filter((l: any) => l.type === "ai").length ?? 0,
    };

    const activity = (logs.data || []).map((l: any) => ({
      time: l.created_at,
      event: l.message || l.event || "—",
      module: l.module || l.type || "system",
      status: l.status || "ok",
    }));

    return NextResponse.json({
      stats,
      activity,
      siphoned_count: siphoned.count ?? 0,
      updated_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
