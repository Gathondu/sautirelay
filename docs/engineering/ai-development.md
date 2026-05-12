# AI Development Standards

## Purpose

These rules help AI coding assistants and human reviewers work safely in this repository.

## Entry Points

Agents should read:

1. `AGENTS.md`.
2. Relevant docs under `docs/engineering/`.
3. Relevant adapter files under `.cursor/rules/` if running inside Cursor.
4. Product docs under `docs/` when changing behavior or user flows.

## Do Not Depend On Local Machine Rules

All project standards must be available in the repository. Do not rely on a contributor's private Cursor rules, local memory, or machine-specific paths.

## Workflow Selection

- Frontend tasks: read `docs/engineering/frontend-svelte.md`, `design-system.md`, `testing.md`, and `security.md` when sensitive data is involved.
- Backend tasks: read `docs/engineering/backend-python.md`, `api-conventions.md`, `testing.md`, and `security.md`.
- Cross-service tasks: read `architecture.md`, `api-conventions.md`, and `testing.md`.
- Documentation tasks: read `principles.md` and keep indexes synchronized.

## Skills Boundary

Do not create skills yet. Skills are reserved for future repeatable workflows such as feature scaffolding, writing specs, or release processes. Current work should remain documentation and rules only.

## Agent Conduct

- Keep edits scoped.
- Do not create commits or branches unless requested.
- Do not add deployment code unless requested.
- Preserve existing user changes.
- Report validation commands and failures clearly.
