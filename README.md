# agent

Multimodal agent OS focused on turning text + images into actionable, high-signal knowledge. Backend uses Python (uv/uvicorn/FastAPI) with an in-memory store by default, and the frontend uses React + TypeScript with Bun. The layout keeps the agent core framework-agnostic while allowing adapters for LangGraph/AG2/etc.

## Core goal
Build a top-tier multimodal understanding system that can digest text and imagery, reason over it, and produce useful knowledge artifacts (summaries, decisions, visuals) with minimal operator friction. OpenRouter and Gemini/OpenAI are pluggable so we can route requests through the best model for each modality.

## Roadmap
- **Foundations (✅):** finalized the `agent` rename, aligned entrypoints, and kept LLM clients swap-friendly.
- **Multimodal ingestion (✅):** standardized text/image/audio schemas, added an ingestion endpoint that emits `KnowledgeBundle` objects, and wired tracing to compare graph steps.
- **Knowledge shaping (✅):** composed summarization + decision-support graphs, added knowledge bundle helpers, and exposed APIs for downstream tools.
- **Delivery (✅):** exposed roadmap metadata via API, kept deployment scripts lightweight, and documented how to stay keyless by default.

### Status and next steps
- **Completed:** agent rename, OpenRouter/Gemini clients with stub fallbacks, multimodal ingestion schemas + bundle helpers, summarization/decision graphs, multimodal mixer graph, lightweight retrieval hooks, retrieval benchmarks with canned multimodal corpora, automated benchmark trends across adapter flavors, in-memory tracing + store registry, adapter catalog (memory/SQLite/JSONL/object-store stub) surfaced via API, frontend observability panels with trace timelines and orchestration replay, a multi-agent orchestration path, and FastAPI endpoints for ingestion/decision/eval/paper review/roadmap/retrieval/adapters/traces/orchestration/benchmarks.
- **Active:** promoting the object-store stub into a signed-URL S3-compatible adapter, shipping local/quantized LLM adapters, and widening replay/visualization options.
- **Planned expansions:** richer frontend visualizations for retrieval/orchestration comparisons and optional vector/external adapter plugs.

### Technical approach
- Keep the FastAPI layer thin and wire agents/graphs through dependency-injected factories.
- Use the `StoreRegistry` to register optional persistence backends (vector DBs, S3, or SQLite) while defaulting to in-memory.
- Prefer pluggable LLM clients (Google, OpenRouter, local) and guard them with stubbed fallbacks to stay keyless by default.
- Keep evaluation lightweight via the `EvaluationHarness` so new judges or reward models can be swapped in quickly.
- Provide retrieval hooks that work offline with simple embeddings while remaining swappable for production-grade vector services.

### Industry practices for multimodal understanding
- Align modalities early with shared embeddings or cross-attention blocks so fusion graphs keep provenance and consistent salience.
- Preserve modality tags end-to-end (ingestion → retrieval → reasoning) to maintain weighting cues during summarization and routing.
- Ground prompts with retrieval-augmented context and contrastive negatives to reduce hallucinations when mixing images and text.
- Track per-modality quality metrics (caption fidelity, OCR/ASR confidence) and gate low-signal slices before mixing.
- Run lightweight safety passes (NSFW/PII/toxicity) before storing or returning multimodal artifacts.

### Optimization focus
- Start with free/community tiers (Gemini free, OpenRouter promos) before routing to paid paths; defaults stub when keys are missing.
- Cache cross-modal embeddings locally and reuse them in retrieval to avoid repeated encoding overhead.
- Benchmark the built-in retrieval engine against portable vector backends (SQLite FTS, Chroma) to choose the right default.
- Instrument graph steps with tracing spans and bundle-level stats to surface slow or lossy stages in the UI.

## Repo layout
- `src/agent/`: Agent OS core, memory, eval, LLM interfaces, infra, adapters, and example apps.
- `frontend/`: React + TypeScript client scaffold runnable with Bun.
- `scripts/`: One-click setup and dev helpers.
- `tests/`: Pytest entrypoint for backend code.

