import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'
import { isSupabaseConfigured } from '@/lib/supabase/env'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const BACKEND_TIMEOUT_MS = 25_000

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

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS)
    const res = await fetch(`${BACKEND_URL}/api-keys`, {
      headers,
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const data = await res.json().catch(() => ({}))
    if (res.status === 502) {
      return NextResponse.json(
        { detail: 'Backend unavailable (502). The API may be starting up. Try again in a moment.' },
        { status: 502 },
      )
    }
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    const isTimeout = err instanceof Error && err.name === 'AbortError'
    return NextResponse.json(
      {
        detail: isTimeout
          ? 'Backend request timed out. The API may be cold-starting.'
          : err instanceof Error ? err.message : 'Failed to list keys',
      },
      { status: 502 },
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

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS)
    const res = await fetch(`${BACKEND_URL}/api-keys`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ name: body?.name || 'default' }),
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const data = await res.json().catch(() => ({}))
    if (res.status === 502) {
      return NextResponse.json(
        { detail: 'Backend unavailable (502). The API may be starting up. Try again in a moment.' },
        { status: 502 },
      )
    }
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    const isTimeout = err instanceof Error && err.name === 'AbortError'
    return NextResponse.json(
      {
        detail: isTimeout
          ? 'Backend request timed out. The API may be cold-starting.'
          : err instanceof Error ? err.message : 'Failed to create key',
      },
      { status: 502 },
    )
  }
}
