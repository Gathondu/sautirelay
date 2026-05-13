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
      errorMessage = error instanceof Error ? error.message : 'Unable to load verifier queue.';
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
      modalError = 'Load the verifier queue first.';
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
        modalError = error instanceof Error ? error.message : 'Unable to load report details.';
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
      modalError = 'Load the verifier queue first.';
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
      modalError = error instanceof Error ? error.message : 'Unable to load cluster details.';
    } finally {
      modalLoading = false;
    }
  }

  async function submitEscalation(): Promise<void> {
    if (selectedType !== 'cluster' || !selectedId) {
      modalError = 'Escalation is only available for a selected cluster.';
      return;
    }
    if (!verifierToken) {
      modalError = 'Missing verifier session token. Reload the verifier queue.';
      return;
    }
    if (!mediatorId.trim() || !actionBrief.trim() || !safetyNote.trim() || !followUpDueAt.trim()) {
      modalError = 'Mediator ID, action brief, safety note, and follow-up date are required.';
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
      modalSuccess = 'Cluster escalated to mediator successfully.';
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : 'Unable to escalate cluster.';
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
      modalSuccess = 'AI intake completed for this report.';
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : 'Unable to process report with AI.';
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
      modalSuccess = 'Report marked as verified.';
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : 'Unable to verify report.';
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
      modalSuccess = 'Cluster marked as verified.';
      await loadVerifierQueue();
    } catch (error) {
      modalError = error instanceof Error ? error.message : 'Unable to verify cluster.';
    } finally {
      isSubmittingDecision = false;
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
        <p class={styles.muted}>
          {report.summary ?? report.redactedText ?? report.translatedText ?? 'Report awaiting AI processing.'}
        </p>
        <button
          class={styles.button}
          type="button"
          disabled={!getReportId(report)}
          onclick={() => openReportModal(report)}
        >
          View
        </button>
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
        <button
          class={styles.button}
          type="button"
          disabled={!getClusterId(cluster)}
          onclick={() => openClusterModal(cluster)}
        >
          View
        </button>
      </article>
    {/each}
  </section>

  {#if isModalOpen}
    <div class={styles.modalOverlay}>
      <div class={styles.modalCard} role="dialog" aria-modal="true" aria-labelledby="verifier-modal-heading">
        <header class={styles.modalHeader}>
          <h2 id="verifier-modal-heading">
            {selectedType === 'report' ? 'Report detail' : selectedType === 'cluster' ? 'Cluster detail' : 'Detail'}
          </h2>
        </header>

        <div class={styles.modalBody}>
          {#if modalLoading}
            <p class={styles.muted}>Loading detail...</p>
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
              <p>{selectedReportDetail.summary ?? selectedReportDetail.aiSummary ?? 'No summary available.'}</p>
              <h3>Redacted text</h3>
              <p class={styles.muted}>{selectedReportDetail.redactedText ?? 'No redacted text available.'}</p>
              <h3>Translated text</h3>
              <p class={styles.muted}>{selectedReportDetail.translatedText ?? 'No translated text available.'}</p>
              <p class={styles.muted}>Related reports: {selectedReportDetail.relatedReportIds?.length ?? 0}</p>
              <h3>Safety warnings</h3>
              {#if (selectedReportDetail.safetyWarnings ?? []).length > 0}
                <ul>
                  {#each selectedReportDetail.safetyWarnings ?? [] as warning (warning)}
                    <li>{warning}</li>
                  {/each}
                </ul>
              {:else}
                <p class={styles.muted}>No safety warnings.</p>
              {/if}
              <div class={styles.inlineActions}>
                <button
                  class={styles.buttonSecondary}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={processSelectedReport}
                >
                  Run AI intake
                </button>
                <button
                  class={styles.button}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={verifySelectedReport}
                >
                  Mark verified
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
              <p>{selectedReportPreview.summary ?? 'No detail summary is available yet.'}</p>
              <p class={styles.muted}>
                {isAwaitingAi(selectedReportPreview)
                  ? 'This report is awaiting AI response. Please check again shortly.'
                  : 'Detailed report content is not available yet for this item.'}
              </p>
              {#if isAwaitingAi(selectedReportPreview)}
                <button
                  class={styles.button}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={processSelectedReport}
                >
                  Run AI intake
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
              <h3>Recommended mediator action</h3>
              <p class={styles.muted}>
                {selectedClusterDetail.recommendedMediatorAction ??
                  'No mediator action recommendation is available yet.'}
              </p>
              <h3>Safety warnings</h3>
              {#if (selectedClusterDetail.safetyWarnings ?? []).length > 0}
                <ul>
                  {#each selectedClusterDetail.safetyWarnings ?? [] as warning (warning)}
                    <li>{warning}</li>
                  {/each}
                </ul>
              {:else}
                <p class={styles.muted}>No safety warnings.</p>
              {/if}
              <h3>Reports in cluster ({(selectedClusterDetail.reportIds ?? []).length})</h3>
              {#if (selectedClusterDetail.reportIds ?? []).length > 0}
                <ul>
                  {#each selectedClusterDetail.reportIds ?? [] as reportId (reportId)}
                    <li>{reportId}</li>
                  {/each}
                </ul>
              {:else}
                <p class={styles.muted}>No linked reports.</p>
              {/if}

              <div class={styles.inlineActions}>
                <button
                  class={styles.buttonSecondary}
                  type="button"
                  disabled={isSubmittingDecision}
                  onclick={verifySelectedCluster}
                >
                  Mark cluster verified
                </button>
              </div>

              <h3>Escalate to mediator</h3>
              <label class={styles.field}>
                Mediator ID
                <input bind:value={mediatorId} />
              </label>
              <label class={styles.field}>
                Action brief
                <textarea bind:value={actionBrief}></textarea>
              </label>
              <label class={styles.field}>
                Safety note
                <textarea bind:value={safetyNote}></textarea>
              </label>
              <label class={styles.field}>
                Urgency
                <select bind:value={urgency}>
                  {#each urgencyOptions as urgencyOption (urgencyOption)}
                    <option value={urgencyOption}>{urgencyOption}</option>
                  {/each}
                </select>
              </label>
              <label class={styles.field}>
                Follow-up due at (ISO datetime)
                <input bind:value={followUpDueAt} placeholder="2026-05-20T12:00:00Z" />
              </label>
              <button class={styles.button} type="button" disabled={isSubmittingEscalation} onclick={submitEscalation}>
                {isSubmittingEscalation ? 'Submitting...' : 'Escalate to mediator'}
              </button>
            {/if}

            {#if selectedType === 'cluster' && !selectedClusterDetail && selectedClusterPreview}
              <div class={styles.meta}>
                <span class={styles.pill}>{selectedClusterPreview.status}</span>
                <span class={styles.pill}>
                  {selectedClusterPreview.riskLevel ?? selectedClusterPreview.risk_level ?? 'MEDIUM'}
                </span>
                <span class={styles.pill}
                  >{selectedClusterPreview.reportCount ?? selectedClusterPreview.report_count ?? 0} reports</span
                >
              </div>
              <p>{selectedClusterPreview.summary}</p>
              <p class={styles.muted}>Detailed cluster data is not available yet. You can close and retry.</p>
            {/if}

            {#if modalSuccess}
              <p class={styles.success} role="status">{modalSuccess}</p>
            {/if}
          {/if}
        </div>

        <div class={styles.modalActions}>
          <button class={styles.buttonSecondary} type="button" onclick={closeModal}>Close</button>
        </div>
      </div>
    </div>
  {/if}
</main>
