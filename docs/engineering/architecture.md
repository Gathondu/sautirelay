# Engineering Architecture

## Repository Shape

SautiRelay is organized as a local-first frontend/backend application:

```text
sautirelay/
|- frontend/                 # Svelte 5 + Vite, pnpm
|- backend/                  # FastAPI, uv
|- docker/                   # Local Docker assets
|- docs/                     # Documentation index
|  |- product/               # Product documentation
|  \- engineering/          # Canonical engineering standards
|- .cursor/rules/            # Cursor adapters to engineering standards
|- infra/                    # Future infrastructure notes only
|- AGENTS.md                 # Portable AI/contributor entrypoint
|- PLAN.md
\- README.md
```

## Service Boundaries

- Frontend owns user interaction, form state, consent presentation, validation display, and API result rendering.
- Backend owns validation, privacy handling, relay structuring, classification placeholders, and route recommendation.
- OpenAPI owns the contract between frontend and backend.

## Frontend Boundary

The frontend uses Svelte 5 with Vite. It should call the backend through generated client code derived from `backend/app/openapi.yaml`.

Do not put backend business logic in the frontend. Basic form affordances and client-side validation are acceptable, but the backend remains authoritative.

## Backend Boundary

The backend uses FastAPI. Route handlers should be thin and delegate business behavior to services.

The backend should be deterministic until the project explicitly introduces provider-backed AI or persistence.

## Deployment Boundary

AWS deployment is future-facing documentation only. Do not add deployment code until requested.

## Rule Boundary

Engineering standards live in `docs/engineering/`. Cursor rules and other AI tool adapters should only route agents and contributors to the relevant standards.
