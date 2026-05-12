<script lang="ts">
  import AppLayout from './layout/AppLayout.svelte';
  import DocsRoute from './routes/docs/DocsRoute.svelte';
  import ReportRoute from './routes/report/ReportRoute.svelte';
  import { parseRoute } from '../lib/router/routes';

  let currentRoute = $state(parseRoute(window.location.hash));

  function syncRoute(): void {
    currentRoute = parseRoute(window.location.hash);
  }

  $effect(() => {
    window.addEventListener('hashchange', syncRoute);

    return () => {
      window.removeEventListener('hashchange', syncRoute);
    };
  });
</script>

<AppLayout {currentRoute}>
  {#if currentRoute.name === 'docs'}
    <DocsRoute route={currentRoute} />
  {:else}
    <ReportRoute />
  {/if}
</AppLayout>
