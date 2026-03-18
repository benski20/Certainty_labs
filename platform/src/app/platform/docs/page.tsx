'use client'

import { useState, useEffect } from 'react'
import { Copy, Check, ChevronRight, ExternalLink } from 'lucide-react'

// ── Types ───────────────────────────────────────────────────────────

interface Param {
  name: string
  type: string
  required?: boolean
  default?: string
  desc: string
}

interface Endpoint {
  method: 'GET' | 'POST' | 'DELETE'
  path: string
  desc: string
  body?: Param[]
  response: string
  curl: string
  python: string
  sdk: string
}

// ── Data ────────────────────────────────────────────────────────────

// Matches SDK fixed URL (users do not configure)
const DEFAULT_API_BASE = 'https://sandboxtesting101--certainty-labs-api.modal.run'
const BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_CERTAINTY_BASE_URL || DEFAULT_API_BASE

const endpoints: Endpoint[] = [
  {
    method: 'GET',
    path: '/health',
    desc: 'Check API availability and version.',
    response: `{ "status": "ok", "version": "0.1.0" }`,
    curl: `curl ${BASE}/health`,
    python: `import requests\nr = requests.get("${BASE}/health")\nprint(r.json())`,
    sdk: `from certaintylabs import Certainty\nclient = Certainty()\nprint(client.health().version)`,
  },
  {
    method: 'POST',
    path: '/train',
    desc: 'Train a TransEBM. Data: built-in GSM8K (omit data), or your EORM JSONL via data or data_path. Match tokenizer_name to your LLM (Qwen/Llama).',
    body: [
      { name: 'data', type: 'object[]', required: false, desc: 'In-memory EORM: [{question, label, gen_text}, ...].' },
      { name: 'data_path', type: 'string', required: false, desc: 'Server path to EORM JSONL (SDK train_from_file for local).' },
      { name: 'tokenizer_name', type: 'string', required: false, default: 'gpt2', desc: 'gpt2, qwen2.5-7b, llama-3.1-8b, or full HF ID.' },
      { name: 'gpu', type: 'string', required: false, desc: 'Runtime GPU: T4, L4, A10, A100, L40S, H100.' },
      { name: 'epochs', type: 'integer', required: false, default: '20', desc: 'Training epochs.' },
      { name: 'batch_size', type: 'integer', required: false, default: '1', desc: 'Batch size.' },
      { name: 'd_model', type: 'integer', required: false, default: '768', desc: 'Transformer hidden size.' },
      { name: 'n_heads', type: 'integer', required: false, default: '4', desc: 'Attention heads.' },
      { name: 'n_layers', type: 'integer', required: false, default: '2', desc: 'Transformer layers.' },
      { name: 'lr', type: 'float', required: false, default: '5e-5', desc: 'Learning rate.' },
      { name: 'max_length', type: 'integer', required: false, default: '2048', desc: 'Max token length.' },
      { name: 'validate_every', type: 'integer', required: false, default: '1', desc: 'Validate every N epochs.' },
      { name: 'val_holdout', type: 'float', required: false, default: '0.2', desc: 'Validation split ratio.' },
    ],
    response: `{ "model_path": "./certainty_workspace/model/ebm_certainty_model.pt", "best_val_acc": 72.5, "epochs_trained": 20, "elapsed_seconds": 145.3 }`,
    curl: `curl -X POST ${BASE}/train -H "Content-Type: application/json" -H "Authorization: Bearer ck_..." -d '{"epochs": 10}'`,
    python: `headers = {"Authorization": "Bearer ck_..."}\nr = requests.post("${BASE}/train", json={"epochs": 10, "gpu": "A10"}, headers=headers).json()`,
    sdk: `r = client.train(epochs=10, gpu="A10")\nr = client.train_with_data(samples, tokenizer_name="qwen2.5-7b", save_to="./my_model")`,
  },
  {
    method: 'POST',
    path: '/rerank',
    desc: 'Generate candidates via LLM (OpenAI or HF) then score and return the best. Or pass pre-generated candidates. Lower energy = better.',
    body: [
      { name: 'candidates', type: 'string[]', required: false, default: '[]', desc: 'Pre-generated texts. Omit to generate via openai_api_key or hf_model+hf_token.' },
      { name: 'prompt', type: 'string', required: false, default: '""', desc: 'Question (required when generating).' },
      { name: 'model_path', type: 'string', required: false, default: '"./certainty_workspace/model/..."', desc: 'Trained .pt model path.' },
      { name: 'tokenizer_path', type: 'string', required: false, desc: 'Tokenizer dir (from training).' },
      { name: 'openai_api_key', type: 'string', required: false, desc: 'OpenAI-compatible: generate n_candidates, then score.' },
      { name: 'openai_model', type: 'string', required: false, default: 'gpt-4o', desc: 'Model name.' },
      { name: 'openai_base_url', type: 'string', required: false, desc: 'OpenAI-compatible base URL.' },
      { name: 'hf_model', type: 'string', required: false, desc: 'HF model (e.g. qwen2.5-7b). Use with hf_token.' },
      { name: 'hf_token', type: 'string', required: false, desc: 'HF API token (required if hf_model).' },
      { name: 'n_candidates', type: 'integer', required: false, default: '5', desc: 'Candidates to generate when using LLM.' },
    ],
    response: `{ "best_candidate": "Best answer.", "best_index": 0, "all_energies": [-1.42, 0.87, 2.31] }`,
    curl: `# Pre-generated\ncurl -X POST ${BASE}/rerank -H "Authorization: Bearer ck_..." -d '{"candidates": ["A","B","C"], "prompt": "What is 2+2?"}'\n# LLM generates then scores\ncurl -X POST ${BASE}/rerank -H "Authorization: Bearer ck_..." -d '{"prompt": "What is 2+2?", "openai_api_key": "sk-...", "n_candidates": 5}'`,
    python: `# Your candidates\nr = requests.post("${BASE}/rerank", json={"candidates": ["A","B","C"]}, headers=headers).json()\n# LLM generates + scores\nr = requests.post("${BASE}/rerank", json={"prompt": q, "openai_api_key": "sk-...", "n_candidates": 5}, headers=headers).json()`,
    sdk: `best = client.rerank(candidates=["A","B","C"], prompt=q)\nbest = client.rerank(prompt=q, openai_api_key="sk-...", n_candidates=5)`,
  },
  {
    method: 'POST',
    path: '/score',
    desc: 'Get EBM energy for outputs (no selection). Lower = higher confidence. Use for logging, audit, A/B.',
    body: [
      { name: 'texts', type: 'string[]', required: true, desc: 'Outputs to score (order preserved).' },
      { name: 'prompt', type: 'string', required: false, default: '""', desc: 'Optional context.' },
      { name: 'model_path', type: 'string', required: false, default: '"./certainty_workspace/model/..."', desc: 'Trained .pt model.' },
      { name: 'tokenizer_path', type: 'string', required: false, desc: 'Tokenizer dir.' },
    ],
    response: `{ "energies": [-1.42, 0.87, 2.31] }`,
    curl: `curl -X POST ${BASE}/score -H "Authorization: Bearer ck_..." -d '{"texts": ["A", "B"], "prompt": "What is 2+2?"}'`,
    python: `r = requests.post("${BASE}/score", json={"texts": [out1, out2], "prompt": q}, headers=headers).json()`,
    sdk: `scores = client.score(texts=[out1, out2], prompt=q)`,
  },
  {
    method: 'POST',
    path: '/pipeline',
    desc: 'Train then optionally rerank. Same params as train + candidates for rerank.',
    body: [
      { name: 'data', type: 'object[]', required: false, desc: 'EORM records.' },
      { name: 'data_path', type: 'string', required: false, desc: 'Path to EORM JSONL.' },
      { name: 'tokenizer_name', type: 'string', required: false, desc: 'gpt2, qwen2.5-7b, llama-3.1-8b.' },
      { name: 'gpu', type: 'string', required: false, desc: 'Runtime GPU (T4, A10, A100, etc.).' },
      { name: 'epochs', type: 'integer', required: false, default: '10', desc: 'Training epochs.' },
      { name: 'batch_size', type: 'integer', required: false, default: '1', desc: 'Batch size.' },
      { name: 'd_model', type: 'integer', required: false, default: '768', desc: 'Hidden size.' },
      { name: 'n_heads', type: 'integer', required: false, default: '4', desc: 'Attention heads.' },
      { name: 'n_layers', type: 'integer', required: false, default: '2', desc: 'Layers.' },
      { name: 'lr', type: 'float', required: false, default: '5e-5', desc: 'Learning rate.' },
      { name: 'max_length', type: 'integer', required: false, default: '2048', desc: 'Max length.' },
      { name: 'validate_every', type: 'integer', required: false, default: '1', desc: 'Validate every N epochs.' },
      { name: 'val_holdout', type: 'float', required: false, default: '0.2', desc: 'Val split.' },
      { name: 'candidates', type: 'string[]', required: false, desc: 'If set, rerank after training.' },
    ],
    response: `{ "train": { "model_path": "...", "best_val_acc": 68, "elapsed_seconds": 82 }, "rerank": { "best_candidate": "..." } or null }`,
    curl: `curl -X POST ${BASE}/pipeline -H "Authorization: Bearer ck_..." -d '{"epochs": 10, "candidates": ["A","B"]}'`,
    python: `r = requests.post("${BASE}/pipeline", json={"epochs": 10, "candidates": ["A","B"]}, headers=headers).json()`,
    sdk: `r = client.pipeline(epochs=10, gpu="A10", candidates=["A","B"], save_to="./model")`,
  },
  {
    method: 'GET',
    path: '/models/download',
    desc: 'Download trained model + tokenizer as zip. Query param: path (server model path from train response).',
    body: [
      { name: 'path', type: 'string', required: true, desc: 'Query param: server path to model.pt (e.g. ./certainty_workspace/model/ebm_certainty_model.pt).' },
    ],
    response: 'Zip file (model.pt, tokenizer/, metrics.json)',
    curl: `curl -o model.zip "${BASE}/models/download?path=./certainty_workspace/model/ebm_certainty_model.pt" -H "Authorization: Bearer ck_..."`,
    python: `r = requests.get(f"${BASE}/models/download?path={model_path}", headers=headers)\nwith open("model.zip", "wb") as f: f.write(r.content)`,
    sdk: `client.download_model(result.model_path, local_dir="./my_model")`,
  },
]

