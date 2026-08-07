import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseServer";

export async function GET() {
  try {
    // Lấy tối đa 500 dòng log gần nhất
    const { data, error } = await supabase
      .from('system_logs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(500);

    if (error) {
      console.error('Error fetching logs:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    // Đảo ngược lại mảng để render từ trên xuống dưới (từ cũ đến mới)
    const sortedData = data ? data.reverse() : [];
    
    return NextResponse.json(sortedData);
  } catch (err) {
    console.error('Unexpected error:', err);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function DELETE() {
  try {
    // Xoá tất cả log
    const { error } = await supabase
      .from('system_logs')
      .delete()
      .neq('id', '00000000-0000-0000-0000-000000000000'); // Xóa tất cả với mẹo query

    if (error) {
      console.error('Error clearing logs:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error('Unexpected error:', err);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
