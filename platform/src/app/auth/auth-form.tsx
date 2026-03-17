'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'

const AUTH_TIMEOUT_MS = 15000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Request timed out. If using Supabase free tier, your project may be paused—try again in a minute.')), ms),
    ),
  ])
}

export function AuthForm({ nextPath }: { nextPath: string }) {
  const router = useRouter()
  const [mode, setMode] = useState<'sign-in' | 'sign-up'>('sign-in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (loading) return

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const supabase = createSupabaseBrowserClient()

      if (mode === 'sign-in') {
        const { error: signInError } = await withTimeout(
          supabase.auth.signInWithPassword({
            email: email.trim(),
            password,
          }),
          AUTH_TIMEOUT_MS,
        )
        if (signInError) throw signInError
        setLoading(false)
        router.push(nextPath || '/platform')
        router.refresh()
        return
      }

      const emailRedirectTo =
        typeof window === 'undefined'
          ? undefined
          : `${window.location.origin}/auth/callback?next=${encodeURIComponent(nextPath)}`

      const { error: signUpError } = await withTimeout(
        supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { emailRedirectTo },
        }),
        AUTH_TIMEOUT_MS,
      )
      if (signUpError) throw signUpError

      setSuccess('Account created. Check your email to confirm, then sign in.')
      setMode('sign-in')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="flex rounded-md bg-neutral-100 p-1 text-sm">
        <button
          type="button"
          onClick={() => setMode('sign-in')}
          className={`flex-1 rounded px-3 py-1.5 transition-colors ${
            mode === 'sign-in' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
          }`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => setMode('sign-up')}
          className={`flex-1 rounded px-3 py-1.5 transition-colors ${
            mode === 'sign-up' ? 'bg-white shadow-sm text-neutral-900' : 'text-neutral-500'
          }`}
        >
          Sign up
        </button>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm focus:outline-none focus:border-neutral-400"
          placeholder="you@company.com"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm focus:outline-none focus:border-neutral-400"
          placeholder="At least 8 characters"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-green-700">{success}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
      >
        {loading ? 'Please wait...' : mode === 'sign-in' ? 'Sign in' : 'Create account'}
      </button>
    </form>
  )
}
