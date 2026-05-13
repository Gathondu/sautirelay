<script lang="ts">
  import AppLayout from '../app/layout/AppLayout.svelte';
  import '../styles.css';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
</script>

<AppLayout>{@render children()}</AppLayout>
