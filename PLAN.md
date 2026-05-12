# Project Plan - sautirelay (formerly umojasignal)

## Summary

Build a locally runnable Svelte + FastAPI application named **sautirelay**. The repo is organized for a future AWS deployment using S3 + CloudFront for the frontend and Lambda + API Gateway for the backend, but current work focuses on local development and testing only.

## Repository Layout

```text
sautirelay/
|- frontend/          # Svelte (Vite) UI, managed with pnpm
|  |- src/
|  |- static/
|  |- tests/
|  |- package.json
|  \- vite.config.ts
|- backend/           # FastAPI service, run with uv
|  |- app/
|  |  |- routers/
|  |  \- schemas/
|  |- tests/
|  \- main.py
|- docker/            # Dockerfiles and compose for local dev
|  \- docker-compose.yml
|- docs/              # Documentation and future-deployment notes
|- PLAN.md
\- AGENTS.md
```

## Implementation Steps

1. **Initialize projects** - use `pnpm` for the frontend and `uv` for the backend dependency and run workflow.
2. **Define OpenAPI contract** - add `backend/app/openapi.yaml` describing `/relay` and `/status` endpoints.
3. **Generate TypeScript client** - use pnpm tooling to create a client under `frontend/src/api/`.
4. **Implement FastAPI backend** - add `POST /relay` with Pydantic validation and a `GET /status` health check.
5. **Build Svelte UI** - create a simple form that submits payloads and displays responses.
6. **Dockerize locally** - add frontend and backend Dockerfiles plus a compose file for local startup.
7. **Unit testing** - use PyTest + `httpx` for backend tests and Vitest + `@testing-library/svelte` for frontend tests.
8. **CI pipeline** - add GitHub Actions for linting, unit tests, and Docker builds.
9. **Documentation** - update `README.md` and add an AWS architecture diagram under `docs/`.
10. **Future deployment placeholders** - add `infra/README.md` describing the planned AWS resources.

## Test Plan

- Backend: verify request validation, error handling, and placeholder relay logic with PyTest.
- Frontend: test component rendering, form submission, and client-side error handling with Vitest.
- All tests must pass on every PR, with a target of at least 80% coverage.

## Assumptions And Defaults

- **Deployment**: Production will use AWS with S3 + CloudFront and Lambda + API Gateway. No deployment code is added yet.
- **Package managers**: Frontend uses `pnpm`; backend uses `uv` for execution and dependency locking.
- **Environment variables**: `AWS_REGION`, `FRONTEND_BUCKET`, and `LAMBDA_FUNCTION_NAME` will be injected at deployment time; local defaults can live in `.env.example`.
- **Linting**: Prettier for frontend and Ruff or Black for backend.
- **Container runtime**: Docker Compose runs services locally on ports `5173` and `8000`.
