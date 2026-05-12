# Coding Standards

## General

- Prefer simple, explicit code.
- Keep edits scoped to the requested behavior.
- Do not refactor unrelated code.
- Do not add abstractions unless they remove real complexity or match an established pattern.
- Keep naming consistent with existing files and docs.

## Type Safety

- Use TypeScript for frontend logic.
- Use typed Python for backend logic.
- Avoid `any` in TypeScript and `Any` in Python unless a boundary requires it and the reason is documented.

## Error Handling

- Validate inputs early.
- Use explicit error paths.
- Do not swallow exceptions silently.
- Return meaningful API errors without leaking internal details.

## State And Side Effects

- Keep business logic out of UI components.
- Keep side effects isolated and easy to test.
- Prefer pure functions for transformations, validation, classification, and formatting.

## Files And Naming

- Svelte components: `PascalCase.svelte`.
- CSS modules: `Component.module.css`.
- Frontend helpers: `kebab-case.utils.ts`.
- Frontend business logic: `kebab-case.functions.ts`.
- Python modules: `snake_case.py`.
- Tests should sit near the relevant application boundary or under the established `tests/` folder.

## Comments

Write comments only when they clarify non-obvious intent, privacy constraints, or safety-sensitive behavior.

## Generated Code

Generated API client code should be placed under `frontend/src/api/` and should not be hand-edited.
