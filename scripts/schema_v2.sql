-- =============================================================================
-- Bot_Albion_TNC — SCHEMA V2 (Production-ready, Non-destructive)
-- =============================================================================
-- Mục tiêu: Chuẩn hóa toàn bộ Database Schema theo tiêu chuẩn backend chuyên nghiệp.
-- Nguyên tắc AN TOÀN: KHÔNG xóa bất kỳ bảng/dữ liệu cũ nào.
--   - Bảng đã tồn tại -> ALTER thêm cột (IF NOT EXISTS), giữ nguyên data.
--   - Bảng chưa có      -> CREATE TABLE IF NOT EXISTS.
--   - Trigger updated_at áp dụng cho mọi bảng (idempotent).
-- Chạy: Supabase Studio -> SQL Editor -> Paste toàn bộ -> Run.
-- Hoặc: psql "postgresql://..." -f schema_v2.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. HELPER: trigger auto-update updated_at (idempotent)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Hàm tiện ích gắn trigger (bỏ qua nếu đã có)
CREATE OR REPLACE FUNCTION public.attach_updated_at(tbl text)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgrelid = tbl::regclass AND tgname = 'trg_' || tbl || '_updated'
    ) THEN
        EXECUTE format(
            'CREATE TRIGGER trg_%1$s_updated BEFORE UPDATE ON %1$s
             FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();',
            tbl
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. EXISTING TABLES — chuẩn hóa bổ sung (giữ data cũ)
-- =============================================================================

-- 1.1 guild_config (Onboarding + CoreBank config chung)
ALTER TABLE public.guild_config
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.guild_config
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
-- Đảm bảo các cột Discord ID là TEXT (đã đúng). Giữ nguyên.
SELECT public.attach_updated_at('public.guild_config');

-- 1.2 ai_config
ALTER TABLE public.ai_config
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
-- updated_at đã có; đảm bảo NOT NULL
ALTER TABLE public.ai_config ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE public.ai_config ALTER COLUMN updated_at SET NOT NULL;
SELECT public.attach_updated_at('public.ai_config');

-- 1.3 user_activity (LastSeen)
ALTER TABLE public.user_activity
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
-- last_seen hiện là TEXT -> giữ (code ghi string). Không đổi type để tránh break.
SELECT public.attach_updated_at('public.user_activity');

-- 1.4 user_economy (Siphoned points)
ALTER TABLE public.user_economy
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
-- silver_pieces integer -> Nâng lên NUMERIC để chính xác hơn (ko mất data, widen only)
ALTER TABLE public.user_economy ALTER COLUMN silver_pieces TYPE numeric(18,2)
    USING silver_pieces::numeric(18,2);
SELECT public.attach_updated_at('public.user_economy');

-- 1.5 sp_metadata
ALTER TABLE public.sp_metadata
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.sp_metadata
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
SELECT public.attach_updated_at('public.sp_metadata');

-- 1.6 alo_tts_config
ALTER TABLE public.alo_tts_config
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.alo_tts_config
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
SELECT public.attach_updated_at('public.alo_tts_config');

-- 1.7 json_storage
ALTER TABLE public.json_storage
    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.json_storage
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
SELECT public.attach_updated_at('public.json_storage');

-- =============================================================================
-- 2. NEW TABLES (chưa có DDL chuẩn) — CREATE IF NOT EXISTS
-- =============================================================================

-- 2.1 blacklist (Global Blacklist)
CREATE TABLE IF NOT EXISTS public.blacklist (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    discord_id       text,
    ingame_name      text,
    ingame_id        text,
    reason           text,
    added_by_discord_id text,
    source_guild_id  text REFERENCES public.guild_config(guild_id) ON DELETE SET NULL,
    timestamp        timestamptz DEFAULT now(),
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_blacklist_discord ON public.blacklist(discord_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_ingame  ON public.blacklist(ingame_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_guild  ON public.blacklist(source_guild_id);
SELECT public.attach_updated_at('public.blacklist');

-- 2.2 discord_channels (FK cache)
CREATE TABLE IF NOT EXISTS public.discord_channels (
    id          text PRIMARY KEY,
    guild_id    text REFERENCES public.guild_config(guild_id) ON DELETE CASCADE,
    name        text,
    type        text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_channels_guild ON public.discord_channels(guild_id);
SELECT public.attach_updated_at('public.discord_channels');

-- 2.3 discord_roles
CREATE TABLE IF NOT EXISTS public.discord_roles (
    id          text PRIMARY KEY,
    guild_id    text REFERENCES public.guild_config(guild_id) ON DELETE CASCADE,
    name        text,
    color       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_roles_guild ON public.discord_roles(guild_id);
SELECT public.attach_updated_at('public.discord_roles');

-- 2.4 chat_history (ChatLogger + AI search)
CREATE TABLE IF NOT EXISTS public.chat_history (
    id            text PRIMARY KEY,
    guild_id      text REFERENCES public.guild_config(guild_id) ON DELETE SET NULL,
    channel_id    text,
    channel_name  text,
    user_id       text,
    author_name   text,
    content       text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chat_guild    ON public.chat_history(guild_id);
CREATE INDEX IF NOT EXISTS idx_chat_channel  ON public.chat_history(channel_id);
CREATE INDEX IF NOT EXISTS idx_chat_created  ON public.chat_history(created_at DESC);
SELECT public.attach_updated_at('public.chat_history');

-- 2.5 core_credited (CoreBank dedupe)
CREATE TABLE IF NOT EXISTS public.core_credited (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id  text NOT NULL,
    user_id     text,
    guild_id    text REFERENCES public.guild_config(guild_id) ON DELETE SET NULL,
    amount      numeric(18,2) DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (message_id)
);
CREATE INDEX IF NOT EXISTS idx_core_msg ON public.core_credited(message_id);
CREATE INDEX IF NOT EXISTS idx_core_guild ON public.core_credited(guild_id);
SELECT public.attach_updated_at('public.core_credited');

-- 2.6 sp_transactions (Siphoned log)
CREATE TABLE IF NOT EXISTS public.sp_transactions (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_name    text NOT NULL,
    amount         numeric(18,2) DEFAULT 0,
    log_timestamp  timestamptz,
    guild_id       text REFERENCES public.guild_config(guild_id) ON DELETE SET NULL,
    inserted_at    timestamptz NOT NULL DEFAULT now(),
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sp_player   ON public.sp_transactions(player_name);
CREATE INDEX IF NOT EXISTS idx_sp_inserted ON public.sp_transactions(inserted_at DESC);
CREATE INDEX IF NOT EXISTS idx_sp_guild    ON public.sp_transactions(guild_id);
SELECT public.attach_updated_at('public.sp_transactions');

-- 2.7 system_logs (SystemLogger)
CREATE TABLE IF NOT EXISTS public.system_logs (
    id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    level     text NOT NULL DEFAULT 'INFO',
    module    text,
    message   text,
    guild_id  text REFERENCES public.guild_config(guild_id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now()
    -- system_logs: chỉ ghi, không updated_at
);
CREATE INDEX IF NOT EXISTS idx_logs_level    ON public.system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created  ON public.system_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_guild    ON public.system_logs(guild_id);

-- =============================================================================
-- 3. ROW LEVEL SECURITY (RLS)
-- =============================================================================
-- Nguyên tắc: Service Role (bot + backend API) BYPASS RLS -> đọc/ghi thoải mái.
-- Anon Key (browser) -> DENY ALL (không client trực tiếp truy cập DB).
-- Nếu sau này cần dashboard đọc 1 số bảng qua anon, thêm policy riêng ở đây.

-- Bật RLS cho mọi bảng
ALTER TABLE public.guild_config      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_config         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_economy      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sp_metadata       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alo_tts_config    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.json_storage      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blacklist         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_channels  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_roles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.core_credited     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sp_transactions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_logs       ENABLE ROW LEVEL SECURITY;

-- Hàm helper kiểm tra Service Role (dùng biến session do Supabase set khi dùng service key)
-- Supabase tự set role = 'service_role' khi dùng service_role key -> cho phép toàn quyền.
-- Dưới đây là policy an toàn: chỉ service_role mới truy cập.

CREATE OR REPLACE FUNCTION public.is_service_role() RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT current_user = 'service_role';
$$;

-- Drop policy cũ nếu có (idempotent) rồi tạo mới
DO $$
DECLARE
    t text;
    tbls text[] := ARRAY[
        'guild_config','ai_config','user_activity','user_economy','sp_metadata',
        'alo_tts_config','json_storage','blacklist','discord_channels',
        'discord_roles','chat_history','core_credited','sp_transactions','system_logs'
    ];
BEGIN
    FOREACH t IN ARRAY tbls LOOP
        EXECUTE format('DROP POLICY IF EXISTS pol_service_all ON public.%I;', t);
        EXECUTE format(
            'CREATE POLICY pol_service_all ON public.%1$I
             FOR ALL TO service_role
             USING (true) WITH CHECK (true);', t
        );
    END LOOP;
END $$;

-- (Tùy chọn) Nếu dashboard cần đọc public mà không qua API:
-- CREATE POLICY pol_anon_read ON public.guild_config FOR SELECT TO anon USING (true);
-- Hiện tại: KHÔNG cho anon -> mọi truy cập phải qua backend (service role).

-- =============================================================================
-- 4. (Optional) Dữ liệu seed tối thiểu nếu bảng trống
-- =============================================================================
INSERT INTO public.guild_config (guild_id)
SELECT '712258265769050164'
WHERE NOT EXISTS (SELECT 1 FROM public.guild_config WHERE guild_id = '712258265769050164');

-- =============================================================================
-- HOÀN TẤT. Không có lệnh DROP nào -> dữ liệu cũ được bảo toàn.
-- =============================================================================
