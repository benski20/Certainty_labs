# Supabase setup for auth + API key storage

Use **Supabase** for:
- **Platform user authentication** (Supabase Auth)
- **Persistent API key storage** for the FastAPI backend

If you don’t set Supabase env vars for the API, it uses local file storage (`certainty_workspace/api_keys.json`) for development.

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

## 4. Configure platform authentication (Next.js)

Copy `platform/.env.example` to `platform/.env.local` and set:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

Then restart the platform app (`npm run dev` inside `platform`).  
The app now provides `/auth` (sign in / sign up), protects `/platform/*` routes, and supports sign-out from the platform sidebar.

## 5. Local development without Supabase

Omit `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. The API will use `certainty_workspace/api_keys.json` so you can develop without a Supabase project.
