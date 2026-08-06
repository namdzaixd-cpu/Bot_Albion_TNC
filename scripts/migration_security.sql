-- ============================================================================
-- Migration: RLS hardening & indexes for Bot_Albion_TNC
-- Áp dụng SAU scripts/migration.sql (schema cơ bản).
-- Mục tiêu: bảo mật đúng chuẩn, hiệu năng truy vấn tốt.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. ROW LEVEL SECURITY
-- Tất cả bảng đã ENABLE RLS ở migration gốc. Ở đây ta định nghĩa policy:
--   - SERVICE ROLE (bot & API server): full access (bypass RLS mặc định).
--   - ANON KEY (browser): DENY mọi thứ (không bao giờ cho client truy cập trực tiếp).
--   - AUTHENTICATED (nếu sau này có user login): chỉ SELECT trên dữ liệu public.
-- Lưu ý: Supabase service_role tự động bypass RLS, nên policy dưới chủ yếu
--        nhằm khóa anon/authenticated không mong muốn.
-- ----------------------------------------------------------------------------

-- Xoá policy cũ (nếu có) để idempotent
drop policy if exists "anon_deny_all" on public.guild_config;
drop policy if exists "anon_deny_all" on public.ai_config;
drop policy if exists "anon_deny_all" on public.user_activity;
drop policy if exists "anon_deny_all" on public.user_economy;
drop policy if exists "anon_deny_all" on public.sp_metadata;
drop policy if exists "anon_deny_all" on public.alo_tts_config;
drop policy if exists "anon_deny_all" on public.json_storage;
drop policy if exists "anon_deny_all" on public.corebank_config;
drop policy if exists "anon_deny_all" on public.blacklist;
drop policy if exists "anon_deny_all" on public.siphoned_energy;
drop policy if exists "anon_deny_all" on public.logs;

-- Helper: tạo policy DENY cho anon trên mọi bảng
create policy "anon_deny_all" on public.guild_config
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.ai_config
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.user_activity
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.user_economy
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.sp_metadata
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.alo_tts_config
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.json_storage
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.corebank_config
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.blacklist
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.siphoned_energy
  for all to anon using (false) with check (false);
create policy "anon_deny_all" on public.logs
  for all to anon using (false) with check (false);

-- ----------------------------------------------------------------------------
-- 2. INDEXES — tăng tốc truy vấn theo guild_id / user_id (đã là PK ở một số bảng,
--    nhưng các bảng blacklist / siphoned / logs cần index theo guild_id).
-- ----------------------------------------------------------------------------

create index if not exists idx_blacklist_guild on public.blacklist (guild_id);
create index if not exists idx_siphoned_guild on public.siphoned_energy (guild_id);
create index if not exists idx_logs_guild on public.logs (guild_id);
create index if not exists idx_logs_created on public.logs (created_at desc);
create index if not exists idx_user_activity_updated on public.user_activity (updated_at desc);
create index if not exists idx_user_economy_silver on public.user_economy (silver_pieces desc);

-- ----------------------------------------------------------------------------
-- 3. BẢO VỆ json_storage — giới hạn kích thước data để tránh blob phình to.
--    (Supabase không hỗ trợ check trên jsonb size trực tiếp, nên ta dùng trigger.)
-- ----------------------------------------------------------------------------

create or replace function public.trg_json_storage_size()
returns trigger as $$
begin
  if pg_column_size(new.data) > 1048576 then  -- 1MB
    raise exception 'json_storage.data quá lớn (>1MB)';
  end if;
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_json_storage_size on public.json_storage;
create trigger trg_json_storage_size
  before insert or update on public.json_storage
  for each row execute function public.trg_json_storage_size();
