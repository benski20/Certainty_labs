'use client'

export default function BillingPage() {
  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-xl font-semibold mb-1">Billing</h1>
      <p className="text-sm text-neutral-400 mb-8">
        Manage your plan and payment method.
      </p>

      <div className="space-y-6">
        <div className="p-5 border border-neutral-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-neutral-500 mb-1">Current plan</p>
              <p className="text-lg font-semibold">Free</p>
              <p className="text-sm text-neutral-500 mt-0.5">
                1,000 API calls per month
              </p>
            </div>
            <button className="text-sm font-medium text-neutral-900 border border-neutral-200 px-4 py-2 rounded-md hover:bg-neutral-50 transition-colors">
              Upgrade
            </button>
          </div>
        </div>

        <div className="p-5 border border-neutral-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-neutral-500 mb-1">Payment method</p>
              <p className="text-sm text-neutral-500">No payment method on file.</p>
            </div>
            <button className="text-sm font-medium text-neutral-900 border border-neutral-200 px-4 py-2 rounded-md hover:bg-neutral-50 transition-colors">
              Add
            </button>
          </div>
        </div>

        <div className="p-5 border border-neutral-200 rounded-lg">
          <p className="text-xs text-neutral-500 mb-3">This period</p>
          <div className="flex items-baseline justify-between">
            <p className="text-2xl font-semibold">$0.00</p>
            <p className="text-xs text-neutral-400">
              Resets {new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
