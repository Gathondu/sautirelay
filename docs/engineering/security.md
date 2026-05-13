# Security And Privacy Standards

## Privacy First

SautiRelay handles sensitive community reports. Collect only what is needed to route and review a signal safely.

## Reporter Safety

- Do not require reporter identity.
- Do not expose optional contact details in report summaries.
- Do not store precise coordinates by default.
- Generalize location before report or display.
- Redact obvious names, phone numbers, emails, and sensitive identifiers before responder handoff.

## Secrets

- Do not commit secrets.
- Use `.env.example` for local defaults and placeholders.
- Keep real values in local environment files or managed secret stores when deployment exists.

## Input Validation

- Treat all user input as untrusted.
- Validate request payloads with Pydantic.
- Sanitize output that may be routed to humans or external systems.

## AI Safety

Provider-backed AI is future work. When introduced:

- Never trust model output as authoritative.
- Validate and constrain model output with schemas.
- Keep human review in the escalation path for sensitive reports.
- Do not send unnecessary personal data to model providers.
- Log AI decisions only after privacy review.

## Error Handling

- Do not leak stack traces or internal paths to API clients.
- Return structured, safe error messages.
- Log enough context for debugging without storing sensitive report content unnecessarily.
