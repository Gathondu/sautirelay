# SautiRelay

SautiRelay is a privacy-first community reporting and escalation platform for Africa.

The app is planned as a local-first Svelte 5 + FastAPI project. The frontend uses `pnpm`, the backend uses `uv`, and frontend/backend communication must go through the OpenAPI contract at `backend/app/openapi.yaml`.

## Current Scope

- Build and test locally first.
- Document future AWS architecture without adding deployment code.
- Keep the OpenAPI contract as the boundary between frontend and backend.
- Prioritize anonymous reporting, consent-based location handling, structured report output, and responder routing workflows.
- Use Svelte 5 strictly for frontend work: runes, CSS Modules, and no Svelte 3/4 syntax.

## Documentation

- Project plan: [PLAN.md](PLAN.md)
- Docs table of contents: [docs/README.md](docs/README.md)
- Product docs: [docs/product/README.md](docs/product/README.md)
- Product brief: [docs/product/product-brief.md](docs/product/product-brief.md)
- Product architecture: [docs/product/architecture.md](docs/product/architecture.md)
- User flows: [docs/product/user-flows.md](docs/product/user-flows.md)
- App components: [docs/product/app-components.md](docs/product/app-components.md)
- Engineering standards: [docs/engineering/README.md](docs/engineering/README.md)
- Engineering architecture: [docs/engineering/architecture.md](docs/engineering/architecture.md)
- API conventions: [docs/engineering/api-conventions.md](docs/engineering/api-conventions.md)
- Backend standards: [docs/engineering/backend-python.md](docs/engineering/backend-python.md)
- Local development: [docs/engineering/local-development.md](docs/engineering/local-development.md)
- Future infrastructure notes: [infra/README.md](infra/README.md)
- Agent instructions: [AGENTS.md](AGENTS.md)

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

Dockerfiles are still planned, so Compose should be fully validated after the Docker phase in `PLAN.md` is implemented.

## Planned Next Steps

- Implement FastAPI app structure under `backend/app/`.
- Generate the frontend TypeScript API client from `backend/app/openapi.yaml`.
- Build the Svelte report submission flow.
- Add frontend and backend tests.
- Add Dockerfiles and correct Compose build contexts.
