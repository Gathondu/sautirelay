# Testing Standards

## Test Strategy

Prefer targeted checks first, then broader validation.

## Backend

Use pytest. Cover:

- Health check behavior.
- Valid report submission.
- Validation failures.
- Privacy redaction.
- Location consent and generalization.
- Service-level report classification and route recommendation.

Run with:

```powershell
uv run pytest
```

## Frontend

Use Vitest for unit and component tests. Use Svelte Testing Library or the Svelte testing APIs where appropriate.

Cover:

- Form rendering.
- Required fields and validation feedback.
- Loading, success, and failure states.
- API client integration seams.
- Accessibility-critical labels, focus behavior, and error summaries.

Run with:

```powershell
pnpm test
pnpm exec svelte-check
```

## Contract

When `backend/app/openapi.yaml` changes:

- Validate the YAML.
- Regenerate the frontend client.
- Confirm frontend imports still compile.
- Add or update tests for changed payloads.

## Docker

After meaningful cross-service changes, validate local startup with:

```powershell
docker compose -f docker/docker-compose.yml up
```

If Dockerfiles are not implemented yet, report that Compose cannot be fully validated.

## Reporting Failures

When a command fails, report:

- Exact command.
- Key error text.
- Missing prerequisite, if any.
- Whether the failure is related to the current change.
