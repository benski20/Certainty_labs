'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Key,
  Activity,
  FileText,
  BarChart3,
  CreditCard,
  BookOpen,
} from 'lucide-react'

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
            U
          </div>
          <div className="overflow-hidden">
            <p className="text-[13px] font-medium text-neutral-900 truncate leading-tight">
              User
            </p>
            <p className="text-[11px] text-neutral-400 truncate leading-tight">
              user@example.com
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}
