# Project Plan - SautiRelay

## Product Summary

**SautiRelay** is a privacy-first community reporting and escalation platform for Africa. User-facing product language should use **SautiRelay**, while repository and package identifiers remain lowercase `sautirelay`.

The MVP lets a community member safely submit an early warning or civic concern, captures only the location detail needed for routing, anonymizes and structures the report, and relays it to a trusted responder or verification workflow. The first implementation is local-only: Svelte 5 with Vite for the frontend, FastAPI for the backend, and an OpenAPI contract as the only frontend/backend boundary.

## Problem And Objective

Communities often notice early signs of conflict, civic harm, public service breakdown, aid diversion, displacement pressure, or safety risks before formal responders do. Reporting can be risky when identity, location, or raw wording exposes the reporter. SautiRelay solves this by turning a sensitive community signal into a safer, structured relay item that can be reviewed, triaged, and routed without exposing unnecessary personal details.

## MVP Scope

- Anonymous report submission for community signals.
- Optional, consent-based location details with manual fallback.
- AI-ready report structuring fields: category, urgency, summary, safety notes, and recommended route.
- Human verification and responder handoff workflow documented in the product flow.
- Local FastAPI endpoints for health checks and relay submission.
- Svelte UI for report capture, validation feedback, submission status, and response display.
- Documentation for architecture, user flows, app components, backend design, API contract, and future AWS deployment assumptions.

## Non-Goals For Current Phase

- No AWS deployment scripts or infrastructure-as-code.
- No production authentication, SMS/USSD/WhatsApp integration, or responder organization onboarding.
- No live LLM provider integration until the local contract and placeholder relay workflow are stable.
- No storage of precise reporter identity or precise coordinates unless a later privacy review explicitly approves it.

## Repository Layout

```text
sautirelay/
|- frontend/                  # Svelte 5 + Vite UI, managed with pnpm
|  |- src/
|  |  |- api/                 # Generated TypeScript client from backend/app/openapi.yaml
|  |  |- components/          # Svelte 5 UI components plus CSS modules
|  |  \- routes/              # App views when routing is introduced
|  |- static/
|  |- tests/
|  |- package.json
|  \- vite.config.ts
|- backend/                   # FastAPI service, run with uv
|  |- app/
|  |  |- routers/
|  |  |- schemas/
|  |  |- services/
|  |  \- openapi.yaml         # Contract source of truth
|  |- tests/
|  |- main.py
|  \- pyproject.toml
|- docker/
|  |- backend.Dockerfile
|  |- frontend.Dockerfile
|  \- docker-compose.yml
|- docs/
|  |- api-contract.md
|  |- backend-design.md
|  |- development-rules.md
|  |- engineering/            # Canonical engineering standards
|  |- local-dev.md
|  \- product/                # Product-specific documentation
|     |- README.md
|     |- app-components.md
|     |- architecture.md
|     |- product-brief.md
|     \- user-flows.md
|- .cursor/
|  \- rules/                 # Cursor adapters to docs/engineering/
|- infra/
|  \- README.md              # Future AWS notes only
|- .env.example
|- AGENTS.md
|- PLAN.md
\- README.md
```

## Implementation Phases

### Phase 1 - Documentation And Contract Foundation

1. Confirm naming: SautiRelay for product text and `sautirelay` for repo identifiers.
2. Add product, architecture, user-flow, and component documentation under `docs/product/`.
3. Add backend-design, local-dev, and API-contract documentation under `docs/`.
4. Add canonical engineering standards under `docs/engineering/`.
5. Add project-local Cursor adapters under `.cursor/rules/` and document the standards entrypoint in `docs/development-rules.md`.
6. Add `infra/README.md` with future AWS architecture notes and an explicit "no deployment code yet" boundary.
7. Add `backend/app/openapi.yaml` with `GET /status` and `POST /relay` as the initial contract.
8. Add `.env.example` for local-only defaults.
9. Keep `uv.lock` trackable once generated.

### Phase 2 - Backend Foundation

