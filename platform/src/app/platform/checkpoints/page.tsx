'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight, Download } from 'lucide-react'

interface Checkpoint {
  id: string
  name: string
  runId: string
  created: string
  size: string
}

export default function CheckpointsPage() {
  const [checkpoints] = useState<Checkpoint[]>([])

  const total = checkpoints.length
  const range = total > 0 ? `1\u2013${total}` : '0\u20130'

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-start justify-between mb-1">
        <h1 className="text-xl font-semibold">Checkpoints</h1>
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

      {checkpoints.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-sm text-neutral-400">No checkpoints yet.</p>
          <p className="text-xs text-neutral-400 mt-1">
            Checkpoints are saved automatically during training runs.
          </p>
        </div>
      ) : (
        <div className="border border-neutral-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50/80">
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Name
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Run
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Created
                </th>
                <th className="text-left px-4 py-2.5 font-medium text-neutral-500 text-xs">
                  Size
                </th>
                <th className="px-4 py-2.5 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {checkpoints.map((cp) => (
                <tr
                  key={cp.id}
                  className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50/50 transition-colors"
                >
                  <td className="px-4 py-3 font-medium">{cp.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-neutral-500">
                    {cp.runId}
                  </td>
                  <td className="px-4 py-3 text-neutral-500">{cp.created}</td>
                  <td className="px-4 py-3 text-neutral-500">{cp.size}</td>
                  <td className="px-4 py-3">
                    <button className="text-neutral-400 hover:text-neutral-600 transition-colors p-0.5">
                      <Download className="w-3.5 h-3.5" />
                    </button>
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
