<script lang="ts">
  import { listEscalations, login, type EscalationItem } from '../../lib/api/sautirelay';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let errorMessage = $state('');
  let escalations = $state<EscalationItem[]>([]);

  async function loadEscalations(): Promise<void> {
    isLoading = true;
    errorMessage = '';

    try {
      const auth = await login('mediator@sautirelay.dev', 'mediator-dev-pass');
      const response = await listEscalations(auth.accessToken);
      escalations = response.items;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load mediator assignments.';
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Mediator dashboard | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>Mediator dashboard</h1>
      <p>View anonymized action briefs assigned to trusted mediators.</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadEscalations}>
      {isLoading ? 'Loading...' : 'Load assignments'}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  <section class={styles.grid} aria-label="Mediator assignments">
    {#each escalations as escalation (escalation.escalationId ?? escalation.id)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{escalation.status}</span>
          <span class={styles.pill}>{escalation.urgency}</span>
        </div>
        <h2>{escalation.assignedTo ?? escalation.assigned_to ?? 'Mediator assignment'}</h2>
        <p class={styles.muted}>{escalation.actionBrief ?? escalation.action_brief ?? 'Action brief pending.'}</p>
      </article>
    {/each}
  </section>
</main>
