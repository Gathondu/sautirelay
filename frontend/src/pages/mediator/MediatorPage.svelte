<script lang="ts">
  import {
    acceptEscalation,
    getEscalation,
    getReport,
    listEscalations,
    login,
    recordOutcome,
    type EscalationDetail,
    type EscalationItem,
    type ReportDetail,
  } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let isSubmitting = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');
  let escalations = $state<EscalationItem[]>([]);
  let mediatorToken = $state('');

  let isModalOpen = $state(false);
  let selectedEscalation = $state<EscalationItem | null>(null);
  let selectedEscalationDetail = $state<EscalationDetail | null>(null);
  let selectedReportDetail = $state<ReportDetail | null>(null);
  let modalLoading = $state(false);
  let modalError = $state('');
  let modalSuccess = $state('');
  let outcomeNotes = $state('');

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

  function escalationId(escalation: EscalationItem | EscalationDetail | null): string {
    if (!escalation) return '';
    return escalation.escalationId ?? escalation.id ?? '';
  }

  function canAcceptStatus(status: string | undefined): boolean {
    return status === 'PENDING_ACCEPTANCE';
  }

  function closeModal(): void {
    isModalOpen = false;
    selectedEscalation = null;
    selectedEscalationDetail = null;
    selectedReportDetail = null;
    modalLoading = false;
    modalError = '';
    modalSuccess = '';
    outcomeNotes = '';
  }

  async function openAssignmentModal(escalation: EscalationItem): Promise<void> {
    selectedEscalation = escalation;
    selectedEscalationDetail = null;
    selectedReportDetail = null;
    outcomeNotes = '';
    modalError = '';
    modalSuccess = '';
    isModalOpen = true;

    const id = escalationId(escalation);
    if (!id || !mediatorToken) {
      modalError = m.modal_load_queue_first();
      return;
    }

    modalLoading = true;

    try {
      const detail = await getEscalation(mediatorToken, id);
      selectedEscalationDetail = detail;

      if (detail.reportId) {
        selectedReportDetail = await getReport(mediatorToken, detail.reportId);
      }
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_loading_detail();
    } finally {
      modalLoading = false;
    }
  }

  async function acceptAssignment(): Promise<void> {
    const id = escalationId(selectedEscalationDetail ?? selectedEscalation);
    if (!id || !mediatorToken) return;

    isSubmitting = true;
    errorMessage = '';
    successMessage = '';
    modalError = '';
    modalSuccess = '';

    try {
      const updated = await acceptEscalation(mediatorToken, id);
      selectedEscalation = updated;
      selectedEscalationDetail = selectedEscalationDetail ? { ...selectedEscalationDetail, ...updated } : null;
      modalSuccess = m.mediator_assignment_accepted();
      successMessage = m.mediator_assignment_accepted();
      await loadEscalations();
    } catch (error) {
      const message = error instanceof Error ? error.message : m.mediator_error_accept();
      modalError = message;
      errorMessage = message;
    } finally {
      isSubmitting = false;
    }
  }

  async function recordAssignmentOutcome(): Promise<void> {
    const id = escalationId(selectedEscalationDetail ?? selectedEscalation);
    const notes = outcomeNotes.trim();
    if (!id || !mediatorToken || !notes) {
      modalError = m.mediator_outcome_required();
      return;
    }

    isSubmitting = true;
    errorMessage = '';
    successMessage = '';
    modalError = '';
    modalSuccess = '';

    try {
      await recordOutcome(mediatorToken, id, {
        outcomeType: 'DIALOGUE_HELD',
        notes,
        deescalated: true,
        followUpRequired: false,
      });
      outcomeNotes = '';
      modalSuccess = m.mediator_outcome_recorded();
      successMessage = m.mediator_outcome_recorded();
      await loadEscalations();
      selectedEscalationDetail = selectedEscalationDetail
        ? { ...selectedEscalationDetail, status: 'RESOLVED' }
        : selectedEscalationDetail;
      selectedEscalation = selectedEscalation ? { ...selectedEscalation, status: 'RESOLVED' } : selectedEscalation;
    } catch (error) {
      const message = error instanceof Error ? error.message : m.mediator_error_outcome();
      modalError = message;
      errorMessage = message;
    } finally {
      isSubmitting = false;
    }
  }

  function detailValue(primary?: string | null, fallback?: string): string {
    return primary?.trim() || fallback || m.modal_no_summary();
  }

  function recommendedActions(detail: EscalationDetail | null): string[] {
    return detail?.recommendedActions ?? detail?.recommended_actions ?? [];
  }

  function fieldNotes(detail: EscalationDetail | null): string[] {
    return detail?.fieldNotes ?? detail?.field_notes ?? [];
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
          <button class={styles.buttonSecondary} type="button" onclick={() => openAssignmentModal(escalation)}>
            {m.modal_detail()}
          </button>
        </div>
      </article>
    {/each}
  </section>

  {#if isModalOpen}
    <div class={styles.modalOverlay}>
      <div class={styles.modalCard} role="dialog" aria-modal="true" aria-labelledby="mediator-modal-heading">
        <header class={styles.modalHeader}>
          <h2 id="mediator-modal-heading">{m.modal_detail()}</h2>
        </header>

        <div class={styles.modalBody}>
          {#if modalLoading}
            <p class={styles.muted}>{m.modal_loading_detail()}</p>
          {:else}
            {#if modalError}
              <p class={styles.error} role="alert">{modalError}</p>
            {/if}

            {#if selectedEscalation}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedEscalationDetail?.status ?? selectedEscalation.status}</span>
                <span class={styles.pill}>{selectedEscalationDetail?.urgency ?? selectedEscalation.urgency}</span>
              </div>

              <h3>{selectedEscalationDetail?.assignedTo ?? selectedEscalation.assignedTo ?? m.mediator_assignment_fallback()}</h3>
              <p>{detailValue(selectedEscalationDetail?.actionBrief ?? selectedEscalation.actionBrief, m.mediator_action_pending())}</p>
              <p class={styles.muted}>
                {detailValue(selectedEscalationDetail?.safetyNote ?? selectedEscalation.safetyNote, m.mediator_safety_pending())}
              </p>

              {#if selectedEscalationDetail?.approximateArea}
                <h3>Approximate area</h3>
                <p>{selectedEscalationDetail.approximateArea}</p>
              {/if}

              {#if recommendedActions(selectedEscalationDetail).length > 0}
                <h3>Recommended actions</h3>
                <ul>
                  {#each recommendedActions(selectedEscalationDetail) as action (action)}
                    <li>{action}</li>
                  {/each}
                </ul>
              {/if}

              {#if fieldNotes(selectedEscalationDetail).length > 0}
                <h3>Field notes</h3>
                <ul>
                  {#each fieldNotes(selectedEscalationDetail) as note (note)}
                    <li>{note}</li>
                  {/each}
                </ul>
              {/if}

              {#if selectedReportDetail}
                <h3>{m.modal_report_detail()}</h3>
                <p>{detailValue(selectedReportDetail.summary ?? selectedReportDetail.aiSummary)}</p>
                <h3>{m.modal_redacted_text()}</h3>
                <p class={styles.muted}>{detailValue(selectedReportDetail.redactedText, m.modal_no_redacted_text())}</p>
                <h3>{m.modal_translated_text()}</h3>
                <p class={styles.muted}>
                  {detailValue(selectedReportDetail.translatedText, m.modal_no_translated_text())}
                </p>
                <h3>{m.modal_safety_warnings()}</h3>
                {#if (selectedReportDetail.safetyWarnings ?? []).length > 0}
                  <ul>
                    {#each selectedReportDetail.safetyWarnings ?? [] as warning (warning)}
                      <li>{warning}</li>
                    {/each}
                  </ul>
                {:else}
                  <p class={styles.muted}>{m.modal_no_safety_warnings()}</p>
                {/if}
              {/if}

              <div class={styles.inlineActions}>
                <button
                  class={styles.buttonSecondary}
                  type="button"
                  disabled={isSubmitting || !canAcceptStatus(selectedEscalationDetail?.status ?? selectedEscalation.status)}
                  onclick={acceptAssignment}
                >
                  {m.mediator_accept()}
                </button>
              </div>

              <label class={styles.field}>
                {m.mediator_outcome_notes()}
                <textarea bind:value={outcomeNotes}></textarea>
              </label>

              {#if modalSuccess}
                <p class={styles.success} role="status">{modalSuccess}</p>
              {/if}

              <button class={styles.button} type="button" disabled={isSubmitting} onclick={recordAssignmentOutcome}>
                {m.mediator_record_outcome()}
              </button>
            {/if}
          {/if}
        </div>

        <div class={styles.modalActions}>
          <button class={styles.buttonSecondary} type="button" onclick={closeModal}>{m.modal_close()}</button>
        </div>
      </div>
    </div>
  {/if}
</main>
