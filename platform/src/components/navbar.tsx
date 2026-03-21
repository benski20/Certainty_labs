'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const navLinks = [
  { href: '/research', label: 'Research' },
  { href: '/platform/docs', label: 'API' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className={cn(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
          scrolled
            ? 'bg-white/60 backdrop-blur-md border-b border-neutral-200/50'
            : 'bg-transparent',
        )}
      >
        <nav className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link
            href="/"
            className={cn(
              'font-mono text-sm font-medium tracking-tight transition-colors',
              scrolled ? 'text-neutral-900' : 'text-neutral-800',
            )}
          >
            {'{'} Certainty Labs {'}'}
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'relative px-3 py-2 text-[13px] font-medium transition-colors rounded-md',
                  scrolled
                    ? 'text-neutral-500 hover:text-neutral-900'
                    : 'text-neutral-600 hover:text-neutral-900',
                )}
              >
                {link.label}
              </Link>
            ))}
            <div
              className={cn(
                'mx-2 h-4 w-px',
                scrolled ? 'bg-neutral-300' : 'bg-neutral-200',
              )}
            />
            <Link
              href="/auth?next=/platform"
              className={cn(
                'px-3 py-2 text-[13px] font-medium transition-colors rounded-md',
                scrolled
                  ? 'text-neutral-500 hover:text-neutral-900'
                  : 'text-neutral-600 hover:text-neutral-900',
              )}
            >
              Sign in
            </Link>
            <Link
              href="/platform"
              className={cn(
                'ml-2 inline-flex items-center gap-1.5 px-4 py-2 text-[13px] font-medium rounded-md transition-all',
                scrolled
                  ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                  : 'bg-neutral-900 text-white hover:bg-neutral-800 border border-neutral-800',
              )}
            >
              Platform
              <ChevronRight className="w-3.5 h-3.5" strokeWidth={2.5} />
            </Link>
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className={cn(
              'md:hidden p-2 rounded-md transition-colors',
                scrolled
                ? 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100'
                : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100',
            )}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </nav>
      </motion.header>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="fixed inset-x-0 top-14 z-40 md:hidden overflow-hidden"
          >
            <div
              className={cn(
                'border-b bg-white/80 backdrop-blur-md border-neutral-200/50',
                'px-6 py-4 flex flex-col gap-1',
              )}
            >
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-3 py-2.5 text-sm font-medium text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-md transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <div className="my-2 h-px bg-neutral-200" />
              <Link
                href="/auth?next=/platform"
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 text-sm font-medium text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-md transition-colors"
              >
                Sign in
              </Link>
              <Link
                href="/platform"
                onClick={() => setMobileOpen(false)}
                className="mt-2 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium bg-neutral-900 text-white rounded-md hover:bg-neutral-800 transition-colors"
              >
                Platform
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
