<script lang="ts">
  import { checkReportStatus } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
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
        status: response.safeStatus ?? response.status ?? m.status_fallback(),
        message: response.message,
      };
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : m.status_error();
    } finally {
      isChecking = false;
    }
  }
</script>

<svelte:head>
  <title>{m.status_page_title()} | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>{m.status_heading()}</h1>
      <p>{m.status_intro()}</p>
    </div>
  </header>

  <section class={styles.panel}>
    <div class={styles.toolbar}>
      <input bind:value={trackingCode} placeholder={m.status_placeholder()} />
      <button class={styles.button} type="button" disabled={isChecking || !trackingCode.trim()} onclick={handleCheck}>
        {isChecking ? m.status_checking_button() : m.status_check_button()}
      </button>
    </div>

    {#if errorMessage}
      <p class={styles.error} role="alert">{errorMessage}</p>
    {/if}

    {#if result}
      <article class={styles.card} role="status">
        <h2>{result.status}</h2>
        <p class={styles.muted}>{result.message ?? m.status_no_sensitive_details()}</p>
      </article>
    {/if}
  </section>
</main>
