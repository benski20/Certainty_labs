// In production (e.g. Vercel), set NEXT_PUBLIC_API_URL to your deployed API URL so the app does not try localhost.
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const error = await res.text().catch(() => `HTTP ${res.status}`)
    throw new Error(error)
  }

  return res.json()
}

// ── Types ───────────────────────────────────────────────────────────

interface HealthResponse {
  status: string
  version: string
}

interface TrainResponse {
  model_path: string
  best_val_acc: number
  epochs_trained: number
  elapsed_seconds: number
}

interface RerankResponse {
  best_candidate: string
  best_index: number
  all_energies: number[]
}

interface PipelineResponse {
  train: TrainResponse
  rerank: RerankResponse | null
}

// API keys (stored in Supabase when configured)
interface KeyInfo {
  id: string
  name: string
  prefix: string
  created_at: number
}

interface CreateKeyResponse {
  id: string
  name: string
  key: string
  prefix: string
  created_at: number
}

interface ListKeysResponse {
  keys: KeyInfo[]
  auth_enabled: boolean
}

// ── API Client ──────────────────────────────────────────────────────

export const api = {
  health: () => apiRequest<HealthResponse>('/health'),

  keys: {
    create: (name: string) =>
      apiRequest<CreateKeyResponse>('/api-keys', {
        method: 'POST',
        body: JSON.stringify({ name: name || 'default' }),
      }),
    list: () => apiRequest<ListKeysResponse>('/api-keys'),
    delete: (id: string) =>
      apiRequest<{ deleted: string; auth_enabled: boolean }>(`/api-keys/${id}`, {
        method: 'DELETE',
      }),
  },

  train: (config: {
    data_path?: string
    data?: Record<string, unknown>[]
    epochs?: number
    batch_size?: number
    d_model?: number
    n_heads?: number
    n_layers?: number
    lr?: number
    max_length?: number
    validate_every?: number
    val_holdout?: number
  }) =>
    apiRequest<TrainResponse>('/train', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  rerank: (
    candidates: string[],
    opts?: { prompt?: string; model_path?: string; tokenizer_path?: string },
  ) =>
    apiRequest<RerankResponse>('/rerank', {
      method: 'POST',
      body: JSON.stringify({ candidates, ...opts }),
    }),

  pipeline: (config: {
    data_path?: string
    data?: Record<string, unknown>[]
    epochs?: number
    batch_size?: number
    d_model?: number
    n_heads?: number
    n_layers?: number
    lr?: number
    max_length?: number
    validate_every?: number
    val_holdout?: number
    candidates?: string[]
  }) =>
    apiRequest<PipelineResponse>('/pipeline', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
}
