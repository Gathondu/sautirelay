# SautiRelay Frontend Wiring Plan

## Current Backend Baseline

- Local `main` is the active branch in this workspace. No git remote is configured, so there is no upstream `main` to fetch or compare.
- The backend now exposes the SautiRelay product API under `backend/app/routers/` with `/reports`, `/clusters`, `/escalations`, `/auth/login`, `/dashboard/metrics`, and `/status`.
- `backend/app/openapi.yaml` describes the intended contract, but a few live router responses still differ from that contract. For example, the OpenAPI contract describes `GET /escalations` as `{ items, total }`, while the current router returns a raw escalation list. The frontend API adapter should tolerate those current shapes until backend contract alignment is complete.

## Frontend Architecture

- Use SvelteKit file-based routes instead of the previous Vite-only hash router.
- Keep Svelte 5 runes and event attributes.
- Use CSS Modules for page and layout styles. Do not introduce Tailwind.
- Keep the frontend as a separate client for the FastAPI backend; do not add SvelteKit server API routes for product workflow calls unless a later security requirement needs a proxy.
- Use `PUBLIC_API_URL` for the backend base URL, defaulting locally to `http://localhost:8000`.

## Route Map

- `/`: anonymous reporter flow with safety notice, language selection, category, text details, timeframe, immediate-danger flag, approximate location, consent, and safe submission confirmation.
- `/status`: anonymous tracking-code lookup through `GET /reports/status/{trackingCode}`.
- `/verifier`: seeded verifier dashboard that logs in as the local verifier and reads `/reports` and `/clusters`.
- `/mediator`: seeded mediator dashboard that logs in as the local mediator and reads `/escalations`.
- `/analytics`: privacy-safe aggregate metrics from `/dashboard/metrics`.
- `/docs`: existing in-app documentation browser.
- `/docs/[...docId]`: direct links to individual product and engineering docs.

## API Wiring Sequence

1. Add a small typed API adapter in `frontend/src/lib/api/sautirelay.ts`.
2. Wire anonymous report submission first because it is public and demonstrates the start of the capstone journey.
3. Wire tracking-code lookup second to close the reporter feedback loop.
4. Wire seeded verifier and mediator views through `/auth/login` using local demo credentials only: `verifier@sautirelay.dev` / `verifier-dev-pass` and `mediator@sautirelay.dev` / `mediator-dev-pass`.
5. Wire analytics last and keep all displayed metrics aggregate-only.
6. When the backend OpenAPI and live routers are fully aligned, replace tolerant response normalization with generated OpenAPI types.

## Follow-Up Integration Work

- Add generated TypeScript client output under `frontend/src/api/` once the backend contract stabilizes.
- Add frontend tests for report submission, status lookup, role-gated dashboard loading, and analytics rendering.
- Add route-level loading and empty states for seeded demo data.
- Add mediator actions for accepting escalations and recording outcomes.
- Add verifier actions for processing reports, verifying clusters, and escalating to mediators.
- Keep real SMS, WhatsApp, voice upload, production auth, and AWS deployment out of the MVP frontend pass.
