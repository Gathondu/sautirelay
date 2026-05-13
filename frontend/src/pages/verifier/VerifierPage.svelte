<script lang="ts">
  import { listClusters, listReports, login, type ClusterItem, type ReportItem } from '../../lib/api/sautirelay';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let errorMessage = $state('');
  let reports = $state<ReportItem[]>([]);
  let clusters = $state<ClusterItem[]>([]);

  async function loadVerifierQueue(): Promise<void> {
    isLoading = true;
    errorMessage = '';

    try {
      const auth = await login('verifier@sautirelay.dev', 'verifier-dev-pass');
      const [reportQueue, clusterQueue] = await Promise.all([listReports(auth.accessToken), listClusters(auth.accessToken)]);
      reports = reportQueue.items;
      clusters = clusterQueue.items;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load verifier queue.';
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Verifier dashboard | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>Verifier dashboard</h1>
      <p>Review redacted reports and clustered signals before mediator escalation.</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadVerifierQueue}>
      {isLoading ? 'Loading...' : 'Load seeded queue'}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  <section class={styles.grid} aria-label="Verifier queue">
    {#each reports as report (report.reportId ?? report.id ?? report.trackingCode)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{report.status}</span>
          <span class={styles.pill}>{report.riskLevel ?? report.risk_level ?? 'MEDIUM'}</span>
        </div>
        <h2>{report.category}</h2>
        <p class={styles.muted}>{report.summary ?? report.redactedText ?? report.translatedText ?? 'Report awaiting AI processing.'}</p>
      </article>
    {/each}

    {#each clusters as cluster (cluster.clusterId ?? cluster.id)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{cluster.status}</span>
          <span class={styles.pill}>{cluster.riskLevel ?? cluster.risk_level ?? 'MEDIUM'}</span>
          <span class={styles.pill}>{cluster.reportCount ?? cluster.report_count ?? 0} reports</span>
        </div>
        <h2>{cluster.title}</h2>
        <p class={styles.muted}>{cluster.summary}</p>
      </article>
    {/each}
  </section>
</main>
