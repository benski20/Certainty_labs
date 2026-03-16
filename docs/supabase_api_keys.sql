-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor) to create the API keys table.
-- Required for production when using SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.

create table if not exists public.api_keys (
  id text primary key,
  name text not null default 'default',
  key_hash text not null,
  prefix text not null,
  created_at double precision not null
);

create unique index if not exists idx_api_keys_key_hash on public.api_keys (key_hash);

comment on table public.api_keys is 'Certainty Labs API keys (key_hash only; raw key never stored).';
