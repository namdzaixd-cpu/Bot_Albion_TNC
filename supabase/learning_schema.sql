-- ============================================================
-- Schema: Memory & Knowledge (Long-term memory + self-learning)
-- Dùng cho tính năng bot tự nhớ user + học skill từ người dùng.
-- Chạy trong Supabase SQL Editor (project Bot_Albion_TNC).
-- KHÔNG đụng các bảng cũ (json_storage, guild_config...).
-- ============================================================

-- Cần extension pgvector để search ngữ nghĩa.
create extension if not exists vector;

-- 1) memory: nhớ user / fact ngắn (như "memory" của Hermes)
create table if not exists memory (
    id          bigint generated always as identity primary key,
    user_id     text not null,                 -- Discord user id (hoặc 'global')
    kind        text not null default 'fact',  -- 'user' | 'fact' | 'preference'
    content     text not null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);
create index if not exists idx_memory_user on memory(user_id);
create index if not exists idx_memory_user_kind on memory(user_id, kind);

-- 2) knowledge: kiến thức / skill user dạy (có embedding để semantic search)
create table if not exists knowledge (
    id          bigint generated always as identity primary key,
    guild_id    text,                            -- scope theo server (nullable)
    title       text not null,
    body        text not null,
    embedding   vector(1536),                    -- OpenAI text-embedding-3-small
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);
create index if not exists idx_knowledge_guild on knowledge(guild_id);

-- Index để search vector nhanh (cosine)
create index if not exists idx_knowledge_embedding
    on knowledge using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Hàm lưu knowledge kèm embedding (gọi từ backend sau khi tạo embedding)
-- Backend tính embedding rồi truyền vào, tránh để DB gọi external API.
-- (Supabase Edge Function có thể làm, nhưng backend đơn giản hơn.)

-- RLS: backend dùng service_role key -> bypass. Nếu dùng anon thì bật RLS riêng.
-- Với bot (service_role) không cần RLS policy.

comment on table memory is 'Long-term memory: user profile, facts, preferences.';
comment on table knowledge is 'User-taught knowledge/skills with semantic search via pgvector.';
