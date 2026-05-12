# SautiRelay Backend Design

## Goals

- Keep backend behavior deterministic for the MVP.
- Align runtime schemas with `backend/app/openapi.yaml`.
- Protect sensitive reporter details by default.
- Keep dependencies minimal and managed with `uv`.

## Proposed Layout

```text
backend/
|- app/
|  |- __init__.py
|  |- main.py
|  |- openapi.yaml
|  |- routers/
|  |  |- __init__.py
|  |  |- relay.py
|  |  \- status.py
|  |- schemas/
|  |  |- __init__.py
|  |  \- relay.py
|  \- services/
|     |- __init__.py
|     |- privacy.py
|     \- relay.py
|- tests/
|- main.py
\- pyproject.toml
```

`backend/main.py` can remain the local entrypoint, importing the app from `backend/app/main.py`.

## Relay Request

The backend accepts:

- Report description.
- Optional category hint.
- Optional urgency hint.
- Location mode.
- Manual location text or approximate location data when consent exists.
- Optional follow-up preference in future phases.

## Relay Response

The backend returns:

- Relay ID.
- Status.
- Category.
- Urgency.
- Anonymized summary.
- Safety notes.
- Recommended route.
- Location confidence.

## Privacy Handling

- Remove phone numbers, emails, and obvious personal identifiers from relay summaries.
- Generalize location before returning or storing it.
- Do not require reporter identity.
- Treat optional contact details as future work requiring separate privacy review.

## Error Model

Use consistent JSON errors with:

- `code`
- `message`
- `field` when applicable
- `details` when helpful

## Tests

Use `pytest` and `httpx` for API tests. Cover success, validation failure, missing description, unsupported location mode, and health check behavior.
