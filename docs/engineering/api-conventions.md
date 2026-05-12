# API Conventions

## Contract Source

`backend/app/openapi.yaml` is the source of truth for frontend/backend communication.

## Initial Endpoints

- `GET /status`
- `POST /relay`

Do not add backend endpoints that are not represented in the OpenAPI contract.

## Change Workflow

1. Update `backend/app/openapi.yaml`.
2. Update backend Pydantic schemas.
3. Update FastAPI route behavior.
4. Regenerate frontend API client code under `frontend/src/api/`.
5. Update frontend usage.
6. Update tests and docs.

## Request Rules

- Validate all input.
- Avoid requiring reporter identity.
- Do not require precise location.
- Keep consent fields explicit when location or follow-up contact is involved.

## Response Rules

- Return stable response shapes.
- Include structured error fields.
- Do not leak internal exception details.
- Do not include sensitive reporter details in relay responses.

## Compatibility

- Additive optional response fields are acceptable.
- New required request fields are breaking changes and require coordinated frontend updates.
- Field removals and renames are breaking changes.

## Generated Client

Generated client code belongs in `frontend/src/api/`. Do not hand-edit generated files.
