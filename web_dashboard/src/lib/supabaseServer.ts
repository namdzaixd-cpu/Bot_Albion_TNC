// ⚠️ SERVER-ONLY — KHÔNG import file này vào bất kỳ "use client" component nào.
// File chứa SERVICE ROLE KEY (bypass RLS). Chỉ dùng trong API routes (Node runtime).
//
// Lazy singleton: client chỉ tạo khi được dùng (getSupabase()), không lúc import,
// để tránh crash lúc build (collect page data) khi thiếu env.
import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "";
// Ưu tiên SERVICE ROLE (bypass RLS, cần thiết để dashboard đọc/ghi data thật).
// Fallback anon key (NEXT_PUBLIC_*) chỉ để không crash nếu thiếu service role —
// nhưng anon bị RLS deny nên dashboard sẽ trắng -> CẦN set SUPABASE_SERVICE_ROLE_KEY trên env.
const serviceRoleKey =
  process.env.SUPABASE_SERVICE_ROLE_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.SUPABASE_ANON_KEY ||
  "";

let _client: SupabaseClient | null = null;
let _init = false;

export function getSupabase(): SupabaseClient | null {
  if (_init) return _client;
  _init = true;
  if (!supabaseUrl || !serviceRoleKey) {
    console.warn(
      "[supabaseServer] Thiếu NEXT_PUBLIC_SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY — client không khởi tạo."
    );
    return null;
  }
  _client = createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  return _client;
}

// Backward-compat: `supabase` lazy proxy để route cũ dùng `supabase.from(...)` vẫn chạy.
// Chỉ dùng khi env đã sẵn sàng (runtime). Ở build-time thiếu env sẽ throw rõ ràng.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const supabase = new Proxy({} as any, {
  get(_t, prop) {
    const c = getSupabase();
    if (!c) throw new Error("Supabase server client chưa khởi tạo (thiếu env).");
    const v = (c as any)[prop];
    return typeof v === "function" ? v.bind(c) : v;
  },
}) as any;
