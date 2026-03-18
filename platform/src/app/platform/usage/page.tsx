'use client'

import { useEffect, useState } from 'react'

interface UsageSummary {
  user_id: string
  period: string
  total: number
  train: number
  rerank: number
  score: number
  pipeline: number
  models_download: number
}

export default function UsagePage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [periods, setPeriods] = useState<UsageSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchUsage() {
      try {
        const [currentRes, historyRes] = await Promise.all([
          fetch('/api/usage'),
          fetch('/api/usage?periods=6'),
        ])
        if (!currentRes.ok) {
          if (currentRes.status === 401) {
            setSummary(null)
            setLoading(false)
            return
          }
          throw new Error(await currentRes.text())
        }
        const current = await currentRes.json()
        setSummary(current)
        if (historyRes.ok) {
          const history = await historyRes.json()
          setPeriods(history.periods ?? [])
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load usage')
      } finally {
        setLoading(false)
      }
    }
    fetchUsage()
  }, [])

  if (loading) {
    return (
      <div className="p-8 max-w-4xl">
        <h1 className="text-xl font-semibold mb-1">Usage</h1>
        <p className="text-sm text-neutral-400">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 max-w-4xl">
        <h1 className="text-xl font-semibold mb-1">Usage</h1>
        <p className="text-sm text-red-500">{error}</p>
      </div>
    )
  }

  const s = summary ?? {
    total: 0,
    train: 0,
    rerank: 0,
    score: 0,
    pipeline: 0,
    models_download: 0,
    period: new Date().toISOString().slice(0, 7),
  }
  const maxBar = Math.max(...periods.map((p) => p.total), 1)

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-xl font-semibold mb-1">Usage</h1>
      <p className="text-sm text-neutral-400 mb-8">
        {s.period ? `Period ${s.period}` : 'Current billing period'}
      </p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Total API calls</p>
          <p className="text-2xl font-semibold">{s.total}</p>
        </div>
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Training runs</p>
          <p className="text-2xl font-semibold">{s.train}</p>
        </div>
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Rerank calls</p>
          <p className="text-2xl font-semibold">{s.rerank}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Score calls</p>
          <p className="text-2xl font-semibold">{s.score}</p>
        </div>
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Pipeline runs</p>
          <p className="text-2xl font-semibold">{s.pipeline}</p>
        </div>
      </div>

      <div className="border border-neutral-200 rounded-lg p-6">
        <p className="text-xs text-neutral-500 mb-4 font-medium">
          Monthly usage (last 6 months)
        </p>
        <div className="flex items-end gap-[3px] h-32">
          {periods.length > 0
            ? periods.map((p) => (
                <div
                  key={p.period}
                  className="flex-1 bg-neutral-200 rounded-sm min-h-[2px] transition-all"
                  style={{
                    height: `${Math.max(2, (p.total / maxBar) * 100)}%`,
                  }}
                  title={`${p.period}: ${p.total} calls`}
                />
              ))
            : Array.from({ length: 6 }, (_, i) => (
                <div
                  key={i}
                  className="flex-1 bg-neutral-100 rounded-sm min-h-[2px]"
                />
              ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-neutral-400">
          <span>{periods[0]?.period ?? '6mo ago'}</span>
          <span>{periods[periods.length - 1]?.period ?? 'This month'}</span>
        </div>
      </div>
    </div>
  )
}
