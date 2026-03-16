'use client'

export default function UsagePage() {
  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-xl font-semibold mb-1">Usage</h1>
      <p className="text-sm text-neutral-400 mb-8">Current billing period</p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">API calls</p>
          <p className="text-2xl font-semibold">0</p>
        </div>
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Training runs</p>
          <p className="text-2xl font-semibold">0</p>
        </div>
        <div className="p-4 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-1">Rerank calls</p>
          <p className="text-2xl font-semibold">0</p>
        </div>
      </div>

      <div className="border border-neutral-200 rounded-lg p-6">
        <p className="text-xs text-neutral-500 mb-4 font-medium">
          Daily usage (last 30 days)
        </p>
        <div className="flex items-end gap-[3px] h-32">
          {Array.from({ length: 30 }, (_, i) => (
            <div
              key={i}
              className="flex-1 bg-neutral-100 rounded-sm min-h-[2px]"
            />
          ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-neutral-400">
          <span>30d ago</span>
          <span>Today</span>
        </div>
      </div>
    </div>
  )
}
