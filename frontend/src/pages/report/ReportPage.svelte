<script lang="ts">
  import { submitReport, type ReportCategory, type Urgency } from '../../lib/api/sautirelay';
  import styles from './ReportPage.module.css';

  const categories: Array<{ value: ReportCategory; label: string }> = [
    { value: 'WATER_OR_RESOURCE_CONFLICT', label: 'Water or resource conflict' },
    { value: 'LAND_CONFLICT', label: 'Land dispute' },
    { value: 'HATE_SPEECH_OR_INCITEMENT', label: 'Hate speech or incitement' },
    { value: 'DISPLACEMENT_RISK', label: 'Displacement risk' },
    { value: 'ELECTION_INTIMIDATION', label: 'Election intimidation' },
    { value: 'AID_DIVERSION', label: 'Aid diversion' },
    { value: 'GBV_OR_PROTECTION_RISK', label: 'GBV or protection risk' },
    { value: 'NOT_SURE', label: 'Other / not sure' },
  ];

  const languages = [
    { value: 'English', label: 'English' },
    { value: 'Kiswahili', label: 'Kiswahili' },
    { value: 'French', label: 'Francais' },
    { value: 'Arabic', label: 'Arabic' },
    { value: 'Portuguese', label: 'Portuguese' },
  ];

  let language = $state('English');
  let categoryHint = $state<ReportCategory>('NOT_SURE');
  let text = $state('');
  let timeframe = $state<Urgency>('UNKNOWN');
  let immediateDanger = $state(false);
  let country = $state('');
  let adminLevel1 = $state('');
  let nearestArea = $state('');
  let landmark = $state('');
  let shareWithMediator = $state(true);
  let isSubmitting = $state(false);
  let errorMessage = $state('');
  let confirmation = $state<{ trackingCode: string; message: string } | null>(null);

  const canSubmit = $derived(text.trim().length >= 10 && nearestArea.trim().length >= 2 && !isSubmitting);

  async function handleSubmit(): Promise<void> {
    if (!canSubmit) return;

    isSubmitting = true;
    errorMessage = '';
    confirmation = null;

    try {
      const response = await submitReport({
        text: text.trim(),
        language,
        channel: 'pwa',
        categoryHint,
        timeframe,
        immediateDanger,
        location: {
          country: country.trim() || undefined,
          adminLevel1: adminLevel1.trim() || undefined,
          nearestArea: nearestArea.trim(),
          landmark: landmark.trim() || undefined,
          precision: 'COARSE',
          areaDescription: nearestArea.trim(),
        },
        consent: {
          safetyNoticeAccepted: true,
          dataUseAccepted: true,
          anonymousSubmissionAccepted: true,
          shareWithMediator,
        },
      });

      confirmation = {
        trackingCode: response.trackingCode,
        message: response.message,
      };
      text = '';
      landmark = '';
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to submit report.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Report safely | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <section class={styles.intro} aria-labelledby="report-title">
    <p class={styles.eyebrow}>Anonymous by default</p>
    <h1 id="report-title">Report early signs of conflict safely.</h1>
    <p>
      Share only the safest useful details. SautiRelay stores approximate location, creates a tracking code, and routes
      reports for human review before escalation.
    </p>
    <div class={styles.actions}>
      <a class={styles.primaryLink} href="#report-form">Report a concern</a>
      <a class={styles.secondaryLink} href="/status">Check my report</a>
    </div>
  </section>

  <section class={styles.formPanel} aria-labelledby="form-title" id="report-form">
    <div class={styles.safetyNotice}>
      <strong>Your safety comes first.</strong>
      <span
        >Do not include your name, phone number, exact house, shelter, or sensitive identifying details unless it is
        necessary and safe.</span
      >
    </div>

    {#if confirmation}
      <div class={styles.confirmation} role="status">
        <p>Your report has been received safely.</p>
        <strong>{confirmation.trackingCode}</strong>
        <span>{confirmation.message}</span>
      </div>
    {/if}

    <form class={styles.form} onsubmit={(event) => event.preventDefault()}>
      <h2 id="form-title">Report a concern</h2>

      <label>
        <span>Preferred language</span>
        <select bind:value={language}>
          {#each languages as option (option.value)}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>

      <label>
        <span>Type of concern</span>
        <select bind:value={categoryHint}>
          {#each categories as option (option.value)}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>

      <label class={styles.fullSpan}>
        <span>Tell us what happened or what you heard</span>
        <textarea
          bind:value={text}
          rows="6"
          placeholder="Example: There are rumors that youth may block herders from the water point tomorrow."
        ></textarea>
      </label>

      <label>
        <span>When might this happen?</span>
        <select bind:value={timeframe}>
          <option value="NOW">Now</option>
          <option value="TODAY">Today</option>
          <option value="WITHIN_24_HOURS">Within 24 hours</option>
          <option value="THIS_WEEK">This week</option>
          <option value="UNKNOWN">Not sure</option>
        </select>
      </label>

      <label class={styles.checkLabel}>
        <input type="checkbox" bind:checked={immediateDanger} />
        <span>People may be in immediate danger</span>
      </label>

      <label>
        <span>Country</span>
        <input bind:value={country} placeholder="Optional" />
      </label>

      <label>
        <span>Region / province / state</span>
        <input bind:value={adminLevel1} placeholder="Optional" />
      </label>

      <label>
        <span>Safest useful area</span>
        <input bind:value={nearestArea} placeholder="Nearest town, camp, village, or area" />
      </label>

      <label>
        <span>Optional landmark</span>
        <input bind:value={landmark} placeholder="General landmark only" />
      </label>

      <label class={`${styles.checkLabel} ${styles.fullSpan}`}>
        <input type="checkbox" bind:checked={shareWithMediator} />
        <span>Allow verified, anonymized details to be shared with a trusted mediator</span>
      </label>

      {#if errorMessage}
        <p class={styles.error} role="alert">{errorMessage}</p>
      {/if}

      <button class={styles.submitButton} type="button" disabled={!canSubmit} onclick={handleSubmit}>
        {isSubmitting ? 'Submitting...' : 'Submit safely'}
      </button>
    </form>
  </section>
</main>
