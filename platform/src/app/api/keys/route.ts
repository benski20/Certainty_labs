import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'
import { isSupabaseConfigured } from '@/lib/supabase/env'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getUserId(): Promise<string | null> {
  if (!isSupabaseConfigured()) return null
  const supabase = await createSupabaseServerClient()
  const { data } = await supabase.auth.getUser()
  return data.user?.id ?? null
}

export async function GET(request: NextRequest) {
  try {
    const userId = await getUserId()
    if (isSupabaseConfigured() && !userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (userId) headers['X-User-ID'] = userId

    const res = await fetch(`${BACKEND_URL}/api-keys`, { headers })
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
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
    if (isSupabaseConfigured() && !userId) {
      return NextResponse.json({ detail: 'Sign in required' }, { status: 401 })
    }
    const body = await request.json().catch(() => ({}))
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (userId) headers['X-User-ID'] = userId

    const res = await fetch(`${BACKEND_URL}/api-keys`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ name: body?.name || 'default' }),
    })
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : 'Failed to create key' },
      { status: 500 },
    )
  }
}
