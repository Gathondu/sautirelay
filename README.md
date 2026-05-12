# sautirelay

`sautirelay` is a Svelte + FastAPI application scaffolded for local-first development and future AWS deployment.

The frontend is intended to run with `pnpm` and Svelte with Vite. The backend is intended to run with `uv` and FastAPI. Production deployment is planned for AWS using S3 + CloudFront for the frontend and Lambda + API Gateway for the backend, but deployment code is intentionally deferred for now.

## Current Structure

```text
sautirelay/
|- frontend/
|  |- src/
|  |- static/
|  |- tests/
|  |- package.json
|  \- vite.config.ts
|- backend/
|  |- app/
|  |  |- routers/
|  |  \- schemas/
|  |- tests/
|  \- main.py
|- docker/
|  \- docker-compose.yml
|- docs/
|- PLAN.md
|- AGENTS.md
\- README.md
```

## Tooling

- Frontend package manager: `pnpm`
- Backend runtime and dependency workflow: `uv`
- Frontend framework: Svelte with Vite
- Backend framework: FastAPI
- Local container orchestration: Docker Compose

## Local Development

### Frontend

Run frontend commands from `frontend/`.

```powershell
pnpm install
pnpm dev
```

### Backend

Run backend commands from the repository root.

```powershell
uv sync
uv run backend/main.py
```

### Docker Compose

Use the compose file in `docker/` to wire local services.

```powershell
docker compose -f docker/docker-compose.yml up
```

## Planned Next Steps

- Add `backend/app/openapi.yaml`
- Add generated frontend API client under `frontend/src/api/`
- Add frontend and backend Dockerfiles
- Add unit tests for backend and frontend
- Add CI workflow and AWS deployment documentation placeholders

## Documentation

- Project plan: [PLAN.md](C:/Users/dng/Development/sautirelay/PLAN.md:1)
- Agent instructions: [AGENTS.md](C:/Users/dng/Development/sautirelay/AGENTS.md:1)
