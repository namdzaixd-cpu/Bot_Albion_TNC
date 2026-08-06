// Browser client — dùng ANON KEY. An toàn để import vào client components.
// KHÔNG chứa service role key.
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const supabase = createClient(supabaseUrl, anonKey, {
  auth: { persistSession: true },
});
