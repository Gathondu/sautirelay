<script lang="ts">
  import { primaryRoutes, routeHref } from '../../lib/router/routes';
  import styles from './AppLayout.module.css';
  import type { AppRoute } from '../../lib/router/routes';
  import type { Snippet } from 'svelte';

  let { currentRoute, children }: { currentRoute: AppRoute; children: Snippet } = $props();
</script>

<div class={styles.appShell}>
  <header class={styles.topbar}>
    <a class={styles.brand} href={routeHref({ name: 'docs' })}>SautiRelay</a>

    <nav class={styles.nav} aria-label="Primary navigation">
      {#each primaryRoutes as route (route.name)}
        <a
          class={`${styles.navLink} ${currentRoute.name === route.name ? styles.navLinkActive : ''}`}
          href={route.href}
          aria-current={currentRoute.name === route.name ? 'page' : undefined}
        >
          {route.label}
        </a>
      {/each}
    </nav>
  </header>

  {@render children()}
</div>
