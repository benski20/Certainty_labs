-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor).
-- Creates a view for total + breakdown usage per user, for dashboard loading.
-- Depends on: api_keys, api_usage (run supabase_api_keys.sql and supabase_api_usage.sql first).

-- View: total and breakdown usage per user per period
-- Keys without user_id are excluded (or use COALESCE(k.user_id, 'anonymous') to include them)
create or replace view public.user_usage_summary as
select
  k.user_id,
  u.period,
  sum(u.count) as total,
  sum(case when u.endpoint = 'train' then u.count else 0 end) as train,
  sum(case when u.endpoint = 'rerank' then u.count else 0 end) as rerank,
  sum(case when u.endpoint = 'score' then u.count else 0 end) as score,
  sum(case when u.endpoint = 'pipeline' then u.count else 0 end) as pipeline,
  sum(case when u.endpoint = 'models/download' then u.count else 0 end) as models_download
from public.api_usage u
join public.api_keys k on u.key_id = k.id
where k.user_id is not null
group by k.user_id, u.period;

comment on view public.user_usage_summary is 'Aggregated usage per user per period: total + breakdown by endpoint. For dashboard.';
