# Certainty Labs: Production Roadmap

A prioritized list of steps to reach production-grade, startup-ready (e.g. Thinking Machines Lab–style) execution. Based on the current codebase: API + auth, SDK on TestPyPI, Next.js platform with docs/billing/keys, core compiler + TransEBM pipeline, and pytest coverage.

---

## 1. Hosted API & reliability

**Why first:** Until the API is deployed, every user is “run it yourself.” That caps adoption and revenue.

| Step | What | Notes |
|------|------|--------|
| Deploy API | Run FastAPI on a cloud (Railway, Fly.io, GCP Cloud Run, AWS ECS). | Start with a single region; use Docker or buildpack. |
| Persistent key store | Move API keys off local JSON (e.g. Postgres or managed secrets). | `api/auth.py` currently uses `certainty_workspace/api_keys.json`. |
| Health + uptime | Add `/health` that checks DB/disk; put behind a status page (e.g. statuspage.io or custom). | So users and you know when the API is down. |
| Async training | Make `/train` async: accept job, return `job_id`, poll `/train/status/{job_id}`. | Prevents timeouts and improves UX; you already had this pattern before simplification. |

**Outcome:** Users can call `CERTAINTY_BASE_URL=https://api.certaintylabs.ai` and rely on a live, key-protected API.

---

## 2. Billing & usage

**Why:** Converts usage into revenue and sets clear limits.

| Step | What | Notes |
|------|------|--------|
| Usage metering | Count per-request or per-token usage per API key (e.g. in Postgres). | Log in middleware or in route handlers; aggregate by key + period. |
| Billing backend | Wire platform “Billing” to Stripe (or similar): subscriptions and/or usage-based. | Platform already has a billing page; connect it to a real product/price. |
| Rate limits | Throttle by API key (and optionally by plan). | e.g. 100 req/min free; higher for paid. Use slowapi or custom middleware. |
| Free tier | Define a free tier (e.g. N trains/month, M rerank calls/day). | Clear ceiling so users know when they need to upgrade. |

**Outcome:** You can charge for usage and show usage/billing in the platform.

---

## 3. Observability & operations

**Why:** You need to detect and fix incidents and understand behavior.

| Step | What | Notes |
|------|------|--------|
| Structured logging | JSON logs with request_id, key_id, endpoint, latency, status. | Pipe to Datadog, Aiven, or cloud logging. |
| Metrics | Count requests, errors, and latency by endpoint and key (e.g. Prometheus + Grafana or managed). | Alerts on error rate and latency. |
| Error tracking | Send exceptions to Sentry (or similar). | Fast path to fixing production bugs. |
| Runbooks | One-pager per failure mode: “API 5xx” → check DB, queues, disk. | So anyone on-call can respond. |

**Outcome:** You can debug and improve reliability with data, not guesswork.

---

## 4. Security & compliance (for enterprises)

**Why:** Larger accounts will ask for this before signing.

| Step | What | Notes |
|------|------|--------|
| HTTPS only | Enforce TLS; redirect HTTP → HTTPS. | Standard for production. |
| Key scopes (optional) | Optional per-key limits (e.g. only /rerank, or only certain projects). | Helps enterprises isolate use cases. |
| Audit log | Log key creation/revocation and sensitive operations (e.g. key access to data). | Store in DB or append-only store; useful for SOC2-style narratives. |
| Rate limit by IP | Optional DDoS protection in front of the API (e.g. Cloudflare or API gateway). | Complements key-based limits. |

**Outcome:** You can answer basic security questionnaires and reduce risk.

---

## 5. Product & positioning

**Why:** Clear story and packaging drive adoption and pricing.

