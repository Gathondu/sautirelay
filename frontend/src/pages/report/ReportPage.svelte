<script lang="ts">
  import { submitReport, type ReportCategory, type Urgency } from '../../lib/api/sautirelay';
  import * as m from '../../lib/paraglide/messages';
  import styles from './ReportPage.module.css';

  const categories: Array<{ value: ReportCategory; label: () => string }> = [
    { value: 'WATER_OR_RESOURCE_CONFLICT', label: m.category_water },
    { value: 'LAND_CONFLICT', label: m.category_land },
    { value: 'HATE_SPEECH_OR_INCITEMENT', label: m.category_hate },
    { value: 'DISPLACEMENT_RISK', label: m.category_displacement },
    { value: 'ELECTION_INTIMIDATION', label: m.category_election },
    { value: 'AID_DIVERSION', label: m.category_aid },
    { value: 'GBV_OR_PROTECTION_RISK', label: m.category_gbv },
    { value: 'NOT_SURE', label: m.category_not_sure },
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
      errorMessage = error instanceof Error ? error.message : m.report_error_submit();
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>{m.report_page_title()} | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <section class={styles.intro} aria-labelledby="report-title">
    <p class={styles.eyebrow}>{m.report_eyebrow()}</p>
    <h1 id="report-title">{m.report_title()}</h1>
    <p>{m.report_intro()}</p>
    <div class={styles.actions}>
      <a class={styles.primaryLink} href="#report-form">{m.report_cta_primary()}</a>
      <a class={styles.secondaryLink} href="/status">{m.report_cta_secondary()}</a>
    </div>
  </section>

  <section class={styles.formPanel} aria-labelledby="form-title" id="report-form">
    <div class={styles.safetyNotice}>
      <strong>{m.report_safety_title()}</strong>
      <span>{m.report_safety_body()}</span>
    </div>

    {#if confirmation}
      <div class={styles.confirmation} role="status">
        <p>{m.report_confirmation_title()}</p>
        <strong>{confirmation.trackingCode}</strong>
        <span>{confirmation.message}</span>
      </div>
    {/if}

    <form class={styles.form} onsubmit={(event) => event.preventDefault()}>
      <h2 id="form-title">{m.report_form_title()}</h2>

      <label>
        <span>{m.report_preferred_language()}</span>
        <select bind:value={language}>
          {#each languages as option (option.value)}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>

      <label>
        <span>{m.report_concern_type()}</span>
        <select bind:value={categoryHint}>
          {#each categories as option (option.value)}
            <option value={option.value}>{option.label()}</option>
          {/each}
        </select>
      </label>

      <label class={styles.fullSpan}>
        <span>{m.report_details_label()}</span>
        <textarea bind:value={text} rows="6" placeholder={m.report_details_placeholder()}></textarea>
      </label>

      <label>
        <span>{m.report_timeframe_label()}</span>
        <select bind:value={timeframe}>
          <option value="NOW">{m.time_now()}</option>
          <option value="TODAY">{m.time_today()}</option>
          <option value="WITHIN_24_HOURS">{m.time_24_hours()}</option>
          <option value="THIS_WEEK">{m.time_this_week()}</option>
          <option value="UNKNOWN">{m.time_not_sure()}</option>
        </select>
      </label>

      <label class={styles.checkLabel}>
        <input type="checkbox" bind:checked={immediateDanger} />
        <span>{m.report_immediate_danger()}</span>
      </label>

      <label>
        <span>{m.report_country_label()}</span>
        <input bind:value={country} placeholder={m.report_optional_placeholder()} />
      </label>

      <label>
        <span>{m.report_region_label()}</span>
        <input bind:value={adminLevel1} placeholder={m.report_optional_placeholder()} />
      </label>

      <label>
        <span>{m.report_area_label()}</span>
        <input bind:value={nearestArea} placeholder={m.report_area_placeholder()} />
      </label>

      <label>
        <span>{m.report_landmark_label()}</span>
        <input bind:value={landmark} placeholder={m.report_landmark_placeholder()} />
      </label>

      <label class={`${styles.checkLabel} ${styles.fullSpan}`}>
        <input type="checkbox" bind:checked={shareWithMediator} />
        <span>{m.report_share_with_mediator()}</span>
      </label>

      {#if errorMessage}
        <p class={styles.error} role="alert">{errorMessage}</p>
      {/if}

      <button class={styles.submitButton} type="button" disabled={!canSubmit} onclick={handleSubmit}>
        {isSubmitting ? m.report_submitting_button() : m.report_submit_button()}
      </button>
    </form>
  </section>
</main>
