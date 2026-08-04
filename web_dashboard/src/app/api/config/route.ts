import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

// Lấy GUILD_ID từ môi trường
const GUILD_ID = process.env.DISCORD_GUILD_ID || "712258265769050164";

export async function GET() {
  try {
    const { data, error } = await supabase
      .from('guild_config')
      .select('*')
      .eq('guild_id', GUILD_ID)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        // Không tìm thấy bản ghi, có thể bot chưa tạo
        return NextResponse.json({ 
          guild_id: GUILD_ID,
          is_onboard_enabled: false 
        });
      }
      throw error;
    }

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Lỗi khi gọi API /api/config:", error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { is_onboard_enabled, ...otherUpdates } = body;

    const updateData: any = {};
    if (is_onboard_enabled !== undefined) {
      updateData.is_onboard_enabled = is_onboard_enabled;
    }
    
    for (const key of Object.keys(otherUpdates)) {
        updateData[key] = otherUpdates[key];
    }

    const { data, error } = await supabase
      .from('guild_config')
      .update(updateData)
      .eq('guild_id', GUILD_ID)
      .select()
      .single();

    if (error) throw error;

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Lỗi cập nhật config:", error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
