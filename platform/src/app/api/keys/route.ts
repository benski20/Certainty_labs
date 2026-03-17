import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'
import { createSupabaseAdminClient } from '@/lib/supabase/admin'
import { isSupabaseConfigured } from '@/lib/supabase/env'
import { createHash, randomBytes } from 'crypto'

const KEY_PREFIX = 'ck_'

async function getUserId(): Promise<string | null> {
  if (!isSupabaseConfigured()) return null
  const supabase = await createSupabaseServerClient()
  const { data } = await supabase.auth.getUser()
  return data.user?.id ?? null
}

export async function GET() {
  try {
    const userId = await getUserId()
    if (!userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }

    const admin = createSupabaseAdminClient()
    const { data, error } = await admin
      .from('api_keys')
      .select('id, name, prefix, created_at')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (error) throw error

    const keys = (data ?? []).map((k) => ({
      id: k.id,
      name: k.name,
      prefix: k.prefix,
      created_at: k.created_at,
    }))

    const { count } = await admin.from('api_keys').select('*', { count: 'exact', head: true })
    return NextResponse.json({ keys, auth_enabled: (count ?? 0) > 0 })
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Failed to list keys' },
      { status: 500 },
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const userId = await getUserId()
    if (!userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }

    const body = await request.json().catch(() => ({}))
    const name = body?.name || 'default'

    const raw = KEY_PREFIX + randomBytes(24).toString('hex')
    const keyHash = createHash('sha256').update(raw).digest('hex')
    const id = randomBytes(8).toString('hex')
    const prefix = raw.slice(0, 8)
    const created_at = Date.now() / 1000

    const admin = createSupabaseAdminClient()
    const { error } = await admin.from('api_keys').insert({
      id,
      name,
      key_hash: keyHash,
      prefix,
      created_at,
      user_id: userId,
    })

    if (error) throw error

    return NextResponse.json({
      id,
      name,
      key: raw,
      prefix,
      created_at,
    })
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Failed to create key' },
      { status: 500 },
    )
  }
}
