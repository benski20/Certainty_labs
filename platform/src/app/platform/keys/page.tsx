'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Copy, Eye, EyeOff, Trash2, Check, AlertCircle } from 'lucide-react'
import { api, API_BASE } from '@/lib/api'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { isSupabaseConfigured } from '@/lib/supabase/env'

interface KeyInfo {
  id: string
  name: string
  prefix: string
  created_at: number
}

/** Full key returned once by API after create; we store in state so user can copy before dismissing */
interface NewKeyReveal {
  id: string
  name: string
  key: string
  created_at: number
}

function maskKey(prefix: string) {
  return prefix + '\u2022'.repeat(40)
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<KeyInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKeyReveal, setNewKeyReveal] = useState<NewKeyReveal | null>(null)
  const [visible, setVisible] = useState<Set<string>>(new Set())
  const [copied, setCopied] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null | undefined>(undefined)

  const router = useRouter()

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setUserId(null)
      return
    }
    let cancelled = false
    createSupabaseBrowserClient()
      .auth.getSession()
      .then(({ data }) => {
        if (!cancelled) setUserId(data.session?.user?.id ?? null)
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    // When auth configured, wait for userId (fast from localStorage). Otherwise fetch immediately.
    if (isSupabaseConfigured() && userId === undefined) return
    let cancelled = false
    setLoading(true)
    setError(null)
    api.keys
      .list(userId ?? undefined)
      .then((res) => {
        if (!cancelled) setKeys(res.keys)
      })
      .catch((e) => {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : String(e)
          if (msg.includes('Sign in required')) {
            router.push('/auth?next=/platform/keys')
            return
          }
          const isNetwork = msg === 'Failed to fetch'
          const isProductionUsingLocalhost =
            typeof window !== 'undefined' &&
            !window.location.hostname.includes('localhost') &&
            API_BASE.includes('localhost')
          setError(
            isNetwork && isProductionUsingLocalhost
              ? 'The app is configured to use the local API (localhost). In production, set NEXT_PUBLIC_API_URL to your API URL in Vercel: Project → Settings → Environment Variables. Then redeploy.'
              : isNetwork
                ? `Cannot reach API at ${API_BASE}. Is the server running? (Start with: uvicorn api.main:app --reload)`
                : msg
          )
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [userId])

  const canCreate = !isSupabaseConfigured() || userId != null

  async function createKey() {
    if (!newKeyName.trim() || creating || !canCreate) return
    setCreating(true)
    setError(null)
    try {
      const res = await api.keys.create(newKeyName.trim(), userId ?? undefined)
      setNewKeyReveal({
        id: res.id,
        name: res.name,
        key: res.key,
        created_at: res.created_at,
      })
      setKeys((prev) => [
        { id: res.id, name: res.name, prefix: res.prefix, created_at: res.created_at },
        ...prev,
      ])
      setNewKeyName('')
      setShowCreate(false)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes('Sign in required')) {
        router.push('/auth?next=/platform/keys')
        return
      }
      const isNetwork = msg === 'Failed to fetch'
      const isProductionUsingLocalhost =
        typeof window !== 'undefined' &&
        !window.location.hostname.includes('localhost') &&
        API_BASE.includes('localhost')
      setError(
        isNetwork && isProductionUsingLocalhost
          ? 'The app is configured to use the local API (localhost). In production, set NEXT_PUBLIC_API_URL to your API URL in Vercel: Project → Settings → Environment Variables. Then redeploy.'
          : isNetwork
            ? `Cannot reach API at ${API_BASE}. Is the server running?`
            : msg
      )
    } finally {
      setCreating(false)
    }
  }

  async function deleteKey(id: string) {
    if (deletingId) return
    setDeletingId(id)
    setError(null)
    try {
      await api.keys.delete(id, userId ?? undefined)
      setKeys((prev) => prev.filter((k) => k.id !== id))
      if (newKeyReveal?.id === id) setNewKeyReveal(null)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      if (msg.includes('Sign in required')) {
        router.push('/auth?next=/platform/keys')
        return
      }
      setError(msg)
    } finally {
      setDeletingId(null)
    }
  }

  function toggleVisible(id: string) {
    setVisible((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function copyKey(key: string) {
    navigator.clipboard.writeText(key)
    setCopied(key)
    setTimeout(() => setCopied(null), 1500)
  }

  function formatDate(ts: number) {
    return new Date(ts * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const total = keys.length
  const range = total > 0 ? `1–${total}` : '0–0'

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-start justify-between mb-1">
        <h1 className="text-xl font-semibold">API keys</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-1.5 bg-neutral-900 text-white px-3.5 py-1.5 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Create key
        </button>
      </div>
      <p className="text-sm text-neutral-400 mb-6">
        Keys are stored securely (Supabase or server). Use them with the SDK or <code className="text-xs bg-neutral-100 px-1 rounded">Authorization: Bearer ck_...</code>.
      </p>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-800">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {newKeyReveal && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p className="font-medium mb-1">Key created — copy it now. We won&apos;t show it again.</p>
          <div className="flex items-center gap-2 flex-wrap">
            <code className="font-mono text-xs bg-white px-2 py-1 rounded border border-amber-200 break-all">
              {newKeyReveal.key}
            </code>
            <button
              onClick={() => copyKey(newKeyReveal.key)}
              className="inline-flex items-center gap-1 bg-amber-200 text-amber-900 px-2 py-1 rounded text-xs font-medium hover:bg-amber-300"
            >
              {copied === newKeyReveal.key ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              Copy
            </button>
            <button
              onClick={() => setNewKeyReveal(null)}
              className="text-amber-700 hover:underline text-xs"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {showCreate && (
        <div className="mb-6 p-4 border border-neutral-200 rounded-lg bg-neutral-50">
          <label className="text-sm font-medium block mb-2">Key name</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g. production, development"
              className="flex-1 text-sm border border-neutral-200 rounded-md px-3 py-2 bg-white focus:outline-none focus:border-neutral-400"
              onKeyDown={(e) => e.key === 'Enter' && createKey()}
              autoFocus
              disabled={creating}
            />
            <button
              onClick={() => createKey()}
              disabled={!newKeyName.trim() || creating || !canCreate}
              className="bg-neutral-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-neutral-800 transition-colors disabled:opacity-40"
            >
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button
              onClick={() => {
                setShowCreate(false)
                setNewKeyName('')
              }}
              disabled={creating}
              className="px-4 py-2 rounded-md text-sm text-neutral-500 hover:bg-neutral-100 transition-colors disabled:opacity-40"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-neutral-500 py-8">Loading keys…</p>
      ) : keys.length === 0 && !showCreate ? (
        <div className="py-20 text-center">
          <p className="text-sm text-neutral-400">No API keys yet.</p>
          <p className="text-xs text-neutral-400 mt-1">
            Create a key to use with the SDK or API. It will be saved securely.
          </p>
        </div>
      ) : keys.length > 0 ? (
        <div className="border border-neutral-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50/80">
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">Name</th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">Key</th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">Created</th>
                <th className="px-4 py-2.5 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => {
                const isNewReveal = newKeyReveal?.id === k.id
                const showRaw = isNewReveal && visible.has(k.id)
                const displayKey = isNewReveal && newKeyReveal
                  ? showRaw
                    ? newKeyReveal.key
                    : maskKey(k.prefix)
                  : maskKey(k.prefix)
                const canCopy = isNewReveal && newKeyReveal
                return (
                  <tr key={k.id} className="border-b border-neutral-100 last:border-0">
                    <td className="px-4 py-3 font-medium">{k.name}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs text-neutral-600 break-all">
                          {displayKey}
                        </span>
                        {isNewReveal && (
                          <button
                            onClick={() => toggleVisible(k.id)}
                            className="text-neutral-400 hover:text-neutral-600 p-0.5"
                            title={showRaw ? 'Hide' : 'Show'}
                          >
                            {showRaw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                          </button>
                        )}
                        {canCopy && (
                          <button
                            onClick={() => copyKey(newKeyReveal!.key)}
                            className="text-neutral-400 hover:text-neutral-600 p-0.5"
                            title="Copy key"
                          >
                            {copied === newKeyReveal?.key ? (
                              <Check className="w-3.5 h-3.5 text-green-500" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        )}
                        {!canCopy && (
                          <span className="text-neutral-400 text-xs" title="Full key is only shown once at creation">
                            —
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-neutral-500">{formatDate(k.created_at)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => deleteKey(k.id)}
                        disabled={deletingId !== null}
                        className="text-neutral-300 hover:text-red-500 transition-colors p-0.5 disabled:opacity-50"
                        title="Revoke key"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
