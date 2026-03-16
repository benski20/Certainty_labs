import Link from 'next/link'

export function Footer() {
  return (
    <footer className="border-t border-neutral-200">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row justify-between gap-8">
          <div>
            <p className="text-lg font-semibold tracking-tight">
              Certainty Labs
            </p>
            <p className="text-sm text-neutral-500 mt-1">
              Constraint-guaranteed outputs for production AI.
            </p>
          </div>
          <div className="flex gap-12">
            <div>
              <p className="text-sm font-medium mb-3">Platform</p>
              <div className="flex flex-col gap-2">
                <Link
                  href="/platform/docs"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  API Docs
                </Link>
                <Link
                  href="/platform/keys"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  API Keys
                </Link>
                <Link
                  href="/platform/runs"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  Training Runs
                </Link>
                <Link
                  href="/platform/checkpoints"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  Checkpoints
                </Link>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-3">Research</p>
              <div className="flex flex-col gap-2">
                <Link
                  href="/research"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  Papers
                </Link>
                <a
                  href="https://arxiv.org/abs/2505.14999"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
                >
                  EORM
                </a>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-12 pt-6 border-t border-neutral-100">
          <p className="text-xs text-neutral-400">
            &copy; 2026 Certainty Labs. MIT License.
          </p>
        </div>
      </div>
    </footer>
  )
}
