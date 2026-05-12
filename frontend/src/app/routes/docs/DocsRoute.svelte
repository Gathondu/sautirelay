<script lang="ts">
  import DocsPage from '../../../pages/docs/DocsPage.svelte';
  import type { AppRoute } from '../../../lib/router/routes';

  let { route }: { route: AppRoute } = $props();
  const docId = $derived(route.name === 'docs' ? route.docId : undefined);
</script>

<DocsPage {docId} />
