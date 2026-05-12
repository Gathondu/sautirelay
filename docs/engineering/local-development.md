# Local Development Workflow

## Prerequisites

- Node.js with `pnpm`.
- Python with `uv`.
- Docker Desktop or a compatible Docker runtime for Compose validation.

## Frontend

Run from `frontend/`:

```powershell
pnpm install
pnpm dev
```

Expected local URL: `http://localhost:5173`.

Frontend work must use Svelte 5. When checks are configured, run:

```powershell
pnpm lint
pnpm test
pnpm exec svelte-check
```

The project rule set requires `pnpm` for all frontend package operations.

## Backend

Run from the repository root:

```powershell
uv sync
uv run backend/main.py
```

Expected local URL: `http://localhost:8000`.

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/status
```

## Docker Compose

Run from the repository root:

```powershell
docker compose -f docker/docker-compose.yml up
```

Use this after meaningful cross-service changes. If Dockerfiles are not present yet, complete the Docker phase in `PLAN.md` before treating Compose as fully validated.

## Environment

Local defaults belong in `.env.example`. Secrets and real deployment values should not be committed.

## Troubleshooting

- If the frontend cannot reach the backend, check `VITE_API_BASE_URL`.
- If the backend does not start, run `uv sync` and confirm dependencies in `backend/pyproject.toml`.
- If generated API types are stale, regenerate them from `backend/app/openapi.yaml`.
- If Compose build paths fail, verify contexts in `docker/docker-compose.yml` are relative to the compose file location.
