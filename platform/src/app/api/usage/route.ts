import { NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'
import { createSupabaseAdminClient } from '@/lib/supabase/admin'
import { isSupabaseConfigured } from '@/lib/supabase/env'

async function getUserId(): Promise<string | null> {
  if (!isSupabaseConfigured()) return null
  const supabase = await createSupabaseServerClient()
  const { data } = await supabase.auth.getUser()
  return data.user?.id ?? null
}

export async function GET(request: Request) {
  try {
    const userId = await getUserId()
    if (!userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const period = searchParams.get('period') ?? undefined
    const periods = searchParams.get('periods') ? parseInt(searchParams.get('periods')!, 10) : undefined

    const admin = createSupabaseAdminClient()

    if (periods && periods > 1) {
      // Last N months for charts
      const monthList: string[] = []
      for (let i = 0; i < periods; i++) {
        const d = new Date()
        d.setMonth(d.getMonth() - i)
        monthList.push(d.toISOString().slice(0, 7))
      }
      const { data, error } = await admin
        .from('user_usage_summary')
        .select('*')
        .eq('user_id', userId)
        .in('period', monthList)
        .order('period', { ascending: true })

      if (error) throw error
      return NextResponse.json({ user_id: userId, periods: data ?? [] })
    }

    const targetPeriod = period ?? new Date().toISOString().slice(0, 7)
    const { data, error } = await admin
      .from('user_usage_summary')
      .select('*')
      .eq('user_id', userId)
      .eq('period', targetPeriod)
      .limit(1)
      .single()

    if (error && error.code !== 'PGRST116') throw error

    const row = data ?? {
      user_id: userId,
      period: targetPeriod,
      total: 0,
      train: 0,
      rerank: 0,
      score: 0,
      pipeline: 0,
      models_download: 0,
    }
    return NextResponse.json({ user_id: userId, period: targetPeriod, ...row })
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Failed to fetch usage' },
      { status: 500 },
    )
  }
}
