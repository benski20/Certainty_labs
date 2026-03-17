// In production (e.g. Vercel), set NEXT_PUBLIC_API_URL to your deployed API URL so the app does not try localhost.
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit & { userId?: string; baseUrl?: string },
): Promise<T> {
  const { userId, baseUrl = API_BASE, ...rest } = options ?? {}
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rest.headers as Record<string, string>),
  }
  if (userId) {
    headers['X-User-ID'] = userId
  }
  const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint
  const res = await fetch(url, {
    ...rest,
    headers,
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
    // When userId is provided, call backend directly (fast). Otherwise use proxy for server-side session.
    create: (name: string, userId?: string) =>
      userId
        ? apiRequest<CreateKeyResponse>('/api-keys', {
            method: 'POST',
            body: JSON.stringify({ name: name || 'default' }),
            userId,
          })
        : apiRequest<CreateKeyResponse>('/api/keys', {
            method: 'POST',
            body: JSON.stringify({ name: name || 'default' }),
            baseUrl: '',
          }),
    list: (userId?: string) =>
      userId
        ? apiRequest<ListKeysResponse>('/api-keys', { userId })
        : apiRequest<ListKeysResponse>('/api/keys', { baseUrl: '' }),
    delete: (id: string, userId?: string) =>
      userId
        ? apiRequest<{ deleted: string; auth_enabled: boolean }>(`/api-keys/${id}`, {
            method: 'DELETE',
            userId,
          })
        : apiRequest<{ deleted: string; auth_enabled: boolean }>(`/api/keys/${id}`, {
            method: 'DELETE',
            baseUrl: '',
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