1. Add `backend/pyproject.toml` with minimal FastAPI, Uvicorn, Pydantic, pytest, and httpx dependencies.
2. Move FastAPI app construction into `backend/app/`.
3. Add schemas for relay requests, relay responses, location hints, risk categories, urgency levels, and validation errors.
4. Add routers for `/status` and `/relay`.
5. Add a placeholder relay service that normalizes, classifies, redacts sensitive identity hints, and returns a deterministic route recommendation.
6. Add backend tests for health checks, successful relay submission, validation errors, and no precise-location default behavior.

### Phase 3 - Frontend Foundation

1. Upgrade the frontend package metadata to Svelte 5 and compatible Vite tooling.
2. Add Svelte 5 entry files under `frontend/src/`.
3. Use runes only: `$state`, `$derived`, `$props`, `$effect` for side effects, and `$effect.pre` where needed.
4. Do not use `export let`, legacy `on:` event directives, or Svelte stores unless explicitly documented as an exception.
5. Use CSS Modules for component styling with `Component.module.css`; avoid `<style>` blocks, Tailwind, and global CSS except tokens.
6. Keep non-trivial business logic out of `.svelte` files in `*.functions.ts`; put helpers in `*.utils.ts`.
7. Generate a TypeScript API client from `backend/app/openapi.yaml` into `frontend/src/api/`.
8. Build the report submission form with category, description, location option, consent state, urgency hint, and contact opt-in fields.
9. Add loading, success, validation-error, and backend-unavailable states.
10. Add accessibility-focused labels, error summaries, and keyboard-friendly submission flow.
11. Add frontend tests with Vitest and Svelte Testing Library once the component structure exists.

### Phase 4 - Local Docker Workflow

1. Add frontend and backend Dockerfiles under `docker/`.
2. Correct `docker/docker-compose.yml` build contexts so they resolve from the repository root.
3. Wire frontend to the backend through an environment variable such as `VITE_API_BASE_URL=http://localhost:8000`.
4. Verify local startup with:

```powershell
docker compose -f docker/docker-compose.yml up
```

### Phase 5 - Quality Gates

1. Backend: run `uv sync`, `uv run pytest`, and coverage checks when configured.
2. Frontend: run `pnpm install`, `pnpm lint`, `svelte-check`, TypeScript checks, and `pnpm test` when configured.
3. Contract: regenerate the TypeScript client every time `backend/app/openapi.yaml` changes.
4. Integration: use Docker Compose after meaningful cross-service changes.
5. Documentation: keep `README.md`, `PLAN.md`, `AGENTS.md`, `docs/engineering/`, `.cursor/rules/`, and `docs/development-rules.md` synchronized with the actual tree and project standards.

### Phase 6 - Future Expansion

1. Add persistence for relay records after the local stateless flow is validated.
2. Add responder dashboards, triage queues, audit trails, and escalation status updates.
3. Add low-bandwidth channels such as SMS, USSD, WhatsApp, or offline-first mobile capture.
4. Add provider-backed AI classification and redaction only after privacy and safety rules are documented.
5. Add AWS deployment code only when explicitly requested.

## Core User Flow

1. Reporter opens SautiRelay and chooses to submit a community signal.
2. Reporter enters what happened, where it is relevant, and how urgent it feels.
3. Reporter chooses whether to share approximate location, manual location, or no location.
4. Backend validates the report and produces a relay package with a category, urgency, anonymized summary, safety notes, and recommended responder route.
5. UI shows the relay result and next-step status without exposing private reporter details.

## OpenAPI Contract

`backend/app/openapi.yaml` is the source of truth for frontend/backend communication.

Initial endpoints:

- `GET /status`: health check for local dev and Docker Compose validation.
- `POST /relay`: accepts a report payload and returns a structured relay package.

Any contract change must be reflected in generated frontend API code and in `docs/api-contract.md`.

## Validation Plan

- Validate the live tree against this plan before marking scaffold work complete.
- Prefer targeted checks first, then broader validation.
- Report exact command failures and missing prerequisites.
- Do not create commits, branches, deployment scripts, or unrelated refactors unless explicitly requested.

## Assumptions

- Frontend package manager: `pnpm`.
- Backend package and execution workflow: `uv`.
- Container runtime: Docker Compose.
- Local ports: frontend `5173`, backend `8000`.
- Future AWS shape: S3 + CloudFront for frontend, Lambda + API Gateway for backend, and managed storage when persistence is introduced.
