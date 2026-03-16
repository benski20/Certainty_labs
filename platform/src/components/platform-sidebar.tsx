'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  Key,
  Activity,
  FileText,
  BarChart3,
  CreditCard,
  BookOpen,
  LogOut,
} from 'lucide-react'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { isSupabaseConfigured } from '@/lib/supabase/env'

const navigation = [
  { name: 'API docs', href: '/platform/docs', icon: BookOpen },
  { name: 'API keys', href: '/platform/keys', icon: Key },
  { name: 'Training runs', href: '/platform/runs', icon: Activity },
  { name: 'Checkpoints', href: '/platform/checkpoints', icon: FileText },
  { name: 'Usage', href: '/platform/usage', icon: BarChart3 },
  { name: 'Billing', href: '/platform/billing', icon: CreditCard },
]

export function PlatformSidebar() {
  const pathname = usePathname()
  const [email, setEmail] = useState('user@example.com')
  const [loadingUser, setLoadingUser] = useState(false)
  const authEnabled = isSupabaseConfigured()

  useEffect(() => {
    if (!authEnabled) return
    let cancelled = false
    const supabase = createSupabaseBrowserClient()
    setLoadingUser(true)

    supabase.auth
      .getUser()
      .then(({ data }) => {
        if (!cancelled && data.user?.email) {
          setEmail(data.user.email)
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingUser(false)
      })

    return () => {
      cancelled = true
    }
  }, [authEnabled])

  async function signOut() {
    if (!authEnabled) return
    const supabase = createSupabaseBrowserClient()
    await supabase.auth.signOut()
    window.location.href = '/auth'
  }

  const initial = email?.[0]?.toUpperCase() || 'U'

  return (
    <aside className="w-52 shrink-0 border-r border-neutral-200 bg-white flex flex-col min-h-screen">
      <div className="px-4 py-5">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-neutral-900 rounded-lg flex items-center justify-center">
            <span className="text-white text-xs font-bold">C</span>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-2 space-y-0.5">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-[13px] transition-colors ${
                isActive
                  ? 'bg-neutral-100 text-neutral-900 font-medium'
                  : 'text-neutral-500 hover:bg-neutral-50 hover:text-neutral-900'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-neutral-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-neutral-200 rounded-full flex items-center justify-center text-[10px] font-semibold text-neutral-600">
            {initial}
          </div>
          <div className="overflow-hidden">
            <p className="text-[13px] font-medium text-neutral-900 truncate leading-tight">
              {loadingUser ? 'Loading...' : 'User'}
            </p>
            <p className="text-[11px] text-neutral-400 truncate leading-tight">
              {email}
            </p>
          </div>
        </div>
        {authEnabled && (
          <button
            onClick={signOut}
            className="mt-3 w-full inline-flex items-center justify-center gap-1.5 rounded-md border border-neutral-200 px-2 py-1.5 text-[12px] text-neutral-600 hover:text-neutral-900 hover:border-neutral-300 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
        )}
      </div>
    </aside>
  )
}
