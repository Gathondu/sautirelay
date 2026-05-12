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

The initial relay request should support:

- Report description.
- Optional category hint.
- Optional urgency hint.
- Location mode.
- Manual location text or approximate location data when consent exists.
- Optional follow-up preference in later phases.

## Response Rules

- Return stable response shapes.
- Include structured error fields.
- Do not leak internal exception details.
- Do not include sensitive reporter details in relay responses.

The initial relay response should include:

- Relay ID.
- Status.
- Category.
- Urgency.
- Anonymized summary.
- Safety notes.
- Recommended route.
- Location confidence.

## Error Shape

Document API errors with a consistent JSON structure such as:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Report description is required.",
  "field": "description"
}
```

## Compatibility

- Additive optional response fields are acceptable.
- New required request fields are breaking changes and require coordinated frontend updates.
- Field removals and renames are breaking changes.

## Generated Client

Generated client code belongs in `frontend/src/api/`. Do not hand-edit generated files.

The exact generator can be selected during implementation, but the generated output must stay under `frontend/src/api/`.
