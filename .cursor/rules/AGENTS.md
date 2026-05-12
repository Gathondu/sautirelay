# SautiRelay Cursor Rule Hub

## Purpose

This directory adapts the repository's canonical engineering standards for Cursor.

The source of truth is `docs/engineering/`. Do not treat `.cursor/rules/*.mdc` as independent standards.

## Required Reading

Before applying workflow-specific rules, read:

- `docs/engineering/README.md`
- `docs/engineering/principles.md`
- `AGENTS.md`

Then read the workflow-specific docs listed in the relevant `.mdc` file.

## Workflow Selection

- Frontend work: use `svelte.mdc`.
- Backend Python and FastAPI work: use `python.mdc`, `fastapi.mdc`, and `uv.mdc`.
- API contract work: use `fastapi.mdc` plus `docs/engineering/api-conventions.md`.
- FastMCP work: use `fastmcp.mdc` only if MCP tooling is introduced.

## Project Defaults

- Frontend: Svelte 5 with Vite.
- Frontend package manager: `pnpm`.
- Styling: CSS Modules.
- Backend: FastAPI with `uv`.
- API contract: `backend/app/openapi.yaml`.
- Skills: intentionally deferred until later.
