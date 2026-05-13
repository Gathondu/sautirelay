<script lang="ts">
  import {
    acceptEscalation,
    listEscalations,
    login,
    recordOutcome,
    type EscalationItem,
  } from '../../lib/api/sautirelay';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let isSubmitting = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');
  let escalations = $state<EscalationItem[]>([]);
  let mediatorToken = $state('');
  let outcomeNotesById = $state<Record<string, string>>({});

  async function loadEscalations(): Promise<void> {
    isLoading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const auth = await login('mediator@sautirelay.dev', 'mediator-dev-pass');
      mediatorToken = auth.accessToken;
      const response = await listEscalations(auth.accessToken);
      escalations = response.items;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load mediator assignments.';
    } finally {
      isLoading = false;
    }
  }

  function escalationId(escalation: EscalationItem): string {
    return escalation.escalationId ?? escalation.id ?? '';
  }

  async function acceptAssignment(escalation: EscalationItem): Promise<void> {
    const id = escalationId(escalation);
    if (!id || !mediatorToken) return;

    isSubmitting = true;
    errorMessage = '';
    successMessage = '';
    try {
      await acceptEscalation(mediatorToken, id);
      successMessage = 'Assignment accepted.';
      await loadEscalations();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to accept assignment.';
    } finally {
      isSubmitting = false;
    }
  }

  async function recordAssignmentOutcome(escalation: EscalationItem): Promise<void> {
    const id = escalationId(escalation);
    const notes = outcomeNotesById[id]?.trim();
    if (!id || !mediatorToken || !notes) {
      errorMessage = 'Outcome notes are required.';
      return;
    }

    isSubmitting = true;
    errorMessage = '';
    successMessage = '';
    try {
      await recordOutcome(mediatorToken, id, {
        outcomeType: 'DIALOGUE_HELD',
        notes,
        deescalated: true,
        followUpRequired: false,
      });
      outcomeNotesById = { ...outcomeNotesById, [id]: '' };
      successMessage = 'Outcome recorded.';
      await loadEscalations();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to record outcome.';
    } finally {
      isSubmitting = false;
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

  {#if successMessage}
    <p class={styles.success} role="status">{successMessage}</p>
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
        <p class={styles.muted}>{escalation.safetyNote ?? escalation.safety_note ?? 'Protect the source.'}</p>
        <div class={styles.inlineActions}>
          <button
            class={styles.buttonSecondary}
            type="button"
            disabled={isSubmitting}
            onclick={() => acceptAssignment(escalation)}
          >
            Accept
          </button>
        </div>
        <label class={styles.field}>
          Outcome notes
          <textarea
            value={outcomeNotesById[escalationId(escalation)] ?? ''}
            oninput={(event) => {
              outcomeNotesById = {
                ...outcomeNotesById,
                [escalationId(escalation)]: event.currentTarget.value,
              };
            }}
          ></textarea>
        </label>
        <button
          class={styles.button}
          type="button"
          disabled={isSubmitting}
          onclick={() => recordAssignmentOutcome(escalation)}
        >
          Record outcome
        </button>
      </article>
    {/each}
  </section>
</main>
