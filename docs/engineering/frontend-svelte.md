# Frontend Svelte Standards

## Stack

- Svelte 5 with SvelteKit and Vite.
- TypeScript for frontend logic.
- CSS Modules for styling.
- `pnpm` for package operations.

The current frontend uses SvelteKit file-based routes with a separate FastAPI backend. Do not add SvelteKit server API routes for product workflow calls unless a later security requirement needs a proxy.

## Package Commands

Use `pnpm` only:

```powershell
pnpm install
pnpm dev
pnpm test
pnpm lint
pnpm exec svelte-check
```

Do not add `npm`, `yarn`, or mixed lockfiles.

## Svelte 5 Runes

Use Svelte 5 runes:

- `$state()` for local reactive state.
- `$derived()` or `$derived.by()` for computed values.
- `$props()` for component props.
- `$effect()` only for side effects.
- `$effect.pre()` only when pre-DOM-update behavior is required.

Do not use:

- `export let`.
- Legacy `on:` event directives.
- Svelte stores unless a written exception explains why runes are insufficient.
- `$effect` for derived state.

## Event Handling

Use event attributes:

```svelte
<button onclick={submitReport}>Submit</button>
```

Do not use legacy event directives:

```svelte
<!-- Do not use -->
<button on:click={submitReport}>Submit</button>
```

## Component Structure

Keep `.svelte` files focused on:

- State wiring.
- Event binding.
- Rendering.
- Accessibility attributes.

Move non-trivial logic to:

- `*.functions.ts` for business logic.
- `*.utils.ts` for reusable helpers.

## Styling

Use CSS Modules:

```svelte
<script lang="ts">
  import styles from './RelayForm.module.css';
</script>

<form class={styles.form}></form>
```

Avoid:

- `<style>` blocks in `.svelte` files.
- Tailwind or utility CSS frameworks.
- Hardcoded repeated colors, spacing, or typography.

Use shared CSS variables for tokens once a design token file exists.

## API Usage

Use generated API client code from `frontend/src/api/`. Do not hand-write fetch calls throughout components when a generated client exists.

Frontend configuration should use public SvelteKit/Vite env values such as `PUBLIC_API_URL`.

## Internationalization

- Use Paraglide for UI internationalization.
- Source messages live in `frontend/messages/`, with English as the base locale.
- Import message functions from `frontend/src/lib/paraglide/messages` and call them directly in Svelte components.
- Keep UI locale tags as BCP-47 codes such as `en`, `sw`, `fr`, `ar`, and `pt`.
- Keep report payload language values aligned with the backend contract; do not substitute UI locale codes unless the backend contract changes.
- Do not translate backend-returned operational data such as report statuses, risk levels, generated summaries, or enum values unless a local display mapping is intentionally added.

## Testing

Use Vitest for unit and component tests. Use Playwright for future end-to-end tests.

Test behavior:

- Rendering.
- Form validation feedback.
- Loading state.
- Success state.
- API failure state.
- Accessibility-critical labels and error summaries.

## Official References

These standards are aligned with Svelte 5 runes, TypeScript support, and testing guidance from the official Svelte documentation.
