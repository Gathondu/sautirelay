<script lang="ts">
  import styles from './ReportPage.module.css';
</script>

<svelte:head>
  <title>Report | SautiRelay</title>
</svelte:head>

<main class={styles.page}>
  <section class={styles.panel} aria-labelledby="report-title">
    <p class={styles.eyebrow}>SautiRelay</p>
    <h1 id="report-title">Report workspace</h1>
    <p>
      This route is reserved for the reporting UI. The docs browser now lives under the docs route so both experiences can grow side by side.
    </p>
  </section>
</main>
