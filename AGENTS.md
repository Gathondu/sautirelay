# Agent Instructions - sautirelay

## Scope

All files under the repository root (`c:\Users\dng\Development\sautirelay`) and its sub-directories.

## General Rules

- Follow the repository layout defined in `PLAN.md`.
- Frontend and backend must communicate only via the OpenAPI contract at `backend/app/openapi.yaml`.
- All changes must keep the local Docker Compose setup functional and should be verified with `docker compose up` after meaningful modifications.
- Do not write AWS deployment scripts yet. Keep only placeholders and documentation for future deployment work.

## Frontend Agent

- Use `pnpm` for all package operations.
- Add UI components under `frontend/src/`.
- When the OpenAPI spec changes, regenerate the TypeScript client and update imports.
- Run `pnpm lint` and `pnpm test` when those scripts exist.
- Keep formatting consistent with Prettier.

## Backend Agent

- Run the service with `uv` using `uv run backend/main.py` or the equivalent project entry command.
- Install and lock dependencies with `uv sync` and `uv lock`; keep `uv.lock` current once it exists.
- Implement routers, schemas, and core logic inside `backend/app/`.
- Run `pytest` when tests are present and keep coverage at or above 80 percent.
- Keep dependency declarations minimal and aligned with the lock file.

## Docker And Infrastructure Agent

- Maintain Docker assets under `docker/`.
- Ensure `docker/docker-compose.yml` wires the frontend and backend for local development.
- Keep future CI and infrastructure changes aligned with the plan and local-first workflow.

## Documentation Agent

- Keep `README.md` current with local development steps.
- Add AWS architecture notes under `docs/` and `infra/` when those files are created.
- Ensure plan and agent documentation stay synchronized with actual repository structure.

## Review And Integration Agent

- Verify the folder structure matches `PLAN.md`.
- Check naming consistency across directories and entry files.
- Ensure files referenced in the plan actually exist before marking scaffold work complete.
- Summarize what was created, what is missing, and any follow-up work.

## Validation Rules

- Prefer targeted checks first, then broader validation.
- Do not fix unrelated issues while validating current work.
- Report exact command failures and the missing prerequisite when a tool is unavailable.
- Do not create commits or branches unless explicitly asked.

## Boundaries

- Work only inside this repository.
- Use official OpenAI documentation sources for OpenAI-related questions.
- Do not rename, move, or delete unrelated files.
