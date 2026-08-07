import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseServer";

const GUILD_ID = process.env.GUILD_ID || "default";

export async function GET() {
  try {
    const { data, error } = await supabase
      .from("corebank_config")
      .select("*")
      .eq("guild_id", GUILD_ID)
      .single();

    if (error && error.code !== "PGRST116") {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Nếu chưa có, trả về mặc định
    return NextResponse.json(data || {
      core_channel_id: "",
      bank_channel_id: "",
      unbelievaboat_token: "",
      emoji_map: {},
      auto_react: true
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function PATCH(req: Request) {
  try {
    const body = await req.json();

    const { data, error } = await supabase
      .from("corebank_config")
      .upsert({ guild_id: GUILD_ID, ...body })
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    // Gửi webhook để Bot reload config (nếu có webhook)
    const webhookUrl = process.env.BOT_WEBHOOK_URL;
    if (webhookUrl) {
      try {
        await fetch(webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: "config_reload" })
        });
      } catch (e) {
        console.error("Lỗi gọi webhook tới bot:", e);
      }
    }

    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
