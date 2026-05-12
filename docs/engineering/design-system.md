# Design System Standards

## Product Tone

SautiRelay should feel calm, trustworthy, and practical. The UI should support sensitive reporting without visual noise or pressure.

## Styling

- Use CSS Modules for component styles.
- Use shared CSS variables for tokens once introduced.
- Avoid Tailwind and utility-first frameworks.
- Avoid one-off hardcoded repeated values.

## Components

Components should be small, focused, and accessible.

Expected initial components:

- App shell.
- Report form.
- Location mode selector.
- Consent section.
- Error summary.
- Report result.
- Service status indicator.

## Accessibility

- Every input needs a visible label or clear accessible name.
- Error messages should be associated with the relevant fields.
- Form-level errors should be keyboard reachable.
- Do not rely on color alone to communicate status.
- Preserve user-entered report text when network errors happen.

## Motion

- Keep motion minimal.
- Prefer opacity and transform.
- Respect reduced motion preferences when animations are introduced.

## Content

Use plain, careful language. Do not overpromise safety, anonymity, or responder action beyond what the system actually supports.
