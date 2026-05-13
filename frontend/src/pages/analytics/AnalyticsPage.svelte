<script lang="ts">
  import { getMetrics, login, type DashboardMetrics } from '../../lib/api/sautirelay';
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
      errorMessage = error instanceof Error ? error.message : 'Unable to load analytics.';
    } finally {
      isLoading = false;
    }
  }

  const reportsByCategory = $derived(metrics?.reportsByCategory ?? metrics?.reports_by_category ?? []);
  const riskLevels = $derived(metrics?.riskLevels ?? metrics?.risk_levels ?? []);
</script>

<svelte:head>
  <title>Analytics | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>Privacy-safe analytics</h1>
      <p>Aggregate trends only. No raw reports, exact coordinates, or public allegations.</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadMetrics}>
      {isLoading ? 'Loading...' : 'Load metrics'}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  {#if metrics}
    <section class={styles.grid} aria-label="Dashboard metrics">
      <article class={styles.card}>
        <h2>Total reports</h2>
        <p class={styles.pill}>{metrics.totalReports ?? metrics.total_reports ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>Active clusters</h2>
        <p class={styles.pill}>{metrics.activeClusters ?? metrics.active_clusters ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>Escalated signals</h2>
        <p class={styles.pill}>{metrics.escalatedSignals ?? metrics.escalated_signals ?? 0}</p>
      </article>
      <article class={styles.card}>
        <h2>Resolved signals</h2>
        <p class={styles.pill}>{metrics.resolvedSignals ?? metrics.resolved_signals ?? 0}</p>
      </article>
    </section>

    <section class={styles.grid} aria-label="Metric breakdowns">
      {#each reportsByCategory as item (item.label)}
        <article class={styles.card}>
          <h2>{item.label}</h2>
          <p class={styles.pill}>{item.count} reports</p>
        </article>
      {/each}

      {#each riskLevels as item (item.label)}
        <article class={styles.card}>
          <h2>{item.label}</h2>
          <p class={styles.pill}>{item.count} signals</p>
        </article>
      {/each}
    </section>
  {/if}
</main>
