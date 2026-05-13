<script lang="ts">
  import { page } from '$app/state';
  import { changeLocale, currentLocale, currentTextDirection, localeOptions } from '../../lib/i18n';
  import * as m from '../../lib/paraglide/messages';
  import styles from './AppLayout.module.css';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  let selectedLocale = $state(currentLocale());

  const primaryRoutes = [
    { label: m.nav_report, href: '/' },
    { label: m.nav_status, href: '/status' },
    { label: m.nav_verifier, href: '/verifier' },
    { label: m.nav_mediator, href: '/mediator' },
    { label: m.nav_analytics, href: '/analytics' },
    { label: m.nav_docs, href: '/docs' },
  ];

  function isActive(href: string): boolean {
    if (href === '/') return page.url.pathname === '/';
    return page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
  }

  function handleLocaleChange(event: Event): void {
    const select = event.currentTarget as HTMLSelectElement;
    selectedLocale = select.value as typeof selectedLocale;
    changeLocale(select.value);
  }

  $effect(() => {
    document.documentElement.dataset.sautirelayHydrated = 'true';
  });
</script>

<div class={styles.appShell} dir={currentTextDirection()}>
  <header class={styles.topbar}>
    <a class={styles.brand} href="/">SautiRelay</a>

    <nav class={styles.nav} aria-label={m.nav_label()}>
      {#each primaryRoutes as route (route.href)}
        <a
          class={`${styles.navLink} ${isActive(route.href) ? styles.navLinkActive : ''}`}
          href={route.href}
          aria-current={isActive(route.href) ? 'page' : undefined}
        >
          {route.label()}
        </a>
      {/each}
    </nav>

    <label class={styles.languageControl}>
      <span>{m.language_selector_label()}</span>
      <select bind:value={selectedLocale} oninput={handleLocaleChange} onchange={handleLocaleChange}>
        {#each localeOptions as option (option.value)}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    </label>
  </header>

  {@render children()}
</div>
