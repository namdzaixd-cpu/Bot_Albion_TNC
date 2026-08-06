-- =============================================================================
-- Bot_Albion_TNC — SCHEMA V2 (Non-destructive apply to existing project)
-- Áp dụng lên project jbfqniokcluggcolwgut (Bot_Albion_TNC)
-- Nguyên tắc: KHÔNG DROP, KHÔNG đổi type gây mất data. Chỉ ADD column / ADD constraint / INDEX / RLS.
-- =============================================================================

-- 0. Helper trigger
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. ALTER existing tables: add created_at / updated_at / guild_id where missing
ALTER TABLE public.guild_config      ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.guild_config      ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.ai_config         ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.ai_config         ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE public.ai_config         ALTER COLUMN updated_at SET NOT NULL;

ALTER TABLE public.user_activity    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.user_economy     ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.sp_metadata       ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.sp_metadata       ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.alo_tts_config   ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.alo_tts_config   ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.json_storage     ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.json_storage     ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- corebank_config: KHÔNG thêm FK (dùng guild_id='default' riêng, không match guild_config)
-- Giữ independent để không phá data cũ.


-- chat_history: thiếu updated_at + guild_id
ALTER TABLE public.chat_history      ADD COLUMN IF NOT EXISTS guild_id text;
ALTER TABLE public.chat_history      ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- core_credited: thiếu created_at/updated_at (có sẵn credited_at)
ALTER TABLE public.core_credited    ADD COLUMN IF NOT EXISTS guild_id text;
ALTER TABLE public.core_credited    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.core_credited    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- sp_transactions: thiếu created_at/updated_at/guild_id
ALTER TABLE public.sp_transactions  ADD COLUMN IF NOT EXISTS guild_id text;
ALTER TABLE public.sp_transactions  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.sp_transactions  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- blacklist: thiếu created_at/updated_at
ALTER TABLE public.blacklist        ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.blacklist        ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- discord_channels / discord_roles: thiếu created_at/updated_at
ALTER TABLE public.discord_channels ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.discord_channels ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.discord_roles    ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.discord_roles    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- system_logs: thiếu guild_id (id là uuid, giữ nguyên)
ALTER TABLE public.system_logs      ADD COLUMN IF NOT EXISTS guild_id text;

-- corebank_config: bỏ FK (guild_id='default' riêng)

ALTER TABLE public.core_credited    ADD CONSTRAINT fk_core_guild      FOREIGN KEY (guild_id) REFERENCES public.guild_config(guild_id) ON DELETE SET NULL;
ALTER TABLE public.sp_transactions  ADD CONSTRAINT fk_sp_guild        FOREIGN KEY (guild_id) REFERENCES public.guild_config(guild_id) ON DELETE SET NULL;
ALTER TABLE public.blacklist        ADD CONSTRAINT fk_blacklist_guild FOREIGN KEY (source_guild_id) REFERENCES public.guild_config(guild_id) ON DELETE SET NULL;
ALTER TABLE public.discord_channels ADD CONSTRAINT fk_chan_guild      FOREIGN KEY (guild_id) REFERENCES public.guild_config(guild_id) ON DELETE CASCADE;
ALTER TABLE public.discord_roles    ADD CONSTRAINT fk_role_guild      FOREIGN KEY (guild_id) REFERENCES public.guild_config(guild_id) ON DELETE CASCADE;
ALTER TABLE public.system_logs      ADD CONSTRAINT fk_log_guild       FOREIGN KEY (guild_id) REFERENCES public.guild_config(guild_id) ON DELETE SET NULL;

