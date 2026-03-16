import { createBrowserClient } from '@supabase/ssr'
import { getSupabaseEnv } from './env'

export function createSupabaseBrowserClient() {
  const config = getSupabaseEnv()
  if (!config) {
    throw new Error(
      'Missing Supabase env vars: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.',
    )
  }

  return createBrowserClient(config.url, config.anonKey)
}