| Step | What | Notes |
|------|------|--------|
| One-line pitch | e.g. “Constraint-guaranteed LLM outputs: train a scorer, rerank N candidates, ship the best.” | Use on landing, docs, and in sales. |
| ICP | Pick primary segment: e.g. “AI/ML teams shipping production RAG/agents” or “Compliance-heavy verticals (legal, healthcare).” | Shapes messaging and feature order. |
| Packaging | e.g. Free (limited), Pro (usage-based), Enterprise (SSO, SLA, support). | Align with billing and rate limits. |
| Benchmarks | Publish accuracy/latency on GSM8K (and one other domain) vs baseline. | Builds trust and differentiates from “generic reranker.” |

**Outcome:** Consistent narrative and a clear “who this is for” and “why pay.”

---

## 6. Engineering quality

**Why:** Keeps velocity high and regressions low as you add features.

| Step | What | Notes |
|------|------|--------|
| API integration tests | pytest against a live (or testcontainer) API: health, compile, validate, train (small), rerank. | You have unit tests; add a small suite that hits the real HTTP API. |
| SDK in CI | In SDK repo/CI: install from PyPI (or wheel), run `scripts/test_sdk.py` against a test API. | Prevents shipping a broken SDK. |
| API versioning | e.g. `/v1/compile` and document “v1 stable; v2 when we break things.” | Lets you evolve without breaking existing users. |
| Backward compatibility | When changing request/response shapes, support old clients for N months or major version. | Document in SDK and API changelog. |

**Outcome:** Safer releases and clearer contracts for users.

---

## 7. Data & model experience

**Why:** Ease of getting data in and models out increases activation and retention.

| Step | What | Notes |
|------|------|--------|
| Data upload API | Allow upload of JSONL (or link to S3/GCS) for training instead of only server-side paths. | Removes “I have to SSH and put files there” friction. |
| Model registry | Store trained models by key/project; return a `model_id`; let rerank accept `model_id` or path. | Enables “train once, rerank from anywhere” and multi-model per account. |
| Prebuilt datasets | Offer 2–3 public datasets (e.g. GSM8K + code + one vertical) as one-click options in UI or API. | Lowers time-to-first-train. |

**Outcome:** Users can go from “I have data” or “I want to try” to a trained model with minimal steps.

---

## 8. Platform UX & growth

**Why:** Conversion and retention depend on onboarding and value visibility.

| Step | What | Notes |
|------|------|--------|
| Signup → first key | Flow: sign up → create API key → copy `CERTAINTY_BASE_URL` + key into SDK or env. | Single “hello world” script in docs that works after signup. |
| Dashboard usage | Show usage (calls, training jobs, failures) per key in the platform. | Reuse the same metrics you use for billing. |
| Docs + SDK in one place | Keep API docs and SDK snippets in sync; add “Try it” with a sandbox key if you offer one. | You already have SDK tabs; add a clear “run this after signup” section. |
| Status page | Public status page for API and platform. | Links from docs and footer; reduces support load during incidents. |

**Outcome:** New users get to “first successful rerank” quickly; existing users see value and limits.

---

## Suggested order (next 3–6 months)

1. **Hosted API + persistent keys** (Section 1) — so the product is “use our API” not “run our code.”
2. **Usage metering + Stripe + rate limits** (Section 2) — so you can charge and protect the system.
3. **Logging + metrics + errors** (Section 3) — so you can operate and debug.
4. **Async training + job status** (rest of Section 1) — so training doesn’t time out and UX scales.
5. **Pitch + ICP + packaging** (Section 5) — so positioning and pricing are clear.
6. **Data upload + model registry** (Section 7) — so power users can bring their own data and models without SSH.

Sections 4 (security), 6 (engineering quality), and 8 (platform UX) can be done in parallel in small chunks (e.g. HTTPS and runbooks early; audit log and full SDK CI as you approach enterprise or scale).

---

## Summary

You already have: a differentiated core (constraints → TransEBM → rerank), a clean API, auth, an SDK, and a docs/billing/keys platform. The biggest gaps for a “production-level startup” are: **running the API as a hosted service**, **persistent keys and usage-based billing**, **observability**, and **async training**. After that, focus on **positioning, packaging, and data/model UX** so the product is easy to try, buy, and scale with.
