'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Run {
  id: string
  status: 'running' | 'completed' | 'failed'
  created: string
  duration: string
  samples: number
}

const statusStyles: Record<string, string> = {
  running: 'bg-blue-50 text-blue-600',
  completed: 'bg-green-50 text-green-600',
  failed: 'bg-red-50 text-red-600',
}

export default function TrainingRunsPage() {
  const [runs] = useState<Run[]>([])

  const total = runs.length
  const range = total > 0 ? `1\u2013${total}` : '0\u20130'

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-start justify-between mb-1">
        <h1 className="text-xl font-semibold">Training runs</h1>
        <div className="flex items-center gap-3 text-sm text-neutral-500">
          <button className="hover:text-neutral-900 transition-colors disabled:opacity-30" disabled>
            <ChevronLeft className="w-4 h-4 inline" /> Previous
          </button>
          <button className="hover:text-neutral-900 transition-colors disabled:opacity-30" disabled>
            Next <ChevronRight className="w-4 h-4 inline" />
          </button>
        </div>
      </div>
      <p className="text-sm text-neutral-400 mb-6">
        Showing {range} of {total}
      </p>

      {runs.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-sm text-neutral-400">No training runs yet.</p>
          <p className="text-xs text-neutral-400 mt-1">
            Start a training run through the API.
          </p>
        </div>
      ) : (
        <div className="border border-neutral-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50/80">
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Run ID
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Status
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Created
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Duration
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Samples
                </th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs">{run.id}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusStyles[run.status]}`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-500">{run.created}</td>
                  <td className="px-4 py-3 text-neutral-500">{run.duration}</td>
                  <td className="px-4 py-3 text-neutral-500">
                    {run.samples.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
