<script lang="ts">
  import {
    escalateCluster,
    getCluster,
    getReport,
    listClusters,
    listReports,
    login,
    processReport,
    type ClusterDetail,
    type ClusterItem,
    type ReportDetail,
    type ReportItem,
    type Urgency,
    verifyCluster,
    verifyReport,
  } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
  import styles from '../operations.module.css';

  let isLoading = $state(false);
  let errorMessage = $state('');
  let reports = $state<ReportItem[]>([]);
  let clusters = $state<ClusterItem[]>([]);
  let verifierToken = $state('');

  let isModalOpen = $state(false);
  let selectedType = $state<'report' | 'cluster' | null>(null);
  let selectedId = $state('');
  let selectedReportDetail = $state<ReportDetail | null>(null);
  let selectedClusterDetail = $state<ClusterDetail | null>(null);
  let selectedReportPreview = $state<ReportItem | null>(null);
  let selectedClusterPreview = $state<ClusterItem | null>(null);
  let modalLoading = $state(false);
  let modalError = $state('');
  let modalSuccess = $state('');

  let mediatorId = $state('');
  let actionBrief = $state('');
  let safetyNote = $state('');
  let urgency = $state<Urgency>('THIS_WEEK');
  let followUpDueAt = $state('');
  let isSubmittingEscalation = $state(false);
  let isSubmittingDecision = $state(false);

  const urgencyOptions: Urgency[] = ['UNKNOWN', 'ROUTINE', 'THIS_WEEK', 'WITHIN_24_HOURS', 'IMMEDIATE'];

  function getReportId(report: ReportItem): string {
    return report.reportId ?? report.id ?? report.trackingCode ?? '';
  }

  function getClusterId(cluster: ClusterItem): string {
    return cluster.clusterId ?? cluster.id ?? '';
  }

  async function loadVerifierQueue(): Promise<void> {
    isLoading = true;
    errorMessage = '';

    try {
      const auth = await login('verifier@sautirelay.dev', 'verifier-dev-pass');
      verifierToken = auth.accessToken;
      const [reportQueue, clusterQueue] = await Promise.all([
        listReports(auth.accessToken),
        listClusters(auth.accessToken),
      ]);
      reports = reportQueue.items;
      clusters = clusterQueue.items;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : m.verifier_error_load();
    } finally {
      isLoading = false;
    }
  }

  function closeModal(): void {
    isModalOpen = false;
    selectedType = null;
    selectedId = '';
    selectedReportDetail = null;
    selectedClusterDetail = null;
    selectedReportPreview = null;
    selectedClusterPreview = null;
    modalLoading = false;
    modalError = '';
    modalSuccess = '';
    mediatorId = '';
    actionBrief = '';
    safetyNote = '';
    urgency = 'THIS_WEEK';
    followUpDueAt = '';
    isSubmittingEscalation = false;
    isSubmittingDecision = false;
  }

  function isAwaitingAi(report: ReportItem): boolean {
    return report.status === 'NEW' || report.status === 'PROCESSING';
  }

  async function openReportModal(report: ReportItem): Promise<void> {
    const reportId = getReportId(report);
    selectedReportPreview = report;

    if (!verifierToken) {
      isModalOpen = true;
      selectedType = 'report';
      selectedId = reportId;
      modalError = m.modal_load_queue_first();
      return;
    }

    isModalOpen = true;
    selectedType = 'report';
    selectedId = reportId;
    selectedReportDetail = null;
    selectedClusterDetail = null;
    modalError = '';
    modalSuccess = '';
    if (isAwaitingAi(report)) {
      return;
    }
    modalLoading = true;

    try {
      selectedReportDetail = await getReport(verifierToken, reportId);
    } catch (error) {
      if (isAwaitingAi(report)) {
        modalError = '';
      } else {
        modalError = error instanceof Error ? error.message : m.modal_error_report_detail();
      }
    } finally {
      modalLoading = false;
    }
  }

  async function openClusterModal(cluster: ClusterItem): Promise<void> {
    const clusterId = getClusterId(cluster);
    selectedClusterPreview = cluster;

    if (!verifierToken) {
      isModalOpen = true;
      selectedType = 'cluster';
      selectedId = clusterId;
      modalError = m.modal_load_queue_first();
      return;
    }

    isModalOpen = true;
    selectedType = 'cluster';
    selectedId = clusterId;
    selectedClusterDetail = null;
    selectedReportDetail = null;
    modalError = '';
    modalSuccess = '';
    modalLoading = true;

    try {
      selectedClusterDetail = await getCluster(verifierToken, clusterId);
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_error_cluster_detail();
    } finally {
      modalLoading = false;
    }
  }

  async function submitEscalation(): Promise<void> {
    if (selectedType !== 'cluster' || !selectedId) {
      modalError = m.modal_escalation_selected_cluster();
      return;
    }
    if (!verifierToken) {
      modalError = m.modal_missing_verifier_token();
      return;
    }
    if (!mediatorId.trim() || !actionBrief.trim() || !safetyNote.trim() || !followUpDueAt.trim()) {
      modalError = m.modal_escalation_required();
      return;
    }

    isSubmittingEscalation = true;
    modalError = '';
    modalSuccess = '';
    try {
      await escalateCluster(verifierToken, selectedId, {
        mediatorId: mediatorId.trim(),
        actionBrief: actionBrief.trim(),
        safetyNote: safetyNote.trim(),
        urgency,
        followUpDueAt: followUpDueAt.trim(),
      });
      modalSuccess = m.modal_cluster_escalated();
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_error_escalate();
    } finally {
      isSubmittingEscalation = false;
    }
  }

  async function processSelectedReport(): Promise<void> {
    if (selectedType !== 'report' || !selectedId || !verifierToken) return;

    isSubmittingDecision = true;
    modalError = '';
    modalSuccess = '';
    try {
      await processReport(verifierToken, selectedId);
      selectedReportDetail = await getReport(verifierToken, selectedId);
      modalSuccess = m.modal_ai_completed();
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_error_process_report();
    } finally {
      isSubmittingDecision = false;
    }
  }

  async function verifySelectedReport(): Promise<void> {
    if (selectedType !== 'report' || !selectedId || !verifierToken) return;

    isSubmittingDecision = true;
    modalError = '';
    modalSuccess = '';
    try {
      await verifyReport(verifierToken, selectedId, {
        decision: 'VERIFIED',
        notes: 'Verified through trusted local review.',
        confidence: 0.85,
      });
      selectedReportDetail = await getReport(verifierToken, selectedId);
      modalSuccess = m.modal_report_verified();
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_error_verify_report();
    } finally {
      isSubmittingDecision = false;
    }
  }

  async function verifySelectedCluster(): Promise<void> {
    if (selectedType !== 'cluster' || !selectedId || !verifierToken) return;

    isSubmittingDecision = true;
    modalError = '';
    modalSuccess = '';
    try {
      await verifyCluster(verifierToken, selectedId, {
        decision: 'VERIFIED',
        notes: 'Cluster verified through trusted local review.',
        confidence: 0.85,
      });
      selectedClusterDetail = await getCluster(verifierToken, selectedId);
      modalSuccess = m.modal_cluster_verified();
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : m.modal_error_verify_cluster();
    } finally {
      isSubmittingDecision = false;
    }
  }
