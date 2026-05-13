<script lang="ts">
  import {
    acceptEscalation,
    listEscalations,
    login,
    recordOutcome,
    type EscalationItem,
  } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
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
      errorMessage = error instanceof Error ? error.message : m.mediator_error_load();
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
      successMessage = m.mediator_assignment_accepted();
      await loadEscalations();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : m.mediator_error_accept();
    } finally {
      isSubmitting = false;
    }
  }

  async function recordAssignmentOutcome(escalation: EscalationItem): Promise<void> {
    const id = escalationId(escalation);
    const notes = outcomeNotesById[id]?.trim();
    if (!id || !mediatorToken || !notes) {
      errorMessage = m.mediator_outcome_required();
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
      successMessage = m.mediator_outcome_recorded();
      await loadEscalations();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : m.mediator_error_outcome();
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>{m.mediator_page_title()} | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>{m.mediator_heading()}</h1>
      <p>{m.mediator_intro()}</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadEscalations}>
      {isLoading ? m.mediator_loading_button() : m.mediator_load_button()}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  {#if successMessage}
    <p class={styles.success} role="status">{successMessage}</p>
  {/if}

  <section class={styles.grid} aria-label={m.mediator_assignments_label()}>
    {#each escalations as escalation (escalation.escalationId ?? escalation.id)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{escalation.status}</span>
          <span class={styles.pill}>{escalation.urgency}</span>
        </div>
        <h2>{escalation.assignedTo ?? escalation.assigned_to ?? m.mediator_assignment_fallback()}</h2>
        <p class={styles.muted}>{escalation.actionBrief ?? escalation.action_brief ?? m.mediator_action_pending()}</p>
        <p class={styles.muted}>{escalation.safetyNote ?? escalation.safety_note ?? m.mediator_safety_pending()}</p>
        <div class={styles.inlineActions}>
          <button
            class={styles.buttonSecondary}
            type="button"
            disabled={isSubmitting}
            onclick={() => acceptAssignment(escalation)}
          >
            {m.mediator_accept()}
          </button>
        </div>
        <label class={styles.field}>
          {m.mediator_outcome_notes()}
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
          {m.mediator_record_outcome()}
        </button>
      </article>
    {/each}
  </section>
</main>
