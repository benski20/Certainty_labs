import Link from 'next/link'
import { isSupabaseConfigured } from '@/lib/supabase/env'
import { AuthForm } from './auth-form'

export default async function AuthPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>
}) {
  const params = await searchParams
  const next = params?.next || '/platform'
  const configured = isSupabaseConfigured()

  return (
    <main className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <div className="mb-5">
          <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-800">
            {'<-'} Back to home
          </Link>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">Sign in to Certainty Labs</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Use your account to access the platform dashboard.
          </p>
        </div>

        {configured ? (
          <AuthForm nextPath={next} />
        ) : (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `platform/.env.local`
            to enable auth.
          </div>
        )}
      </div>
    </main>
  )
}
