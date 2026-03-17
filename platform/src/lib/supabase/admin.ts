import { createClient } from '@supabase/supabase-js'

/** Server-only client with service role for api_keys table. Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY. */
export function createSupabaseAdminClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY required for api_keys. Set in .env.local.')
  }
  return createClient(url, key)
}
