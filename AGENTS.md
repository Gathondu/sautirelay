# Agent Instructions - sautirelay

## Scope

All files under the repository root (`c:\Users\dng\Development\sautirelay`) and its sub-directories.

## General Rules

- Follow the repository layout defined in `PLAN.md`.
- Frontend and backend must communicate only via the OpenAPI contract at `backend/app/openapi.yaml`.
- All changes must keep the local Docker Compose setup functional and should be verified with `docker compose up` after meaningful modifications.
- Do not write AWS deployment scripts yet. Keep only placeholders and documentation for future deployment work.

## Cursor Rules

- Treat `docs/engineering/` as the source of truth for engineering standards.
- Read the project-local Cursor rule hub at `.cursor/rules/AGENTS.md` only as an adapter when working in Cursor.
- Keep `.cursor/rules/*.mdc` thin. They should route agents to canonical docs, not duplicate full standards.
- Apply only the relevant rule set for the current workflow:
  - Svelte/frontend work: consult `svelte.mdc`; ignore Python-only rules except for cross-service integration context.
  - Python/FastAPI backend work: consult `python.mdc`, `fastapi.mdc`, and `uv.mdc`; ignore Svelte-only rules.
  - FastMCP work: consult `fastmcp.mdc` only when MCP tools or FastMCP backend code are introduced.
- Apply SvelteKit-specific guidance from `svelte.mdc` only if this project adopts SvelteKit; the current frontend plan is Svelte 5 with Vite and a separate FastAPI backend.
- Do not create skills yet. Skills are reserved for later repeatable workflows.
- If any Cursor rule conflicts with this repository's local-first boundary, keep the local-first boundary and document the conflict before changing implementation direction.

## Frontend Agent

- Use `pnpm` for all package operations.
- Use Svelte 5 strictly. Do not write Svelte 3/4 syntax.
- Use Svelte 5 runes: `$state`, `$derived`, `$props`, `$effect` only for side effects, and `$effect.pre` when a pre-effect is required.
- Do not use `export let`, `on:` event directives, or Svelte stores unless a documented exception is justified.
- Use CSS Modules for component styling: `Component.module.css` imported as `styles`, with `class={styles.name}`.
- Keep business logic out of `.svelte` files; place non-trivial logic in `*.functions.ts` and helpers in `*.utils.ts`.
- Add UI components under `frontend/src/`.
- When the OpenAPI spec changes, regenerate the TypeScript client and update imports.
- Run `pnpm lint`, `pnpm test`, `svelte-check`, and TypeScript checks when those scripts exist.
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
- Keep `docs/engineering/`, `.cursor/rules/`, `docs/development-rules.md`, `PLAN.md`, and `AGENTS.md` synchronized when project standards change.
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
