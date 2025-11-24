# alex-code-agent

Monorepo scaffold for a worker-flow agent that generates media content. Backend uses Python (uv/uvicorn/FastAPI), frontend uses React + TypeScript with Bun, and Supabase can be added for state/storage. The layout keeps the agent core framework-agnostic while allowing adapters for LangGraph/AG2/etc.

## Repo layout
- `src/alex_agent/`: Agent OS core, memory, eval, LLM interfaces, infra, adapters, and example apps.
- `frontend/`: React + TypeScript client scaffold runnable with Bun.
- `scripts/`: One-click setup and dev helpers.
- `tests/`: Pytest entrypoint for backend code.

## Prerequisites
- Python 3.11+ with [uv](https://github.com/astral-sh/uv) available.
- [Bun](https://bun.sh/) for the frontend.
- Node-compatible toolchain (for React typings) and optional Supabase credentials.
- Google Generative AI key (`GOOGLE_API_KEY`) if you want real text + image generation; otherwise stubs are used.

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

## Scripts
- `scripts/setup.sh` — installs Python (uv sync) and frontend dependencies (bun install).
- `scripts/dev.sh` — starts uvicorn for the API and Bun dev server in the background, with basic log output.

## Backend entrypoints
- `alex_agent.infra.server:create_app` exposes the FastAPI app. Run with:
  ```bash
  uv run uvicorn alex_agent.infra.server:app --reload --host 0.0.0.0 --port 8000
  ```
- `alex_agent.apps.cli` provides a Typer CLI to run a demo loop:
  ```bash
  uv run python -m alex_agent.apps.cli --task-id demo
  ```

### Paper review endpoints
- `POST /review/analyze` — provide `{title, abstract, url?}`; returns summary, key points, and recommended image prompts.
- `POST /review/images` — send `{prompts: [{id, prompt, feedback?}], style?}`; returns generated image URLs (Google by default, placeholders if no key).

## Frontend entrypoints
- `bun dev` serves the React app with hot reload.
- `bun test` runs unit tests (Vitest).
- `bun run e2e` runs Playwright E2E tests. Install browsers once via `bunx playwright install --with-deps chromium`.

## Notes
- Supabase integration can be wired through `infra/store.py` or dedicated adapters; the core remains storage-agnostic.
- Memory, eval, and LLM modules contain interfaces and minimal defaults to extend for production.
