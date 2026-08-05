-- SQL Migration Script: Seoul to Singapore
-- Generated manually for Bot_Albion_TNC

-- 1. Table: guild_config
CREATE TABLE IF NOT EXISTS public.guild_config (
    guild_id text PRIMARY KEY,
    is_onboard_enabled boolean DEFAULT true,
    apply_channel_id text,
    member_role_id text,
    officer_role_id text,
    rules_channel_id text,
    chat_channel_id text,
    question_channel_id text
);
ALTER TABLE public.guild_config ENABLE ROW LEVEL SECURITY;

-- 2. Table: ai_config
CREATE TABLE IF NOT EXISTS public.ai_config (
    guild_id text PRIMARY KEY,
    model text,
    available_models jsonb DEFAULT '[]'::jsonb,
    channel_buffers jsonb DEFAULT '{}'::jsonb,
    intercept_channels jsonb DEFAULT '[]'::jsonb,
    autowiki_channels jsonb DEFAULT '[]'::jsonb,
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.ai_config ENABLE ROW LEVEL SECURITY;

-- 3. Table: user_activity
CREATE TABLE IF NOT EXISTS public.user_activity (
    user_id text PRIMARY KEY,
    last_seen text,
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.user_activity ENABLE ROW LEVEL SECURITY;

-- 4. Table: user_economy
CREATE TABLE IF NOT EXISTS public.user_economy (
    user_id text PRIMARY KEY,
    silver_pieces integer DEFAULT 0,
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.user_economy ENABLE ROW LEVEL SECURITY;

-- 5. Table: sp_metadata
CREATE TABLE IF NOT EXISTS public.sp_metadata (
    id integer PRIMARY KEY DEFAULT 1,
    last_update text DEFAULT 'Chưa có dữ liệu'::text
);
ALTER TABLE public.sp_metadata ENABLE ROW LEVEL SECURITY;

-- 6. Table: alo_tts_config
CREATE TABLE IF NOT EXISTS public.alo_tts_config (
    id integer PRIMARY KEY DEFAULT 1,
    read_name jsonb DEFAULT '{}'::jsonb,
    rejoin jsonb DEFAULT '{}'::jsonb,
    afk jsonb DEFAULT '{}'::jsonb
);
ALTER TABLE public.alo_tts_config ENABLE ROW LEVEL SECURITY;

-- 7. Table: json_storage
CREATE TABLE IF NOT EXISTS public.json_storage (
    file_name text PRIMARY KEY,
    data jsonb DEFAULT '{}'::jsonb
);
ALTER TABLE public.json_storage ENABLE ROW LEVEL SECURITY;

-- Insert data for public.sp_metadata
INSERT INTO public.sp_metadata (id, last_update) VALUES (1, '2026-07-06 20:12:04') ON CONFLICT (id) DO UPDATE SET last_update = EXCLUDED.last_update;

-- Insert data for public.alo_tts_config
INSERT INTO public.alo_tts_config (id, read_name, rejoin, afk) VALUES (1, '{"712258265769050164":true}'::jsonb, '{}'::jsonb, '{}'::jsonb) ON CONFLICT (id) DO UPDATE SET read_name = EXCLUDED.read_name, rejoin = EXCLUDED.rejoin, afk = EXCLUDED.afk;

-- Insert data for public.ai_config
INSERT INTO public.ai_config (guild_id, model, available_models, channel_buffers, intercept_channels, autowiki_channels, updated_at) VALUES ('default', 'inclusionai/ling-3.0-flash:free', '["google/gemini-3.5-flash-lite", "google/gemini-3.1-flash-lite", "google/gemma-4-31b-it", "nvidia/nemotron-3-ultra-550b-a55b:free", "nvidia/nemotron-3-super-120b-a12b:free", "poolside/laguna-s-2.1:free", "inclusionai/ling-3.0-flash:free", "cohere/north-mini-code:free"]'::jsonb, '{}'::jsonb, '[]'::jsonb, '[]'::jsonb, '2026-08-03 20:21:19.112499+00') ON CONFLICT (guild_id) DO UPDATE SET model = EXCLUDED.model, available_models = EXCLUDED.available_models, channel_buffers = EXCLUDED.channel_buffers, intercept_channels = EXCLUDED.intercept_channels, autowiki_channels = EXCLUDED.autowiki_channels, updated_at = EXCLUDED.updated_at;

-- Insert data for public.user_activity
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('816978816782172200', '2026-08-01 16:41:16', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('704367471548825790', '2026-08-01 16:24:07', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('778593128566882314', '2026-08-01 19:43:56', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('787334435884105820', '2026-08-01 17:11:08', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('471166977679949827', '2026-07-31 10:56:59', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('638931124646838323', '2026-08-01 18:09:44', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('881808692046086154', '2026-08-01 19:11:54', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('862207655581450282', '2026-07-31 11:05:59', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('735128444282732565', '2026-07-31 11:09:56', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('756523718079152238', '2026-07-31 16:08:44', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1046802011242385478', '2026-08-01 17:43:49', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('959420162572976139', '2026-07-31 15:31:51', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1064162008771084318', '2026-08-01 18:20:41', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1064077958840602634', '2026-08-01 13:22:07', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('769019173376098314', '2026-07-31 16:18:41', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1470333282410561588', '2026-07-31 16:21:30', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('903254400976437298', '2026-08-01 17:07:29', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('393225645934772225', '2026-08-01 14:54:29', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('419670846873927690', '2026-08-01 17:59:50', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1502635249899798670', '2026-08-01 13:43:17', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('871388208766799882', '2026-08-01 16:10:54', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1102987661565767760', '2026-08-01 13:32:25', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('447586836467154946', '2026-08-01 13:44:32', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('935370928978788442', '2026-08-01 14:21:27', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('743166024265891931', '2026-08-01 15:19:41', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('607992233542680779', '2026-08-01 16:58:09', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('586143271642726410', '2026-08-01 16:18:05', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1225253423797243995', '2026-08-01 16:40:45', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('389427179823431681', '2026-08-01 16:44:25', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('990238139480145951', '2026-08-01 17:59:03', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('1009787764897755251', '2026-08-01 19:17:36', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_activity (user_id, last_seen, updated_at) VALUES ('959110682882748456', '2026-08-01 19:35:28', '2026-08-03 20:21:19.571135+00') ON CONFLICT (user_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = EXCLUDED.updated_at;

-- Insert data for public.user_economy
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('PuzzyDick', 794, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('neitt', 1061, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Kaijou', 253, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('LuanVu', 0, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('DungNG123', 705, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('TheLongboii', -122, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('ZingX', 854, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('LeoKira', 166, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Tokennn', -10, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('SquidThieuNang', -312, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('ShootingStar26', -53, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('3bie', -4, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('CallmePhJ', 21, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('N4MDZ4I', 795, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('L1GHT', 164, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('ChayTuTa', -351, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Kira19', 48, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Kudo2ten', 582, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('MrOG', -666, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('AcmaTheKING', -333, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Polygrap', 517, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('blackPtom', 10, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('TrungKhongNgu', -540, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('AnhNass', -654, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('NHPham', 49, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('KhanhSPN', 25, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('YeuHung', -69, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('0sao', 4, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('HwanAlbion', 257, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('44one', 245, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('MeoBeoChimTo', -10, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('ZzJSSSzZ', 85, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('TieuYeuQuaii', 0, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Jennieee', 414, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('SilverThiefs', 190, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('Doneeeeeeeeeeeee', 8, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
INSERT INTO public.user_economy (user_id, silver_pieces, updated_at) VALUES ('PeguinX', 338, '2026-08-03 20:21:43.470021+00') ON CONFLICT (user_id) DO UPDATE SET silver_pieces = EXCLUDED.silver_pieces, updated_at = EXCLUDED.updated_at;
