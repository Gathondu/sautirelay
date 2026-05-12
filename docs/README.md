# Documentation

This folder is organized into two documentation areas:

- [Product documentation](product/README.md): product intent, user flows, architecture, and app-level behavior.
- [Engineering standards](engineering/README.md): implementation rules, architecture boundaries, local development workflow, testing, and security.

Use the README in each folder as the detailed table of contents for that area.

## Structure

```text
docs/
|- README.md
|- product/
|  \- README.md
\- engineering/
   \- README.md
```

## Maintenance Rules

- Keep product-facing context under `docs/product/`.
- Keep implementation standards and workflows under `docs/engineering/`.
- Do not add standalone markdown files at the root of `docs/` unless this index needs to change.
- When consolidating or replacing docs, update the relevant folder README so the table of contents stays accurate.
