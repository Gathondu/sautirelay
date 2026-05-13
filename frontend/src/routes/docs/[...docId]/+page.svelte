<script lang="ts">
  import DocsPage from '../../../pages/docs/DocsPage.svelte';
  import type { PageProps } from './$types';

  let { params }: PageProps = $props();
</script>

<DocsPage docId={params.docId} />
