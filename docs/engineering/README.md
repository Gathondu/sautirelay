# Engineering Standards

This directory is the source of truth for SautiRelay engineering rules.

Editor-specific files, including `.cursor/rules/*.mdc`, should point here instead of duplicating the full standards. If a standard changes, update the relevant document in this directory first, then update any adapter files only when their routing instructions need to change.

## Standards Index

- [Principles](principles.md): durable team norms and decision rules.
- [Architecture](architecture.md): repository boundaries and service ownership.
- [Local Development](local-development.md): prerequisites, run commands, Docker workflow, and troubleshooting.
- [Coding Standards](coding-standards.md): cross-language implementation rules.
- [Frontend Svelte](frontend-svelte.md): Svelte 5, Vite, TypeScript, CSS Modules, and pnpm rules.
- [Backend Python](backend-python.md): Python, FastAPI, and uv rules.
- [API Conventions](api-conventions.md): OpenAPI and frontend/backend contract rules.
- [Testing](testing.md): backend, frontend, contract, and integration validation.
- [Security](security.md): privacy, secrets, input validation, and AI safety.
- [Design System](design-system.md): UI styling and component design standards.
- [AI Development](ai-development.md): expectations for AI assistants and coding agents.

## Layering Model

1. `docs/engineering/` is canonical and reviewable in pull requests.
2. `AGENTS.md` is the portable entrypoint for AI coding tools and contributors.
3. `.cursor/rules/` is a Cursor adapter that points back to these docs.
4. Skills and workflow automations are deferred until later.

## Project Defaults

- Frontend: Svelte 5 with Vite.
- Frontend package manager: `pnpm`.
- Frontend styling: CSS Modules.
- Backend: FastAPI.
- Backend dependency and execution tool: `uv`.
- Contract: `backend/app/openapi.yaml`.
- Deployment: local-first; AWS deployment code is deferred.

Product context lives separately in [../product/README.md](../product/README.md). The root docs table of contents lives in [../README.md](../README.md).
