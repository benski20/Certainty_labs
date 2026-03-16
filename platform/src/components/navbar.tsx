'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X } from 'lucide-react'

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? 'bg-white/80 backdrop-blur-xl border-b border-neutral-200'
            : 'bg-transparent'
        }`}
      >
        <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Certainty Labs
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link
              href="/research"
              className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
            >
              Research
            </Link>
            <Link
              href="/platform/docs"
              className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
            >
              API
            </Link>
            <Link
              href="/platform"
              className="text-sm bg-neutral-900 text-white px-4 py-2 rounded-md hover:bg-neutral-800 transition-colors"
            >
              Platform
            </Link>
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-neutral-600"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </nav>
      </motion.header>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="fixed inset-x-0 top-16 z-40 bg-white border-b border-neutral-200 p-6 md:hidden"
          >
            <div className="flex flex-col gap-4">
              <Link
                href="/research"
                onClick={() => setMobileOpen(false)}
                className="text-sm text-neutral-600"
              >
                Research
              </Link>
              <Link
                href="/platform/docs"
                onClick={() => setMobileOpen(false)}
                className="text-sm text-neutral-600"
              >
                API
              </Link>
              <Link
                href="/platform"
                onClick={() => setMobileOpen(false)}
                className="text-sm bg-neutral-900 text-white px-4 py-2 rounded-md text-center"
              >
                Platform
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
