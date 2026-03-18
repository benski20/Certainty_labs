-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor) to create the API usage table.
-- Required for usage metering when using SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.

create table if not exists public.api_usage (
  key_id text not null references public.api_keys(id) on delete cascade,
  period text not null,
  endpoint text not null,
  count integer not null default 0,
  primary key (key_id, period, endpoint)
);

create index if not exists idx_api_usage_key_period on public.api_usage (key_id, period);

comment on table public.api_usage is 'Certainty Labs API usage: request counts per key, period (YYYY-MM or YYYY-MM-DD), and endpoint.';

-- RPC for atomic increment (avoids read-modify-write race)
create or replace function public.increment_api_usage(p_key_id text, p_period text, p_endpoint text)
returns void as $$
begin
  insert into public.api_usage (key_id, period, endpoint, count)
  values (p_key_id, p_period, p_endpoint, 1)
  on conflict (key_id, period, endpoint)
  do update set count = public.api_usage.count + 1;
end;
$$ language plpgsql security definer;
