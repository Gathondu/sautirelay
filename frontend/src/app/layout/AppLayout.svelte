<script lang="ts">
  import { page } from '$app/state';
  import styles from './AppLayout.module.css';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();

  const primaryRoutes = [
    { label: 'Report', href: '/' },
    { label: 'Check status', href: '/status' },
    { label: 'Verifier', href: '/verifier' },
    { label: 'Mediator', href: '/mediator' },
    { label: 'Analytics', href: '/analytics' },
    { label: 'Docs', href: '/docs' },
  ];

  function isActive(href: string): boolean {
    if (href === '/') return page.url.pathname === '/';
    return page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
  }
</script>

<div class={styles.appShell}>
  <header class={styles.topbar}>
    <a class={styles.brand} href="/">SautiRelay</a>

    <nav class={styles.nav} aria-label="Primary navigation">
      {#each primaryRoutes as route (route.href)}
        <a
          class={`${styles.navLink} ${isActive(route.href) ? styles.navLinkActive : ''}`}
          href={route.href}
          aria-current={isActive(route.href) ? 'page' : undefined}
        >
          {route.label}
        </a>
      {/each}
    </nav>
  </header>

  {@render children()}
</div>
