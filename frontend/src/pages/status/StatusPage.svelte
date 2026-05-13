<script lang="ts">
  import { checkReportStatus } from '../../lib/api/sautirelay';
  import styles from '../operations.module.css';

  let trackingCode = $state('');
  let isChecking = $state(false);
  let errorMessage = $state('');
  let result = $state<{ status: string; message?: string } | null>(null);

  async function handleCheck(): Promise<void> {
    if (!trackingCode.trim()) return;

    isChecking = true;
    errorMessage = '';
    result = null;

    try {
      const response = await checkReportStatus(trackingCode);
      result = {
        status: response.safeStatus ?? response.status ?? 'Received',
        message: response.message,
      };
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to check this tracking code.';
    } finally {
      isChecking = false;
    }
  }
</script>

<svelte:head>
  <title>Check report | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>Check report status</h1>
      <p>Use the anonymous tracking code from your submission confirmation.</p>
    </div>
  </header>

  <section class={styles.panel}>
    <div class={styles.toolbar}>
      <input bind:value={trackingCode} placeholder="SR-8K42P" />
      <button class={styles.button} type="button" disabled={isChecking || !trackingCode.trim()} onclick={handleCheck}>
        {isChecking ? 'Checking...' : 'Check status'}
      </button>
    </div>

    {#if errorMessage}
      <p class={styles.error} role="alert">{errorMessage}</p>
    {/if}

    {#if result}
      <article class={styles.card} role="status">
        <h2>{result.status}</h2>
        <p class={styles.muted}>{result.message ?? 'No sensitive escalation details are shown in this view.'}</p>
      </article>
    {/if}
  </section>
</main>
