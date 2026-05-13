<script lang="ts">
  import { getMetrics, login, type DashboardMetrics } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let errorMessage = $state('');
  let metrics = $state<DashboardMetrics | null>(null);

  async function loadMetrics(): Promise<void> {
    isLoading = true;
    errorMessage = '';

    try {
      const auth = await login('verifier@sautirelay.dev', 'verifier-dev-pass');
      metrics = await getMetrics(auth.accessToken);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : m.analytics_error_load();
    } finally {
      isLoading = false;
    }
  }

  const reportsByCategory = $derived(metrics?.reportsByCategory ?? metrics?.reports_by_category ?? []);
  const riskLevels = $derived(metrics?.riskLevels ?? metrics?.risk_levels ?? []);
</script>

<svelte:head>
  <title>{m.analytics_page_title()} | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>{m.analytics_heading()}</h1>
      <p>{m.analytics_intro()}</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadMetrics}>
      {isLoading ? m.analytics_loading_button() : m.analytics_load_button()}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  {#if metrics}
    <section class={styles.grid} aria-label={m.analytics_metrics_label()}>
      <article class={styles.card}>
        <h2>{m.analytics_total_reports()}</h2>
        <p class={styles.pill}>{metrics.totalReports ?? metrics.total_reports ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>{m.analytics_active_clusters()}</h2>
        <p class={styles.pill}>{metrics.activeClusters ?? metrics.active_clusters ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>{m.analytics_escalated_signals()}</h2>
        <p class={styles.pill}>{metrics.escalatedSignals ?? metrics.escalated_signals ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>{m.analytics_resolved_signals()}</h2>
        <p class={styles.pill}>{metrics.resolvedSignals ?? metrics.resolved_signals ?? 0}</p>
      </article>
    </section>

    <section class={styles.grid} aria-label={m.analytics_breakdowns_label()}>
      {#each reportsByCategory as item (item.label)}
        <article class={styles.card}>
          <h2>{item.label}</h2>
          <p class={styles.pill}>{m.analytics_reports_unit({ count: item.count })}</p>
        </article>
      {/each}

      {#each riskLevels as item (item.label)}
        <article class={styles.card}>
          <h2>{item.label}</h2>
          <p class={styles.pill}>{m.analytics_signals_unit({ count: item.count })}</p>
        </article>
      {/each}
    </section>
  {/if}
</main>