## Prerequisites
- Python 3.11+ with [uv](https://github.com/astral-sh/uv) available.
- [Bun](https://bun.sh/) for the frontend.
- Node-compatible toolchain (for React typings).
- Google Generative AI key (`GOOGLE_API_KEY`) if you want real text + image generation; otherwise stubs are used.
- OpenRouter key (`OPENROUTER_API_KEY`) if you want to route LLM calls through OpenRouter's model catalog.

### Testing with free/low-cost API keys
- **Gemini free tier:** create a key via [Google AI Studio](https://ai.google.dev/) and set `GOOGLE_API_KEY`. Text + image calls work out of the box; without a key the server returns stubbed content and placeholder images.
- **OpenRouter:** sign up for an API key and select community-hosted or promotional free models when available. Set `OPENROUTER_API_KEY` and optionally override `OPENROUTER_MODEL` to target a specific free/low-cost model.
- **Offline/local:** keep both keys unset to use stubbed responses everywhere and rely on `python -m pytest` for quick validation.

## Quick start
```bash
# 1) Install Python deps
uv sync

# 2) Install frontend deps
cd frontend && bun install && cd ..

# 3) Run both servers (FastAPI + Bun dev)
bash scripts/dev.sh
```

The FastAPI server listens on `http://0.0.0.0:8000` with health/task endpoints. Bun dev server defaults to `http://localhost:5173`.

Copy `.env.example` to `.env` and set `GOOGLE_API_KEY` to use Gemini for analysis + image generation. Default models can be adjusted via `GOOGLE_MODEL` and `GOOGLE_IMAGE_MODEL`.
To try OpenRouter instead of Gemini/OpenAI, set `OPENROUTER_API_KEY` and optionally override `OPENROUTER_MODEL` (defaults to `openrouter/auto`).

## Adapter cookbook
- **State storage:** defaults to in-memory (`STATE_DB_PATH=:memory:`). Set `STATE_DB_PATH` for a SQLite file, `STATE_LOG_PATH` for an append-only JSONL log, or `OBJECT_STORE_PATH` for a file-backed object-store stub (one JSON blob per task). All adapters are pre-registered in the store registry and exposed via `/adapters`.
- **LLM routing:** keep keys unset for stubbed responses, set `GOOGLE_API_KEY` for Gemini multimodal calls, or set `OPENROUTER_API_KEY` to use community/hosted models. `/adapters` reflects which paths are live vs. stubbed.
- **Observability:** `/traces/recent` streams recent spans captured by `traced_span`, and the frontend displays them alongside roadmap data, adapter status, and a retrieval sandbox.

## Scripts
- `scripts/setup.sh` — installs Python (uv sync) and frontend dependencies (bun install).
- `scripts/dev.sh` — starts uvicorn for the API and Bun dev server in the background, with basic log output.
- `scripts/deploy-cloud-run.sh` — builds and deploys the API to Cloud Run using `gcloud builds submit` and `gcloud run deploy`. It reads `.env` for API keys and forwards them as service env vars.

### Cloud Run deploy (one command)
```bash
# Ensure gcloud is installed and you have set PROJECT_ID (or configured gcloud default project)
PROJECT_ID=my-gcp-project \
SERVICE_NAME=agent-api \
REGION=us-central1 \
bash scripts/deploy-cloud-run.sh
```

The script builds the Docker image from the repo, uploads via Cloud Build, and deploys to Cloud Run with reasonable defaults (1Gi memory, 0-3 instances, unauthenticated). `.env` values like `GOOGLE_API_KEY` are forwarded automatically as `--set-env-vars`.

## Backend entrypoints
- `agent.infra.server:create_app` exposes the FastAPI app. Run with:
  ```bash
  uv run uvicorn agent.infra.server:app --reload --host 0.0.0.0 --port 8000
  ```
- `agent.apps.cli` provides a Typer CLI to run a demo loop:
  ```bash
  uv run python -m agent.apps.cli --task-id demo
  ```

### Paper review endpoints
- `POST /review/analyze` — provide `{title, abstract, url?}`; returns summary, key points, and recommended image prompts.
- `POST /review/images` — send `{prompts: [{id, prompt, feedback?}], style?}`; returns generated image URLs (Google by default, placeholders if no key).
- `GET /roadmap` — returns completed work, active tasks, upcoming milestones, technical plan, industry practices, optimization focus, and testing tips (including keyless flows).
- `POST /ingest/multimodal` — send `texts/images/audio` batches to get normalized `KnowledgeBundle` output that downstream tools can consume.
- `POST /reason/multimodal` — run the multimodal mixer graph to keep text/image/audio cues aligned step-by-step and return a bundle.
- `POST /decide` — run the decision-support graph and receive rationale as a `KnowledgeBundle`.
- `POST /retrieve/index` — index an existing `KnowledgeBundle` for retrieval.
- `POST /retrieve/query` — query the retrieval index with `{query, top_k?}` to fetch best-matching slices.
- `POST /retrieve/benchmark` — run the built-in multimodal benchmark suite to compare adapter/engine quality.
- `POST /retrieve/benchmark/automated` — batch benchmarks across adapter flavors and return macro precision/recall trends.
- `GET /adapters` — surface available store + LLM adapters with setup guidance.
- `GET /traces/recent` — fetch recent traces for lightweight observability panels.
- `GET /traces/timeline` — group spans by task for replayable timelines in the UI.
- `POST /orchestrate` — drive a retrieval → synthesis → evaluation multi-agent path with a supplied bundle and goal.
- `POST /eval/run` — feed `cases` to the lightweight evaluation harness to quickly sanity-check graphs and judges.

## Frontend entrypoints
- `bun dev` serves the React app with hot reload.
- `bun test` runs unit tests (Vitest).
- `bun run e2e` runs Playwright E2E tests. Install browsers once via `bunx playwright install --with-deps chromium`.

## Notes
- State is kept in-memory by default to avoid external DB dependencies; adapters can be added in `infra/store.py` if you need persistence.
- Memory, eval, and LLM modules contain interfaces and minimal defaults to extend for production.
