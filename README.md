# AI Service Platform

Full-stack AI-driven service platform with a credit-based in-app economy, a
multi-provider LLM agent pipeline (OpenAI GPT-4o primary, Gemini fallback),
and a multi-format video generation engine (Reels/Shorts 9:16, YouTube Main 16:9).

## Structure

```
/backend    FastAPI app (async, SQLAlchemy + PostgreSQL)
  /app
    /api/routers   auth, users, credits, videos, llm, webhooks
    /core          security (JWT), rate limiting, RBAC dependencies
    /models        SQLAlchemy models (user, credit, subscription, video_job, llm_usage)
    /schemas       Pydantic request/response models
    /services      credit_service, llm_service, stripe_service, video_engine/
      /video_engine
        job_manager.py       job creation + async processing (queue-ready)
        /renderers           pluggable renderer interface (mock, ffmpeg, external API)
    /config        environment-driven settings
/frontend   Next.js dashboard (auth, credit balance, top-up modal, video studio)
docker-compose.yml
.env.example
```

## Getting Started (Docker)

```bash
cp .env.example .env
# fill in real secrets (JWT_SECRET_KEY, POSTGRES_PASSWORD, OPENAI_API_KEY, etc.)
docker-compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000

## Getting Started (Local, no Docker)

Backend:
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# requires a running PostgreSQL instance matching DATABASE_URL in .env
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Credit Economy

- New users receive `SIGNUP_BONUS_CREDITS` on registration.
- Every LLM call and video job debits credits atomically through
  `app/services/credit_service.py`, which maintains an immutable
  `credit_transactions` ledger alongside the running `credit_balances` row.
- Top-ups are purchased via Stripe Checkout (`/credits/top-up/checkout`) and
  credited on the `checkout.session.completed` webhook (`/webhooks/stripe`),
  idempotently keyed on the Stripe session id.

## Multi-Format Video Engine

- Format specs (resolution, fps, safe zones, max duration) live in
  `app/models/video_job.py::VIDEO_FORMAT_SPECS`.
- `POST /api/v1/videos/jobs` charges credits, inserts a `VideoJob` row, and
  schedules async processing (`app/services/video_engine/job_manager.py`).
- Renderer backend is selected via `VIDEO_RENDERER_BACKEND` env var:
  - `mock` (default) — simulated render for local dev/testing.
  - `ffmpeg` — local ffmpeg-based pipeline stub.
  - `external` — stub for a third-party text-to-video API.
- Swap `job_manager._enqueue`/`process_job` for Celery/RQ/Arq in production
  without touching the API layer.

## Notes

- `.env.example` contains placeholder secrets only — real OpenAI, Gemini, and
  Stripe keys must be supplied by you before those integrations will work live.
- Rate limiting is an in-memory sliding window (`app/core/rate_limit.py`);
  back it with Redis for multi-instance deployments.
- Dev convenience `init_db()` auto-creates tables on startup; use Alembic
  migrations for schema changes in production.
