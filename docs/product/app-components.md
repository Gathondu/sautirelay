# SautiRelay App Components

## Frontend Components

Use Svelte 5 component patterns only. The Svelte rules require runes, CSS Modules, TypeScript strictness, and small components with business logic extracted from `.svelte` files.

## Svelte 5 Rules

- Use `$state` for local reactive state.
- Use `$derived` or `$derived.by` for computed values.
- Use `$props` for component props; never use `export let`.
- Use `$effect` only for side effects, not derived state.
- Use event attributes such as `onclick`, not legacy `on:click`.
- Keep non-trivial logic in `*.functions.ts`.
- Keep reusable helpers in `*.utils.ts`.
- Style components with `Component.module.css` imported as `styles`.
- Avoid `<style>` blocks, Tailwind, and broad global CSS except shared tokens.

### App Shell

Owns the main layout, service status surface, and global error boundary.

### Relay Form

Captures the report description, category, urgency hint, location mode, manual location text, consent state, and optional follow-up preference. It should emit a typed payload that matches the generated API client.

### Location Picker

Owns location-mode selection and consent copy. It should support none, manual, and approximate modes without requiring browser geolocation.

### Relay Result

Displays the structured backend response: relay ID, category, urgency, anonymized summary, safety notes, recommended route, and status.

### Error Summary

Displays validation and network errors in a way that is visible, keyboard reachable, and associated with the affected fields.

### Service Status Indicator

Calls `GET /status` and displays whether the backend is reachable.

## Backend Components

### FastAPI App

Creates the application, registers routers, and configures CORS for local development.

### Status Router

Exposes `GET /status` for health checks.

### Relay Router

Exposes `POST /relay`, validates payloads, and returns structured relay responses.

### Schemas

Define request and response models aligned with `backend/app/openapi.yaml`.

### Relay Service

Normalizes submitted text, redacts sensitive hints, assigns category and urgency, and recommends a route. MVP behavior should be deterministic and testable.

### Privacy Utilities

Handle redaction and location generalization before a relay item leaves the backend.

## Test Expectations

- Component tests cover form rendering, validation display, submission loading state, success state, and backend failure state.
- Backend tests cover status, valid relay submission, invalid payloads, and location consent behavior.
- Contract changes require regenerated frontend API code.
- Svelte checks should include `svelte-check`, TypeScript strictness, Vitest behavior tests, and Playwright for future end-to-end coverage.
