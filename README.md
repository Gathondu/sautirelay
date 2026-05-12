# SautiRelay

SautiRelay is a privacy-first community reporting and escalation platform for Africa.

The app is planned as a local-first Svelte 5 + FastAPI project. The frontend uses `pnpm`, the backend uses `uv`, and frontend/backend communication must go through the OpenAPI contract at `backend/app/openapi.yaml`.

## Current Scope

- Build and test locally first.
- Document future AWS architecture without adding deployment code.
- Keep the OpenAPI contract as the boundary between frontend and backend.
- Prioritize anonymous reporting, consent-based location handling, structured relay output, and responder routing workflows.
- Use Svelte 5 strictly for frontend work: runes, CSS Modules, and no Svelte 3/4 syntax.

## Documentation

- Project plan: [PLAN.md](C:/Users/dng/Development/sautirelay/PLAN.md:1)
- Product docs: [docs/product/README.md](C:/Users/dng/Development/sautirelay/docs/product/README.md:1)
- Product brief: [docs/product/product-brief.md](C:/Users/dng/Development/sautirelay/docs/product/product-brief.md:1)
- Architecture: [docs/product/architecture.md](C:/Users/dng/Development/sautirelay/docs/product/architecture.md:1)
- User flows: [docs/product/user-flows.md](C:/Users/dng/Development/sautirelay/docs/product/user-flows.md:1)
- App components: [docs/product/app-components.md](C:/Users/dng/Development/sautirelay/docs/product/app-components.md:1)
- Backend design: [docs/backend-design.md](C:/Users/dng/Development/sautirelay/docs/backend-design.md:1)
- API contract workflow: [docs/api-contract.md](C:/Users/dng/Development/sautirelay/docs/api-contract.md:1)
- Engineering standards: [docs/engineering/README.md](C:/Users/dng/Development/sautirelay/docs/engineering/README.md:1)
- Development rules: [docs/development-rules.md](C:/Users/dng/Development/sautirelay/docs/development-rules.md:1)
- Local development: [docs/local-dev.md](C:/Users/dng/Development/sautirelay/docs/local-dev.md:1)
- Future infrastructure notes: [infra/README.md](C:/Users/dng/Development/sautirelay/infra/README.md:1)
- Agent instructions: [AGENTS.md](C:/Users/dng/Development/sautirelay/AGENTS.md:1)

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
