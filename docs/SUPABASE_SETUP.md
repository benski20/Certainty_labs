# Supabase setup for API key storage

Use **Supabase** (Postgres) for persistent API keys in production. If you don’t set Supabase env vars, the API uses local file storage (`certainty_workspace/api_keys.json`) for development.

## 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and create a project.
2. In the dashboard: **Project Settings → API**. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role** key (under "Project API keys") → `SUPABASE_SERVICE_ROLE_KEY`  
   ⚠️ Keep the service role key secret; it bypasses Row Level Security.

## 2. Create the `api_keys` table

In the Supabase **SQL Editor**, run the script:

[`docs/supabase_api_keys.sql`](./supabase_api_keys.sql)

That creates `public.api_keys` with columns: `id`, `name`, `key_hash`, `prefix`, `created_at`.

## 3. Configure the API server

Copy `.env.example` in the project root to `.env` and set:

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

The API loads the root `.env` at startup, so no extra export is needed. Restart the API after editing `.env`. New keys are stored in Supabase; existing keys in `api_keys.json` are not migrated automatically (create new keys via `POST /api-keys` after switching).

## 4. Local development without Supabase

Omit `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. The API will use `certainty_workspace/api_keys.json` so you can develop without a Supabase project.
