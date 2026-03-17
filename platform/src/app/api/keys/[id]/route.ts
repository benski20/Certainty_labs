import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'
import { createSupabaseAdminClient } from '@/lib/supabase/admin'
import { isSupabaseConfigured } from '@/lib/supabase/env'

async function getUserId(): Promise<string | null> {
  if (!isSupabaseConfigured()) return null
  const supabase = await createSupabaseServerClient()
  const { data } = await supabase.auth.getUser()
  return data.user?.id ?? null
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const userId = await getUserId()
    if (!userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }

    const { id } = await params
    const admin = createSupabaseAdminClient()
    const { data, error } = await admin
      .from('api_keys')
      .delete()
      .eq('id', id)
      .eq('user_id', userId)
      .select('id')

    if (error || !data || data.length === 0) {
      return NextResponse.json({ detail: `Key '${id}' not found.` }, { status: 404 })
    }

    const { count } = await admin.from('api_keys').select('*', { count: 'exact', head: true })
    return NextResponse.json({ deleted: id, auth_enabled: (count ?? 0) > 0 })
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Failed to delete key' },
      { status: 500 },
    )
  }
}
