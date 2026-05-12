# Engineering Principles

## Source Of Truth

Engineering standards live in `docs/engineering/`. Tool-specific files should reference these standards rather than becoming independent rule sets.

## Local First

Current implementation is local-first. Do not add AWS deployment scripts, infrastructure-as-code, or production deployment workflows until explicitly requested.

## Contract First

Frontend and backend communicate only through the OpenAPI contract at `backend/app/openapi.yaml`.

When the contract changes:

1. Update `backend/app/openapi.yaml`.
2. Update backend schemas and routes.
3. Regenerate the frontend API client.
4. Update tests and documentation.

## Minimal Dependencies

Add dependencies only when they solve a clear project need. Prefer existing stack choices:

- Frontend: `pnpm`.
- Backend: `uv`.
- API: FastAPI and Pydantic.
- Frontend framework: Svelte 5 with Vite.

## Workflow Segregation

Use the rules for the workflow you are actually changing:

- Svelte rules for frontend code.
- Python, FastAPI, and uv rules for backend code.
- API conventions for cross-service contract changes.
- Security rules for any data, privacy, auth, or AI-related work.

Do not apply Python-only rules to Svelte files or Svelte-only rules to Python files.

## Documentation Discipline

If implementation changes the project shape, update the relevant docs in the same change. Keep `PLAN.md`, `README.md`, `AGENTS.md`, `.cursor/rules/`, and `docs/engineering/` aligned.

## Public Repository Assumption

Assume every contributor can read only this repository. Do not depend on user-local files, private Cursor rules, local memory, or machine-specific paths for project standards.