// ── Components ──────────────────────────────────────────────────────

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="relative group">
      <div className="absolute right-2 top-2 z-10">
        <button
          onClick={copy}
          className="p-1.5 rounded bg-neutral-200 text-neutral-500 hover:bg-neutral-300 hover:text-neutral-700 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>
      <pre className="bg-neutral-100 text-neutral-800 rounded-lg p-4 text-[13px] leading-relaxed overflow-x-auto font-mono border border-neutral-200 max-w-full">
        <code className="block min-w-0">{code}</code>
      </pre>
    </div>
  )
}

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    POST: 'bg-blue-50 text-blue-700 border-blue-200',
    DELETE: 'bg-red-50 text-red-700 border-red-200',
  }
  return (
    <span className={`text-xs font-mono font-semibold px-2 py-0.5 rounded border ${colors[method] || 'bg-neutral-100 text-neutral-600 border-neutral-200'}`}>
      {method}
    </span>
  )
}

function ParamTable({ params, method }: { params: Param[]; method?: string }) {
  const label = method === 'GET' ? 'Query Parameters' : 'Request Body'
  return (
    <div className="mt-4">
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">{label}</p>
      <div className="border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-neutral-50/80 border-b border-neutral-200">
              <th className="text-left px-3 py-2 font-medium text-neutral-500 text-xs">Parameter</th>
              <th className="text-left px-3 py-2 font-medium text-neutral-500 text-xs">Type</th>
              <th className="text-left px-3 py-2 font-medium text-neutral-500 text-xs hidden md:table-cell">Default</th>
              <th className="text-left px-3 py-2 font-medium text-neutral-500 text-xs">Description</th>
            </tr>
          </thead>
          <tbody>
            {params.map((p) => (
              <tr key={p.name} className="border-b border-neutral-100 last:border-0">
                <td className="px-3 py-2">
                  <code className="text-[13px] font-mono font-medium">{p.name}</code>
                  {p.required && <span className="text-red-400 ml-0.5 text-xs">*</span>}
                </td>
                <td className="px-3 py-2 text-xs text-neutral-500 font-mono">{p.type}</td>
                <td className="px-3 py-2 text-xs text-neutral-400 font-mono hidden md:table-cell">{p.default || '\u2014'}</td>
                <td className="px-3 py-2 text-xs text-neutral-600">{p.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EndpointCard({ ep, id }: { ep: Endpoint; id: string }) {
  const [tab, setTab] = useState<'curl' | 'python' | 'sdk'>('sdk')

  const codeForTab = tab === 'curl' ? ep.curl : tab === 'python' ? ep.python : ep.sdk
  const langForTab = tab === 'curl' ? 'bash' : 'python'

  return (
    <div id={id} className="scroll-mt-24 border border-neutral-200 rounded-lg overflow-hidden bg-white">
      <div className="px-5 py-4 border-b border-neutral-100">
        <div className="flex items-center gap-3 mb-2">
          <MethodBadge method={ep.method} />
          <code className="text-sm font-mono font-semibold">{ep.path}</code>
        </div>
        <p className="text-sm text-neutral-600 leading-relaxed">{ep.desc}</p>
      </div>

      {ep.body && ep.body.length > 0 && (
        <div className="px-5 py-3 border-b border-neutral-100">
          <ParamTable params={ep.body} method={ep.method} />
        </div>
      )}

      <div className="px-5 py-3 border-b border-neutral-100">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">Response</p>
        <CodeBlock code={ep.response} lang="json" />
      </div>

      <div className="px-5 py-3">
        <div className="flex items-center gap-1 mb-2">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mr-3">Example</p>
          {(['curl', 'python', 'sdk'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`text-xs px-2.5 py-1 rounded transition-colors ${tab === t ? 'bg-neutral-900 text-white' : 'text-neutral-500 hover:bg-neutral-100'}`}
            >
              {t === 'curl' ? 'cURL' : t === 'python' ? 'Python' : 'SDK'}
            </button>
          ))}
        </div>
        <CodeBlock code={codeForTab} lang={langForTab} />
      </div>
    </div>
  )
}

// ── Page ────────────────────────────────────────────────────────────

const onThisPageItems = [
  { id: 'overview', label: 'Overview' },
  { id: 'llm-generate-score', label: 'LLM → Generate → Score' },
  { id: 'authentication', label: 'Auth' },
  { id: 'qwen-llama', label: 'Qwen & Llama' },
  { id: 'verifiable-ai', label: 'Score (confidence)' },
  { id: 'ep-train', label: '/train' },
  { id: 'ep-rerank', label: '/rerank' },
  { id: 'ep-score', label: '/score' },
  { id: 'ep-pipeline', label: '/pipeline' },
  { id: 'ep-models-download', label: '/models/download' },
  { id: 'ep-api-keys', label: 'API Keys' },
  { id: 'data-format', label: 'EORM Format' },
  { id: 'errors', label: 'Errors' },
]

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState('overview')

  useEffect(() => {
    const updateActive = () => {
      const threshold = 120
      for (let i = onThisPageItems.length - 1; i >= 0; i--) {
        const el = document.getElementById(onThisPageItems[i].id)
        if (el && el.getBoundingClientRect().top <= threshold) {
          setActiveSection(onThisPageItems[i].id)
          return
        }
      }
      setActiveSection(onThisPageItems[0].id)
    }
    updateActive()
    window.addEventListener('scroll', updateActive, { passive: true })
    return () => window.removeEventListener('scroll', updateActive)
  }, [])

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header — Tinker-style */}
      <header className="sticky top-0 z-30 flex items-center justify-between h-14 px-6 border-b border-neutral-200 bg-white/95 backdrop-blur">
        <a href="/platform/docs" className="text-lg font-semibold text-neutral-900 tracking-tight">
          Certainty API
        </a>
        <div className="flex items-center gap-4" />
      </header>

      <div className="flex flex-1 w-full max-w-[1400px] mx-auto">
        {/* Center content — wider */}
      <div className="flex-1 min-w-0 max-w-5xl px-10 py-10">
        {/* Starter code — copy-paste ready */}
        <div className="mb-10 p-5 bg-neutral-50 border border-neutral-200 rounded-xl">
          <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">Quick start</p>
          <CodeBlock
            code={`# 1. Create key in Platform → API Keys, then:
export CERTAINTY_API_KEY="ck_..."

# 2. Install & run
pip install certaintylabs

# 3. Python
from certaintylabs import Certainty
client = Certainty()
print(client.health().version)
r = client.train(epochs=5)               # built-in GSM8K
best = client.rerank(["A","B","C"], prompt="What is 2+2?")
print(best.best_candidate)

# Optional: LLM generates candidates, then EBM scores
best = client.rerank(prompt="What is 2+2?", openai_api_key="sk-...", n_candidates=5)`}
            lang="python"
          />
        </div>

        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">API Reference</h1>
          <p className="text-[15px] text-neutral-600 mt-2 leading-relaxed">
            Train TransEBM energy models, score and rerank LLM outputs. API URL is fixed; set <code className="text-[13px] bg-neutral-100 px-1 rounded">CERTAINTY_API_KEY</code> for auth.
          </p>
          <div className="flex items-center gap-4 mt-3 flex-wrap">
            <span className="text-xs text-neutral-500">Version</span>
            <code className="text-xs font-mono bg-neutral-100 text-neutral-700 px-2 py-1 rounded border border-neutral-200">0.2.0</code>
          </div>
        </div>

        {/* Overview */}
        <section id="overview" className="mb-12 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">Overview</h2>
          <p className="text-sm text-neutral-600 leading-relaxed mb-4">
            Train on built-in GSM8K or your EORM data. Rerank candidates or generate via OpenAI/HF. Score outputs for confidence tracking. Data: <code className="text-[12px] bg-neutral-100 px-1 rounded">question</code>, <code className="text-[12px] bg-neutral-100 px-1 rounded">label</code> (0/1), <code className="text-[12px] bg-neutral-100 px-1 rounded">gen_text</code>.
          </p>

          <div className="grid grid-cols-3 gap-3">
            {[
              { n: '1', title: 'Train', desc: 'Built-in GSM8K or your EORM data. Tunable params.' },
              { n: '2', title: 'Rerank', desc: 'Score candidates; pick lowest energy. Generate via OpenAI-compatible or HF (Qwen/Llama) then rerank.' },
              { n: '3', title: 'Score', desc: 'Get energy for any output. Log confidence, audit reliability, interpretable metric (no selection).' },
            ].map((s) => (
              <div key={s.n} className="border border-neutral-200 rounded-lg p-3">
                <span className="text-[10px] font-mono text-neutral-400">{s.n}</span>
                <p className="text-sm font-semibold mt-0.5">{s.title}</p>
                <p className="text-xs text-neutral-500 mt-0.5">{s.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 border border-neutral-200 rounded-lg overflow-hidden">
            <div className="px-4 py-2.5 bg-neutral-50/80 border-b border-neutral-200">
              <p className="text-xs font-medium text-neutral-500">Endpoints</p>
            </div>
            <div className="divide-y divide-neutral-100">
              {endpoints.map((ep) => (
                <a
                  key={ep.path}
                  href={`#ep-${ep.path.slice(1).replace(/\//g, '-')}`}
                  className="flex items-center gap-3 px-4 py-2.5 hover:bg-neutral-50 transition-colors"
                >
                  <MethodBadge method={ep.method} />
                  <code className="text-[13px] font-mono">{ep.path}</code>
                  <span className="text-xs text-neutral-400 ml-auto hidden sm:block truncate max-w-[200px]">
                    {ep.desc.split('.')[0]}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-neutral-300 shrink-0" />
                </a>
              ))}
            </div>
          </div>
        </section>

        {/* LLM Generate + Score */}
        <section id="llm-generate-score" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">LLM → Generate → Score</h2>
          <p className="text-sm text-neutral-600 mb-3">
            <strong>Yes.</strong> <code className="text-[12px] bg-neutral-100 px-1 rounded">POST /rerank</code> can call your LLM to generate candidates, then score them with the trained EBM and return the best. Omit <code className="text-[12px] bg-neutral-100 px-1 rounded">candidates</code> and pass either:
          </p>
          <ul className="text-sm text-neutral-600 list-disc list-inside space-y-1 mb-3">
            <li><code className="text-[12px] bg-neutral-100 px-1 rounded">openai_api_key</code> (+ optional <code className="text-[12px] bg-neutral-100 px-1 rounded">openai_model</code>, <code className="text-[12px] bg-neutral-100 px-1 rounded">openai_base_url</code>)</li>
            <li><code className="text-[12px] bg-neutral-100 px-1 rounded">hf_model</code> + <code className="text-[12px] bg-neutral-100 px-1 rounded">hf_token</code> (Hugging Face Inference)</li>
          </ul>
          <p className="text-sm text-neutral-600">The API generates <code className="text-[12px] bg-neutral-100 px-1 rounded">n_candidates</code> (default 5), scores each with the EBM, and returns the lowest-energy (best) one plus all energies.</p>
          <CodeBlock code={`# SDK: LLM generates 5 candidates, EBM scores them, best returned\nbest = client.rerank(prompt="What is 2+2?", openai_api_key="sk-...", n_candidates=5)`} lang="python" />
        </section>

        {/* Auth */}
        <section id="authentication" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">Authentication</h2>
          <p className="text-sm text-neutral-600 mb-2">Create keys in <strong>Platform → API Keys</strong>. Use <code className="text-[12px] bg-neutral-100 px-1 rounded">Authorization: Bearer ck_...</code>. SDK reads <code className="text-[12px] bg-neutral-100 px-1 rounded">CERTAINTY_API_KEY</code> from env.</p>
        </section>

        <section id="qwen-llama" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">Qwen & Llama</h2>
          <p className="text-sm text-neutral-600 mb-2">Match tokenizer to your LLM: <code className="text-[12px] bg-neutral-100 px-1 rounded">tokenizer_name="qwen2.5-7b"</code> or <code className="text-[12px] bg-neutral-100 px-1 rounded">llama-3.1-8b</code>. Rerank: omit <code className="text-[12px] bg-neutral-100 px-1 rounded">candidates</code>, set <code className="text-[12px] bg-neutral-100 px-1 rounded">hf_model</code>+<code className="text-[12px] bg-neutral-100 px-1 rounded">hf_token</code> or <code className="text-[12px] bg-neutral-100 px-1 rounded">openai_api_key</code>.</p>
        </section>

        {/* Verifiable AI */}
        <section id="verifiable-ai" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">Score (confidence tracking)</h2>
          <p className="text-sm text-neutral-600 mb-2"><code className="text-[12px] bg-neutral-100 px-1 rounded">POST /score</code> — energy per output (no reranking). Lower = higher confidence. Use for logging, audit, A/B.</p>
          <CodeBlock code={`client.score(texts=[out1, out2], prompt=q)  # → ScoreResponse(energies=[...])`} lang="python" />
        </section>

        {/* Endpoints */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold text-neutral-900 mb-6">Endpoints</h2>
          <div className="space-y-6">
            {endpoints.map((ep) => (
              <EndpointCard key={ep.path} ep={ep} id={`ep-${ep.path.slice(1).replace(/\//g, '-')}`} />
            ))}
          </div>
        </section>

        {/* API Keys */}
        <section id="ep-api-keys" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">API Key Management</h2>
          <p className="text-sm text-neutral-600 mb-3">Platform → API Keys. Create, list, revoke. Raw key shown once.</p>
          <div className="space-y-4">
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="POST" /><code className="text-sm font-mono">/api-keys</code>
                <span className="text-xs text-neutral-400">Create key (body: name). Returns id, key (once), prefix, created_at.</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl -X POST ${BASE}/api-keys -H "Content-Type: application/json" -H "Authorization: Bearer ck_..." -d '{"name": "prod"}'`} lang="bash" /></div>
            </div>
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="GET" /><code className="text-sm font-mono">/api-keys</code>
                <span className="text-xs text-neutral-400">List your keys (id, name, prefix, created_at). Requires auth.</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl ${BASE}/api-keys -H "Authorization: Bearer ck_..."`} lang="bash" /></div>
            </div>
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="DELETE" /><code className="text-sm font-mono">/api-keys/{'{key_id}'}</code>
                <span className="text-xs text-neutral-400">Revoke key. Returns deleted, auth_enabled.</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl -X DELETE ${BASE}/api-keys/KEY_ID -H "Authorization: Bearer ck_..."`} lang="bash" /></div>
            </div>
          </div>
        </section>

        {/* Data Format */}
        <section id="data-format" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">EORM Format</h2>
          <p className="text-sm text-neutral-600 mb-2">JSONL: <code className="text-[12px] bg-neutral-100 px-1 rounded">question</code>, <code className="text-[12px] bg-neutral-100 px-1 rounded">label</code> (0/1), <code className="text-[12px] bg-neutral-100 px-1 rounded">gen_text</code>. Or <code className="text-[12px] bg-neutral-100 px-1 rounded">preferred</code>/<code className="text-[12px] bg-neutral-100 px-1 rounded">unpreferred</code>.</p>
          <CodeBlock code={`{"question": "What is 2+2?", "label": 1, "gen_text": "The answer is 4."}`} lang="json" />
        </section>

        {/* Errors */}
        <section id="errors" className="mb-10 scroll-mt-24">
          <h2 className="text-lg font-semibold text-neutral-900 mb-2">Errors</h2>
          <p className="text-sm text-neutral-600 mb-2">JSON body with <code className="text-[13px] bg-neutral-100 px-1 rounded">detail</code>.</p>
          <ul className="text-xs text-neutral-600 space-y-1 list-disc list-inside">
            <li><strong>400</strong> — Empty candidates without openai_api_key/hf_model; bad request body.</li>
            <li><strong>401</strong> — Missing or invalid API key (when auth enabled). Create a key in Platform → API Keys.</li>
            <li><strong>404</strong> — Model file or key id not found.</li>
            <li><strong>422</strong> — Validation error (types, required fields).</li>
            <li><strong>500</strong> — Server error (training, model, or exception).</li>
            <li><strong>502</strong> — Backend unavailable (cold start, timeout). Retry in a moment.</li>
          </ul>
          <CodeBlock code={`{"detail": "Model not found: ..."}`} lang="json" />
        </section>

        {/* Footer */}
        <div className="border-t border-neutral-200 pt-6 pb-12 flex items-center justify-between text-xs text-neutral-500">
          <span>Certainty Labs API v0.2.0</span>
          <a
            href={`${BASE}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-blue-600 transition-colors"
          >
            Swagger UI <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Right sidebar — On This Page */}
      <aside className="hidden xl:block w-52 shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto py-6 px-4 border-l border-neutral-100 bg-neutral-50/30">
        <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-widest mb-3 px-0">
          On This Page
        </p>
        <nav className="space-y-0.5 text-[13px]">
          {onThisPageItems.map(({ id, label }) => (
            <a
              key={id}
              href={`#${id}`}
              className={`block py-1.5 px-0 rounded transition-colors ${
                activeSection === id
                  ? 'text-blue-600 font-medium'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="mt-6 pt-4 border-t border-neutral-200 space-y-2 text-[13px]">
          <a href="mailto:support@certaintylabs.com" className="block text-neutral-500 hover:text-blue-600 transition-colors">
            Question? Give us feedback →
          </a>
          <a href={`${BASE}/docs`} target="_blank" rel="noopener noreferrer" className="block text-neutral-500 hover:text-blue-600 transition-colors">
            View source (Swagger) →
          </a>
        </div>
      </aside>
      </div>
    </div>
  )
}