-- 3. Triggers auto-updated_at (CREATE OR REPLACE TRIGGER - PG15 supported)
DROP TRIGGER IF EXISTS trg_guild_config_upd ON public.guild_config;
CREATE TRIGGER trg_guild_config_upd BEFORE UPDATE ON public.guild_config FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_ai_config_upd ON public.ai_config;
CREATE TRIGGER trg_ai_config_upd BEFORE UPDATE ON public.ai_config FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_user_activity_upd ON public.user_activity;
CREATE TRIGGER trg_user_activity_upd BEFORE UPDATE ON public.user_activity FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_user_economy_upd ON public.user_economy;
CREATE TRIGGER trg_user_economy_upd BEFORE UPDATE ON public.user_economy FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_sp_metadata_upd ON public.sp_metadata;
CREATE TRIGGER trg_sp_metadata_upd BEFORE UPDATE ON public.sp_metadata FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_alo_tts_config_upd ON public.alo_tts_config;
CREATE TRIGGER trg_alo_tts_config_upd BEFORE UPDATE ON public.alo_tts_config FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_json_storage_upd ON public.json_storage;
CREATE TRIGGER trg_json_storage_upd BEFORE UPDATE ON public.json_storage FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_corebank_config_upd ON public.corebank_config;
CREATE TRIGGER trg_corebank_config_upd BEFORE UPDATE ON public.corebank_config FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_chat_history_upd ON public.chat_history;
CREATE TRIGGER trg_chat_history_upd BEFORE UPDATE ON public.chat_history FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_core_credited_upd ON public.core_credited;
CREATE TRIGGER trg_core_credited_upd BEFORE UPDATE ON public.core_credited FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_sp_transactions_upd ON public.sp_transactions;
CREATE TRIGGER trg_sp_transactions_upd BEFORE UPDATE ON public.sp_transactions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_blacklist_upd ON public.blacklist;
CREATE TRIGGER trg_blacklist_upd BEFORE UPDATE ON public.blacklist FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_discord_channels_upd ON public.discord_channels;
CREATE TRIGGER trg_discord_channels_upd BEFORE UPDATE ON public.discord_channels FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
DROP TRIGGER IF EXISTS trg_discord_roles_upd ON public.discord_roles;
CREATE TRIGGER trg_discord_roles_upd BEFORE UPDATE ON public.discord_roles FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 4. Indexes
CREATE INDEX IF NOT EXISTS idx_blacklist_discord ON public.blacklist(discord_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_ingame  ON public.blacklist(ingame_id);
CREATE INDEX IF NOT EXISTS idx_chat_guild    ON public.chat_history(guild_id);
CREATE INDEX IF NOT EXISTS idx_chat_channel  ON public.chat_history(channel_id);
CREATE INDEX IF NOT EXISTS idx_chat_created  ON public.chat_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_core_msg      ON public.core_credited(message_id);
CREATE INDEX IF NOT EXISTS idx_core_guild    ON public.core_credited(guild_id);
CREATE INDEX IF NOT EXISTS idx_sp_player     ON public.sp_transactions(player_name);
CREATE INDEX IF NOT EXISTS idx_sp_inserted   ON public.sp_transactions(inserted_at DESC);
CREATE INDEX IF NOT EXISTS idx_sp_guild      ON public.sp_transactions(guild_id);
CREATE INDEX IF NOT EXISTS idx_chan_guild    ON public.discord_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_role_guild    ON public.discord_roles(guild_id);
CREATE INDEX IF NOT EXISTS idx_logs_level    ON public.system_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created  ON public.system_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_guild    ON public.system_logs(guild_id);

-- 5. RLS
ALTER TABLE public.guild_config      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_config         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_economy      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sp_metadata       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alo_tts_config    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.json_storage      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.corebank_config   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blacklist         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_channels  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discord_roles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.core_credited     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sp_transactions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_logs       ENABLE ROW LEVEL SECURITY;

-- Policy: service_role bypass all
DO $$
DECLARE t text; tbls text[] := ARRAY[
 'guild_config','ai_config','user_activity','user_economy','sp_metadata',
 'alo_tts_config','json_storage','corebank_config','blacklist','discord_channels',
 'discord_roles','chat_history','core_credited','sp_transactions','system_logs'];
BEGIN
  FOREACH t IN ARRAY tbls LOOP
    EXECUTE format('DROP POLICY IF EXISTS pol_service_all ON public.%I;', t);
    EXECUTE format('CREATE POLICY pol_service_all ON public.%1$I FOR ALL TO service_role USING (true) WITH CHECK (true);', t);
  END LOOP;
END $$;

-- HOÀN TẤT: không có DROP TABLE nào.
