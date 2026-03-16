'use client'

import { useState, useEffect } from 'react'
import { Copy, Check, ChevronRight, ExternalLink, Search } from 'lucide-react'

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

const DEFAULT_API_BASE = 'https://certainty-labs.onrender.com'
const BASE = process.env.NEXT_PUBLIC_CERTAINTY_BASE_URL || DEFAULT_API_BASE

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
    desc: 'Train a TransEBM. Data: built-in GSM8K (omit data), or your EORM JSONL via data or data_path. Use tokenizer_name for Qwen/Llama compatibility so the EBM matches your LLM tokenization.',
    body: [
      { name: 'data', type: 'object[]', required: false, desc: 'In-memory EORM records: [{question, label, gen_text}, ...].' },
      { name: 'data_path', type: 'string', required: false, desc: 'Server path to EORM JSONL (or use SDK train_from_file for local).' },
      { name: 'tokenizer_name', type: 'string', required: false, desc: 'HuggingFace tokenizer: gpt2 (default), or alias/full ID for Qwen/Llama (e.g. qwen2.5-7b, llama-3.1-8b, Qwen/Qwen2.5-7B-Instruct).' },
      { name: 'epochs', type: 'integer', required: false, default: '20', desc: 'Training epochs.' },
      { name: 'd_model', type: 'integer', required: false, default: '768', desc: 'Transformer hidden size.' },
      { name: 'lr', type: 'float', required: false, default: '5e-5', desc: 'Learning rate.' },
    ],
    response: `{ "model_path": "./certainty_workspace/model/ebm_certainty_model.pt", "best_val_acc": 72.5, "epochs_trained": 20, "elapsed_seconds": 145.3 }`,
    curl: `curl -X POST ${BASE}/train -H "Content-Type: application/json" -d '{"epochs": 10}'`,
    python: `# Built-in (default gpt2 tokenizer)\ndefault = requests.post("${BASE}/train", json={"epochs": 10}).json()\n# Qwen/Llama: match tokenizer to your LLM\nr = requests.post("${BASE}/train", json={"data": records, "tokenizer_name": "qwen2.5-7b", "epochs": 15})`,
    sdk: `result = client.train(epochs=10)\nresult = client.train(tokenizer_name="qwen2.5-7b", epochs=10)\nresult = client.train_with_data(samples, tokenizer_name="llama-3.1-8b")\nresult = client.train_from_file("data.jsonl")`,
  },
  {
    method: 'POST',
    path: '/rerank',
    desc: 'Score candidates with the trained TransEBM; returns the lowest-energy (best) one. Pass candidates, or omit and generate via openai_api_key (OpenAI-compatible) or hf_model + hf_token (Hugging Face Inference for Qwen/Llama).',
    body: [
      { name: 'candidates', type: 'string[]', required: false, default: '[]', desc: 'Pre-generated candidate texts. Omit to generate via openai_api_key or hf_model + hf_token.' },
      { name: 'prompt', type: 'string', required: false, default: '""', desc: 'Question/prompt (required when generating candidates).' },
      { name: 'model_path', type: 'string', required: false, default: '"./certainty_workspace/model/..."', desc: 'Path to trained .pt model.' },
      { name: 'tokenizer_path', type: 'string', required: false, desc: 'Path to tokenizer saved with the model (from training).' },
      { name: 'openai_api_key', type: 'string', required: false, desc: 'OpenAI-compatible: generate n_candidates then rerank.' },
      { name: 'openai_model', type: 'string', required: false, desc: 'Model name (e.g. gpt-4o-mini).' },
      { name: 'openai_base_url', type: 'string', required: false, desc: 'OpenAI-compatible API base URL.' },
      { name: 'hf_model', type: 'string', required: false, desc: 'Hugging Face model ID or alias (e.g. qwen2.5-7b, Qwen/Qwen2.5-7B-Instruct). Use with hf_token.' },
      { name: 'hf_token', type: 'string', required: false, desc: 'Hugging Face API token for Inference API (required if hf_model set).' },
      { name: 'n_candidates', type: 'integer', required: false, default: '5', desc: 'Number of candidates when generating (openai or HF).' },
    ],
    response: `{ "best_candidate": "Best answer text.", "best_index": 0, "all_energies": [-1.42, 0.87, 2.31] }`,
    curl: `# Your candidates\ncurl -X POST ${BASE}/rerank -H "Content-Type: application/json" -d '{"candidates": ["A", "B", "C"], "prompt": "What is 2+2?"}'\n# OpenAI-compatible LLM\ncurl -X POST ${BASE}/rerank -d '{"prompt": "What is 2+2?", "openai_api_key": "sk-...", "n_candidates": 5}'\n# Hugging Face (Qwen/Llama)\ncurl -X POST ${BASE}/rerank -d '{"prompt": "What is 2+2?", "hf_model": "qwen2.5-7b", "hf_token": "hf_...", "n_candidates": 5}'`,
    python: `# Pre-generated\nr = requests.post("${BASE}/rerank", json={"candidates": ["A","B","C"], "prompt": q}).json()\n# OpenAI-compatible\nr = requests.post("${BASE}/rerank", json={"prompt": q, "openai_api_key": "sk-...", "n_candidates": 5}).json()\n# Hugging Face Qwen/Llama\nr = requests.post("${BASE}/rerank", json={"prompt": q, "hf_model": "qwen2.5-7b", "hf_token": "hf_...", "n_candidates": 5}).json()\nprint(r["best_candidate"])`,
    sdk: `best = client.rerank(candidates=["A","B","C"], prompt=q)\nbest = client.rerank(prompt=q, openai_api_key="sk-...", n_candidates=5)\nbest = client.rerank(prompt=q, hf_model="qwen2.5-7b", hf_token="hf_...", n_candidates=5)\nprint(best.best_candidate)`,
  },
  {
    method: 'POST',
    path: '/score',
    desc: 'Get EBM energy scores for one or more outputs (no reranking). Use for verifiable/interpretable AI: log confidence, audit reliability, track scores over time. Lower energy = higher confidence.',
    body: [
      { name: 'texts', type: 'string[]', required: true, desc: 'One or more outputs to score (order preserved in response).' },
      { name: 'prompt', type: 'string', required: false, default: '""', desc: 'Optional context/prompt (prepended when scoring).' },
      { name: 'model_path', type: 'string', required: false, default: '"./certainty_workspace/model/..."', desc: 'Path to trained .pt model.' },
      { name: 'tokenizer_path', type: 'string', required: false, desc: 'Path to tokenizer saved with the model.' },
    ],
    response: `{ "energies": [-1.42, 0.87, 2.31] }`,
    curl: `curl -X POST ${BASE}/score -H "Content-Type: application/json" -d '{"texts": ["Output A", "Output B"], "prompt": "What is 2+2?"}'`,
    python: `r = requests.post("${BASE}/score", json={"texts": [out1, out2], "prompt": q}).json()\nprint(r["energies"])  # log, audit, track confidence`,
    sdk: `scores = client.score(texts=[out1, out2], prompt=q)\nprint(scores.energies)  # lower = higher confidence`,
  },
  {
    method: 'POST',
    path: '/pipeline',
    desc: 'One call: train (on your data or built-in) then optionally rerank. Supports tokenizer_name for Qwen/Llama. Pass candidates to rerank after training.',
    body: [
      { name: 'data', type: 'object[]', required: false, desc: 'In-memory EORM records.' },
      { name: 'data_path', type: 'string', required: false, desc: 'Server path to EORM JSONL.' },
      { name: 'tokenizer_name', type: 'string', required: false, desc: 'Tokenizer for training (gpt2, qwen2.5-7b, llama-3.1-8b, or full HF ID).' },
      { name: 'epochs', type: 'integer', required: false, default: '10', desc: 'Training epochs.' },
      { name: 'candidates', type: 'string[]', required: false, desc: 'If set, rerank these after training.' },
    ],
    response: `{ "train": { "model_path": "...", "best_val_acc": 68, "elapsed_seconds": 82 }, "rerank": { "best_candidate": "..." } or null }`,
    curl: `curl -X POST ${BASE}/pipeline -H "Content-Type: application/json" -d '{"epochs": 10}'`,
    python: `r = requests.post("${BASE}/pipeline", json={"epochs": 10, "tokenizer_name": "qwen2.5-7b"}).json()\nprint(r["train"]["best_val_acc"])`,
    sdk: `result = client.pipeline(epochs=10, tokenizer_name="llama-3.1-8b", candidates=["A", "B"])\nprint(result.train.best_val_acc)`,
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
      <pre className="bg-neutral-100 text-neutral-800 rounded-lg p-4 text-[13px] leading-relaxed overflow-x-auto font-mono border border-neutral-200">
        <code>
          {lang && <span className="text-neutral-500 text-[11px] block mb-2">{lang}</span>}
          {code}
        </code>
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

function ParamTable({ params }: { params: Param[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">Request Body</p>
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
  const [tab, setTab] = useState<'curl' | 'python' | 'sdk'>('curl')

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
          <ParamTable params={ep.body} />
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

const navItems = [
  { id: 'overview', label: 'Overview' },
  { id: 'qwen-llama', label: 'Qwen & Llama' },
  { id: 'authentication', label: 'Authentication' },
  { id: 'quickstart', label: 'Quickstart' },
  { id: 'sdk', label: 'Python SDK' },
  { id: 'ep-health', label: '/health' },
  { id: 'ep-train', label: '/train' },
  { id: 'ep-rerank', label: '/rerank' },
  { id: 'ep-score', label: '/score' },
  { id: 'ep-pipeline', label: '/pipeline' },
  { id: 'ep-api-keys', label: '/api-keys' },
  { id: 'data-format', label: 'Data Format' },
  { id: 'data-external', label: 'Generating Data Externally' },
  { id: 'errors', label: 'Errors' },
]

const onThisPageItems = [
  { id: 'overview', label: 'Overview' },
  { id: 'qwen-llama', label: 'Qwen & Llama' },
  { id: 'authentication', label: 'Authentication' },
  { id: 'quickstart', label: 'Quickstart' },
  { id: 'sdk', label: 'Python SDK' },
  { id: 'verifiable-ai', label: 'Verifiable & interpretable AI' },
  { id: 'ep-train', label: '/train' },
  { id: 'ep-rerank', label: '/rerank' },
  { id: 'ep-score', label: '/score' },
  { id: 'ep-pipeline', label: '/pipeline' },
  { id: 'ep-api-keys', label: 'API Key Management' },
  { id: 'data-format', label: 'EORM Data Format' },
  { id: 'data-external', label: 'Generating Data Externally' },
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

      <div className="flex flex-1">
        {/* Left sidebar — hierarchical nav */}
        <nav className="hidden lg:block w-56 shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto border-r border-neutral-100 py-6 px-4 bg-neutral-50/30">
          <p className="text-[11px] font-semibold text-neutral-400 uppercase tracking-widest mb-3 px-2">
            API Reference
          </p>
          <ul className="space-y-0.5 text-sm">
            {navItems.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className={`block py-2 px-2 rounded-md transition-colors ${
                    item.id.startsWith('ep-')
                      ? 'font-mono text-[13px] text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100'
                      : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100'
                  }`}
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
          <div className="mt-6 pt-4 border-t border-neutral-200">
            <a
              href={`${BASE}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[13px] text-neutral-500 hover:text-blue-600 transition-colors px-2"
            >
              Swagger UI
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </nav>

        {/* Center content */}
      <div className="flex-1 min-w-0 max-w-3xl px-8 py-10">
        {/* Page title */}
        <div className="mb-10">
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">API Reference</h1>
          <p className="text-[15px] text-neutral-600 mt-2 leading-relaxed">
            Train TransEBM scorers, bring your own data or LLM, and rerank LLM outputs for constraint-correct answers.
          </p>
          <div className="flex items-center gap-4 mt-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-500">Base URL</span>
              <code className="text-xs font-mono bg-neutral-100 text-neutral-700 px-2 py-1 rounded border border-neutral-200">{BASE}</code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-500">Version</span>
              <code className="text-xs font-mono bg-neutral-100 text-neutral-700 px-2 py-1 rounded border border-neutral-200">0.1.0</code>
            </div>
          </div>
        </div>

        {/* Overview */}
        <section id="overview" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Overview</h2>
          <div className="text-sm text-neutral-600 leading-relaxed space-y-3">
            <p>
              Certainty trains TransEBM energy models that score LLM outputs (lower energy = more likely correct).
              Use <strong>your own data</strong> (in-memory or JSONL) or the <strong>built-in GSM8K</strong> dataset; <strong>tune training</strong> (epochs, d_model, lr, etc.); use <strong>your own LLM</strong> in rerank to generate candidates (OpenAI-compatible or <strong>Hugging Face Qwen/Llama</strong>).
            </p>
            <p>
              You provide EORM-format training data (question, label 0/1, gen_text). Generate it externally if needed (see &quot;Generating Data Externally&quot; below).
            </p>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-3">
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
                  href={`#ep-${ep.path.slice(1)}`}
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

        {/* Qwen & Llama compatibility */}
        <section id="qwen-llama" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Qwen & Llama (Hugging Face)</h2>
          <p className="text-[15px] text-neutral-600 leading-relaxed mb-3">
            For best results when your candidates come from <strong>Qwen</strong> or <strong>Llama</strong> (on Hugging Face), use the same tokenizer in training so the EBM tokenization matches your LLM.
          </p>
          <ul className="text-sm text-neutral-600 space-y-1.5 list-disc list-inside mb-4">
            <li><strong>Training:</strong> Set <code className="text-[13px] bg-neutral-100 px-1 rounded">tokenizer_name</code> on <code className="text-[13px] bg-neutral-100 px-1 rounded">POST /train</code> or <code className="text-[13px] bg-neutral-100 px-1 rounded">/pipeline</code>. Use an alias (e.g. <code className="text-[13px] bg-neutral-100 px-1 rounded">qwen2.5-7b</code>, <code className="text-[13px] bg-neutral-100 px-1 rounded">llama-3.1-8b</code>) or a full Hugging Face ID. Default is <code className="text-[13px] bg-neutral-100 px-1 rounded">gpt2</code>.</li>
            <li><strong>Rerank (generate candidates):</strong> Omit <code className="text-[13px] bg-neutral-100 px-1 rounded">candidates</code> and set either <strong>OpenAI-compatible</strong> (<code className="text-[13px] bg-neutral-100 px-1 rounded">openai_api_key</code>, etc.) or <strong>Hugging Face</strong> (<code className="text-[13px] bg-neutral-100 px-1 rounded">hf_model</code> + <code className="text-[13px] bg-neutral-100 px-1 rounded">hf_token</code>). HF uses the Inference API to generate <code className="text-[13px] bg-neutral-100 px-1 rounded">n_candidates</code>, then reranks.</li>
          </ul>
          <CodeBlock
            code={`# Train with Qwen tokenizer (saved model + tokenizer used at rerank)\nrequests.post("${BASE}/train", json={"tokenizer_name": "qwen2.5-7b", "epochs": 10})\n\n# Rerank: generate 5 candidates with HF Qwen, then pick best\nrequests.post("${BASE}/rerank", json={"prompt": "What is 2+2?", "hf_model": "qwen2.5-7b", "hf_token": "hf_...", "n_candidates": 5})`}
            lang="python"
          />
        </section>

        {/* Authentication */}
        <section id="authentication" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Authentication</h2>
          <p className="text-[15px] text-neutral-600 leading-relaxed mb-4">
            Bearer API keys via <a href="#ep-api-keys" className="text-blue-600 hover:underline font-mono text-[13px]">/api-keys</a>. When no keys exist, all endpoints are open (local dev). After creating a key, pass it in every request.
          </p>
          <CodeBlock
            code={`# Header (recommended)\ncurl -H "Authorization: Bearer ck_..." ${BASE}/health\n\n# SDK\nfrom certaintylabs import Certainty\nclient = Certainty(api_key="ck_...")`}
            lang="bash"
          />
          <p className="text-sm text-amber-800 mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <strong>Note:</strong> The raw key is returned only once from <code className="text-[11px] bg-white px-1 rounded">POST /api-keys</code>. Store it securely; only a hash is saved.
          </p>
        </section>

        {/* Quickstart */}
        <section id="quickstart" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Quickstart</h2>
          <p className="text-sm text-neutral-600 mb-4 leading-relaxed">
            Use the hosted Certainty API — no local server required.
          </p>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-medium text-neutral-500 mb-1.5">1. Set environment</p>
              <CodeBlock
                code={`export CERTAINTY_BASE_URL="${BASE}"\nexport CERTAINTY_API_KEY="ck_..."  # from /api-keys`}
                lang="bash"
              />
            </div>
            <div>
              <p className="text-xs font-medium text-neutral-500 mb-1.5">2. Train (built-in GSM8K)</p>
              <CodeBlock
                code={`import requests\nr = requests.post("${BASE}/train", json={"epochs": 10}, headers={"Authorization": "Bearer ck_..."}).json()\nprint(r["best_val_acc"], r["model_path"])`}
                lang="python"
              />
            </div>
            <div>
              <p className="text-xs font-medium text-neutral-500 mb-1.5">3. Rerank (your candidates or your LLM)</p>
              <CodeBlock
                code={`# Option A: you provide candidates\nbest = requests.post("${BASE}/rerank", json={"candidates": ["A", "B", "C"], "prompt": q}, headers={"Authorization": "Bearer ck_..."}).json()\n# Option B: API generates with your LLM then reranks\nbest = requests.post("${BASE}/rerank", json={"prompt": q, "openai_api_key": "sk-...", "n_candidates": 5}, headers={"Authorization": "Bearer ck_..."}).json()\nprint(best["best_candidate"])`}
                lang="python"
              />
            </div>
          </div>
        </section>

        {/* Python SDK */}
        <section id="sdk" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Python SDK</h2>
          <p className="text-sm text-neutral-600 mb-4 leading-relaxed">
            <code className="text-[13px] bg-neutral-100 px-1 rounded">certaintylabs</code> — typed sync/async clients for the hosted API. Supports <code className="text-[13px] bg-neutral-100 px-1 rounded">tokenizer_name</code> (Qwen/Llama), <code className="text-[13px] bg-neutral-100 px-1 rounded">openai_api_key</code>, and <code className="text-[13px] bg-neutral-100 px-1 rounded">hf_model</code>+<code className="text-[13px] bg-neutral-100 px-1 rounded">hf_token</code> for rerank; no local server needed.
          </p>
          <CodeBlock code={`pip install certaintylabs`} lang="bash" />
          <div className="mt-3 space-y-3">
            <CodeBlock
              code={`from certaintylabs import Certainty\n\n# Reads CERTAINTY_BASE_URL (${BASE}) and CERTAINTY_API_KEY from env\nclient = Certainty()\n\n# Train (built-in or your data)\nresult = client.train(epochs=10)\nresult = client.train_with_data(samples, epochs=10)\nresult = client.train_from_file("data.jsonl")\n\n# Rerank (your candidates or your LLM)\nbest = client.rerank(candidates=["A","B","C"], prompt=q)\nbest = client.rerank(prompt=q, openai_api_key="sk-...", n_candidates=5)`}
              lang="python"
            />
            <CodeBlock code={`from certaintylabs import AsyncCertainty\nasync with AsyncCertainty() as c:\n    r = await c.train(epochs=5)\n    b = await c.rerank(prompt=q, openai_api_key="sk-...")`} lang="python" />
          </div>
          <p className="text-xs text-neutral-500 mt-3">
            Env: <code className="bg-neutral-100 px-1 rounded">CERTAINTY_BASE_URL</code> (defaults to {BASE}), <code className="bg-neutral-100 px-1 rounded">CERTAINTY_API_KEY</code>. Errors: <code className="bg-neutral-100 px-1 rounded">APIError</code>, <code className="bg-neutral-100 px-1 rounded">ConnectionError</code>.
          </p>
        </section>

        {/* Verifiable & interpretable AI */}
        <section id="verifiable-ai" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Verifiable & interpretable AI</h2>
          <p className="text-[15px] text-neutral-600 leading-relaxed mb-3">
            In addition to <strong>reranking</strong> (pick the best candidate), you can get the <strong>energy score</strong> for any output via <code className="text-[13px] bg-neutral-100 px-1 rounded">POST /score</code>. Same EBM, no selection — just a numeric score per text. Use it to:
          </p>
          <ul className="text-sm text-neutral-600 space-y-1 list-disc list-inside mb-4">
            <li><strong>Track confidence</strong> — log energy for every LLM response and monitor drift or low-confidence outputs.</li>
            <li><strong>Audit reliability</strong> — attach scores to decisions for compliance and post-hoc review.</li>
            <li><strong>Interpretability</strong> — lower energy = more constraint-satisfying; compare outputs or A/B runs with a single metric.</li>
          </ul>
          <CodeBlock
            code={`# Score one or more outputs (order preserved)\nr = requests.post("${BASE}/score", json={"texts": [my_llm_output], "prompt": user_prompt}).json()\nlog_confidence(request_id, r["energies"][0])  # lower = higher confidence`}
            lang="python"
          />
          <p className="text-xs text-neutral-500 mt-2">
            SDK: <code className="bg-neutral-100 px-1 rounded">client.score(texts=[...], prompt=...)</code> returns <code className="bg-neutral-100 px-1 rounded">ScoreResponse(energies=[...])</code>.
          </p>
        </section>

        {/* Endpoints */}
        <section className="mb-14">
          <h2 className="text-xl font-semibold text-neutral-900 mb-6">Endpoints</h2>
          <div className="space-y-6">
            {endpoints.map((ep) => (
              <EndpointCard key={ep.path} ep={ep} id={`ep-${ep.path.slice(1)}`} />
            ))}
          </div>
        </section>

        {/* API Keys */}
        <section id="ep-api-keys" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">API Key Management</h2>
          <p className="text-sm text-neutral-600 mb-4 leading-relaxed">
            Create, list, revoke keys. Endpoints are public until the first key exists; then others require auth.
          </p>
          <div className="space-y-4">
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="POST" /><code className="text-sm font-mono">/api-keys</code>
                <span className="text-xs text-neutral-400">Create key (body: name). Returns id, key (once), prefix, created_at.</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl -X POST ${BASE}/api-keys -H "Content-Type: application/json" -d '{"name": "prod"}'`} lang="bash" /></div>
            </div>
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="GET" /><code className="text-sm font-mono">/api-keys</code>
                <span className="text-xs text-neutral-400">List keys (id, name, prefix, created_at).</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl ${BASE}/api-keys`} lang="bash" /></div>
            </div>
            <div className="border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
                <MethodBadge method="DELETE" /><code className="text-sm font-mono">/api-keys/{'{key_id}'}</code>
                <span className="text-xs text-neutral-400">Revoke key. Returns deleted, auth_enabled.</span>
              </div>
              <div className="px-4 py-2"><CodeBlock code={`curl -X DELETE ${BASE}/api-keys/KEY_ID`} lang="bash" /></div>
            </div>
          </div>
        </section>

        {/* Data Format */}
        <section id="data-format" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">EORM Data Format</h2>
          <p className="text-sm text-neutral-600 mb-3 leading-relaxed">
            JSONL: one JSON object per line. Two options:
          </p>
          <ul className="text-sm text-neutral-600 mb-3 leading-relaxed list-disc list-inside space-y-1">
            <li>
              <strong>Labeled candidates (classic EORM):</strong>{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">question</code>,{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">label</code> (0 or 1),{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">gen_text</code>. Same question = one group for
              Bradley–Terry loss.
            </li>
            <li>
              <strong>Preference pairs:</strong>{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">question</code>,{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">preferred</code>,{' '}
              <code className="text-[13px] bg-neutral-100 px-1 rounded">unpreferred</code>. The trainer automatically
              converts this into two candidates with labels 1/0.
            </li>
          </ul>
          <CodeBlock
            code={`{"question": "What is 2+2?", "label": 1, "gen_text": "The answer is 4."}\n{"question": "What is 2+2?", "label": 0, "gen_text": "The answer is 5."}\n{"question": "What is 2+2?", "preferred": "The answer is 4.", "unpreferred": "The answer is 5."}`}
            lang="jsonl"
          />
        </section>

        {/* Generating Data Externally */}
        <section id="data-external" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Generating your own data externally</h2>
          <p className="text-sm text-neutral-600 mb-3 leading-relaxed">
            If you need to create training data yourself: either (a) output labeled candidates (question, label, gen_text){' '}
            or (b) output preference pairs (question, preferred, unpreferred). Export as JSONL and use{' '}
            <code className="text-[13px] bg-neutral-100 px-1 rounded">train_from_file</code> (SDK) or{' '}
            <code className="text-[13px] bg-neutral-100 px-1 rounded">POST /train</code> with{' '}
            <code className="text-[13px] bg-neutral-100 px-1 rounded">data</code> or{' '}
            <code className="text-[13px] bg-neutral-100 px-1 rounded">data_path</code>. The trainer turns preferences into
            labeled pairs internally.
          </p>
        </section>

        {/* Errors */}
        <section id="errors" className="mb-14 scroll-mt-24">
          <h2 className="text-xl font-semibold text-neutral-900 mb-3">Errors</h2>
          <p className="text-sm text-neutral-600 mb-2">JSON body with <code className="text-[13px] bg-neutral-100 px-1 rounded">detail</code>.</p>
          <ul className="text-xs text-neutral-600 space-y-1 list-disc list-inside">
            <li><strong>400</strong> — Empty candidates without openai_api_key, bad body.</li>
            <li><strong>401</strong> — Missing/invalid API key (when auth enabled).</li>
            <li><strong>404</strong> — Model file or key id not found.</li>
            <li><strong>422</strong> — Validation (types, required fields).</li>
            <li><strong>500</strong> — Training/model/exception.</li>
          </ul>
          <CodeBlock code={`{"detail": "Model not found: ..."}`} lang="json" />
        </section>

        {/* Footer */}
        <div className="border-t border-neutral-200 pt-6 pb-12 flex items-center justify-between text-xs text-neutral-500">
          <span>Certainty Labs API v0.1.0</span>
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
