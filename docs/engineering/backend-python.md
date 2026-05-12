# Backend Python Standards

## Stack

- Python backend.
- FastAPI for HTTP APIs.
- Pydantic for schemas.
- `uv` for dependency management, locking, and execution.
- pytest for tests.

## uv Workflow

Use `uv` only:

```powershell
uv sync
uv add <package>
uv lock
uv run backend/main.py
uv run pytest
```

Do not use `pip` directly for project dependency workflow. Commit `uv.lock` once it exists.

## Application Structure

Preferred backend structure:

```text
backend/
|- app/
|  |- routers/
|  |- schemas/
|  |- services/
|  |- core/
|  \- openapi.yaml
|- tests/
|- main.py
\- pyproject.toml
```

Add repositories only when persistence is introduced.

## Initial MVP Layout

The first implementation pass should keep the structure explicit:

- `backend/main.py` remains the local entrypoint.
- `backend/app/main.py` should create the FastAPI app.
- `backend/app/routers/status.py` should expose `GET /status`.
- `backend/app/routers/relay.py` should expose `POST /relay`.
- `backend/app/schemas/relay.py` should define relay request and response models.
- `backend/app/services/privacy.py` should hold redaction and location-generalization utilities.
- `backend/app/services/relay.py` should hold deterministic relay structuring logic.

## FastAPI Rules

- Keep route handlers thin.
- Use Pydantic request and response schemas.
- Keep business logic in services.
- Use proper HTTP status codes.
- Use `Depends()` for request-scoped dependencies when needed.
- Do not return inconsistent response shapes.

## Typing

- Add type hints to public functions.
- Avoid `Any` unless a boundary requires it and the reason is documented.
- Prefer explicit models over dynamic dictionaries.

## Privacy And Relay Logic

The backend is responsible for:

- Input validation.
- Report normalization.
- Privacy redaction.
- Location generalization.
- Category and urgency classification placeholders.
- Recommended route selection.

Keep MVP behavior deterministic until provider-backed AI is introduced intentionally.

## Tests

Use pytest and cover:

- `/status`.
- Valid relay submission.
- Invalid relay submission.
- Location consent behavior.
- Privacy redaction behavior.
- Contract alignment.
