# SautiRelay API Contract

## Source Of Truth

`backend/app/openapi.yaml` is the contract source of truth. The frontend must consume generated TypeScript client code derived from this file.

## Initial Endpoints

- `GET /status`: returns backend health and service name.
- `POST /relay`: accepts a report and returns a structured relay package.

## Contract Change Workflow

1. Update `backend/app/openapi.yaml`.
2. Update backend schemas and route behavior to match.
3. Regenerate the frontend API client under `frontend/src/api/`.
4. Update frontend imports and tests.
5. Update examples in docs if payloads changed.

## Compatibility Rules

- Additive response fields are allowed when optional.
- Required request fields require a coordinated frontend update.
- Rename or remove fields only in an explicit breaking-change phase.
- Keep example payloads realistic but free of real personal data.

## Error Shape

All documented API errors should include:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Report description is required.",
  "field": "description"
}
```

## Client Generation

The exact generator can be selected during implementation. The generated output should live under `frontend/src/api/` and should not be hand-edited.