</script>

<svelte:head>
  <title>{m.verifier_page_title()} | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <header class={styles.header}>
    <div>
      <h1>{m.verifier_heading()}</h1>
      <p>{m.verifier_intro()}</p>
    </div>
    <button class={styles.button} type="button" disabled={isLoading} onclick={loadVerifierQueue}>
      {isLoading ? m.verifier_loading_button() : m.verifier_load_button()}
    </button>
  </header>

  {#if errorMessage}
    <p class={styles.error} role="alert">{errorMessage}</p>
  {/if}

  <section class={styles.grid} aria-label={m.verifier_queue_label()}>
    {#each reports as report (report.reportId ?? report.id ?? report.trackingCode)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{report.status}</span>
          <span class={styles.pill}>{report.riskLevel ?? report.risk_level ?? 'MEDIUM'}</span>
        </div>
        <h2>{report.category}</h2>
        <p class={styles.muted}>
          {report.summary ?? report.redactedText ?? report.translatedText ?? m.report_awaiting_ai()}
        </p>
        <button
          class={styles.button}
          type="button"
          disabled={!getReportId(report)}
          onclick={() => openReportModal(report)}
        >
          {m.view_button()}
        </button>
      </article>
    {/each}

    {#each clusters as cluster (cluster.clusterId ?? cluster.id)}
      <article class={styles.card}>
        <div class={styles.meta}>
          <span class={styles.pill}>{cluster.status}</span>
          <span class={styles.pill}>{cluster.riskLevel ?? cluster.risk_level ?? 'MEDIUM'}</span>
          <span class={styles.pill}>{m.reports_count({ count: cluster.reportCount ?? cluster.report_count ?? 0 })}</span
          >
        </div>
        <h2>{cluster.title}</h2>
        <p class={styles.muted}>{cluster.summary}</p>
        <button
          class={styles.button}
          type="button"
          disabled={!getClusterId(cluster)}
          onclick={() => openClusterModal(cluster)}
        >
          {m.view_button()}
        </button>
      </article>
    {/each}
  </section>

  {#if isModalOpen}
    <div class={styles.modalOverlay}>
      <div class={styles.modalCard} role="dialog" aria-modal="true" aria-labelledby="verifier-modal-heading">
        <header class={styles.modalHeader}>
          <h2 id="verifier-modal-heading">
            {selectedType === 'report'
              ? m.modal_report_detail()
              : selectedType === 'cluster'
                ? m.modal_cluster_detail()
                : m.modal_detail()}
          </h2>
        </header>

        <div class={styles.modalBody}>
          {#if modalLoading}
            <p class={styles.muted}>{m.modal_loading_detail()}</p>
          {:else}
            {#if modalError}
              <p class={styles.error} role="alert">{modalError}</p>
            {/if}

            {#if selectedType === 'report' && selectedReportDetail}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedReportDetail.status}</span>
                <span class={styles.pill}>
                  {selectedReportDetail.riskLevel ?? selectedReportDetail.risk_level ?? 'MEDIUM'}
                </span>
              </div>
              <p>{selectedReportDetail.summary ?? selectedReportDetail.aiSummary ?? m.modal_no_summary()}</p>
              <h3>{m.modal_redacted_text()}</h3>
              <p class={styles.muted}>{selectedReportDetail.redactedText ?? m.modal_no_redacted_text()}</p>
              <h3>{m.modal_translated_text()}</h3>
              <p class={styles.muted}>{selectedReportDetail.translatedText ?? m.modal_no_translated_text()}</p>
              <p class={styles.muted}>
                {m.modal_related_reports({ count: selectedReportDetail.relatedReportIds?.length ?? 0 })}
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
              <div class={styles.inlineActions}>
                <button
                  class={styles.buttonSecondary}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={processSelectedReport}
                >
                  {m.modal_run_ai()}
                </button>
                <button
                  class={styles.button}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={verifySelectedReport}
                >
                  {m.modal_mark_verified()}
                </button>
              </div>
            {/if}

            {#if selectedType === 'report' && !selectedReportDetail && selectedReportPreview}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedReportPreview.status}</span>
                <span class={styles.pill}
                  >{selectedReportPreview.riskLevel ?? selectedReportPreview.risk_level ?? 'MEDIUM'}</span
                >
              </div>
              <p>{selectedReportPreview.summary ?? m.modal_no_detail_summary()}</p>
              <p class={styles.muted}>
                {isAwaitingAi(selectedReportPreview)
                  ? m.modal_awaiting_ai_detail()
                  : m.modal_report_detail_unavailable()}
              </p>
              {#if isAwaitingAi(selectedReportPreview)}
                <button
                  class={styles.button}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={processSelectedReport}
                >
                  {m.modal_run_ai()}
                </button>
              {/if}
            {/if}

            {#if selectedType === 'cluster' && selectedClusterDetail}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedClusterDetail.status}</span>
                <span class={styles.pill}>
                  {selectedClusterDetail.riskLevel ?? selectedClusterDetail.risk_level ?? 'MEDIUM'}
                </span>
              </div>
              <p>{selectedClusterDetail.summary}</p>
              <h3>{m.modal_recommended_action()}</h3>
              <p class={styles.muted}>
                {selectedClusterDetail.recommendedMediatorAction ?? m.modal_no_recommended_action()}
              </p>
              <h3>{m.modal_safety_warnings()}</h3>
              {#if (selectedClusterDetail.safetyWarnings ?? []).length > 0}
                <ul>
                  {#each selectedClusterDetail.safetyWarnings ?? [] as warning (warning)}
                    <li>{warning}</li>
                  {/each}
                </ul>
              {:else}
                <p class={styles.muted}>{m.modal_no_safety_warnings()}</p>
              {/if}
              <h3>{m.modal_reports_in_cluster({ count: (selectedClusterDetail.reportIds ?? []).length })}</h3>
              {#if (selectedClusterDetail.reportIds ?? []).length > 0}
                <ul>
                  {#each selectedClusterDetail.reportIds ?? [] as reportId (reportId)}
                    <li>{reportId}</li>
                  {/each}
                </ul>
              {:else}
                <p class={styles.muted}>{m.modal_no_linked_reports()}</p>
              {/if}

              <div class={styles.inlineActions}>
                <button
                  class={styles.buttonSecondary}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={verifySelectedCluster}
                >
                  {m.modal_mark_cluster_verified()}
                </button>
              </div>

              <h3>{m.modal_escalate_to_mediator()}</h3>
              <label class={styles.field}>
                {m.modal_mediator_id()}
                <input bind:value={mediatorId} />
              </label>
              <label class={styles.field}>
                {m.modal_action_brief()}
                <textarea bind:value={actionBrief}></textarea>
              </label>
              <label class={styles.field}>
                {m.modal_safety_note()}
                <textarea bind:value={safetyNote}></textarea>
              </label>
              <label class={styles.field}>
                {m.modal_urgency()}
                <select bind:value={urgency}>
                  {#each urgencyOptions as urgencyOption (urgencyOption)}
                    <option value={urgencyOption}>{urgencyOption}</option>
                  {/each}
                </select>
              </label>
              <label class={styles.field}>
                {m.modal_follow_up_due_at()}
                <input bind:value={followUpDueAt} placeholder={m.modal_follow_up_placeholder()} />
              </label>
              <button class={styles.button} type="button" disabled={isSubmittingEscalation} onclick={submitEscalation}>
                {isSubmittingEscalation ? m.modal_escalating_button() : m.modal_escalate_to_mediator()}
              </button>
            {/if}

            {#if selectedType === 'cluster' && !selectedClusterDetail && selectedClusterPreview}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedClusterPreview.status}</span>
                <span class={styles.pill}>
                  {selectedClusterPreview.riskLevel ?? selectedClusterPreview.risk_level ?? 'MEDIUM'}
                </span>
                <span class={styles.pill}
                  >{m.reports_count({
                    count: selectedClusterPreview.reportCount ?? selectedClusterPreview.report_count ?? 0,
                  })}</span
                >
              </div>
              <p>{selectedClusterPreview.summary}</p>
              <p class={styles.muted}>{m.modal_cluster_detail_unavailable()}</p>
            {/if}

            {#if modalSuccess}
              <p class={styles.success} role="status">{modalSuccess}</p>
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
