<script lang="ts">
  import { categoryLabel, docs, docsById } from '../../lib/docs';
  import { routeHref } from '../../lib/router/routes';
  import { createDocGroups, selectedDocFromId } from './docs.functions';
  import styles from './DocsPage.module.css';

  let { docId }: { docId?: string } = $props();

  const groupedDocs = createDocGroups(docs, categoryLabel);
  const selectedDoc = $derived(selectedDocFromId(docs, docsById, docId));
</script>

<svelte:head>
  <title>{selectedDoc ? `${selectedDoc.title} | SautiRelay Docs` : 'SautiRelay Docs'}</title>
</svelte:head>

{#if selectedDoc}
  <div class={styles.page}>
    <aside class={styles.sidebar}>
      <div class={styles.sidebarInner}>
        <p class={styles.eyebrow}>SautiRelay</p>
        <h1 class={styles.brand}>Documentation Browser</h1>
        <p class={styles.intro}>Browse the product and engineering docs without leaving the app.</p>

        <nav class={styles.nav} aria-label="Documentation navigation">
          {#each groupedDocs as group (group.label)}
            {#if group.items.length > 0}
              <section class={styles.group}>
                <h2 class={styles.groupTitle}>{group.label}</h2>

                {#each group.items as doc (doc.id)}
                  <a
                    class={`${styles.docLink} ${doc.id === selectedDoc.id ? styles.docLinkActive : ''}`}
                    href={routeHref({ name: 'docs', docId: doc.id })}
                    aria-current={doc.id === selectedDoc.id ? 'page' : undefined}
                  >
                    <span class={styles.docTitle}>{doc.title}</span>
                    <span class={styles.docSummary}>{doc.summary}</span>
                  </a>
                {/each}
              </section>
            {/if}
          {/each}
        </nav>
      </div>
    </aside>

    <main class={styles.content}>
      <header class={styles.header}>
        <div>
          <p class={styles.pathLabel}>{selectedDoc.path}</p>
          <h2 class={styles.title}>{selectedDoc.title}</h2>
        </div>
      </header>

      <article class={styles.article}>
        <!-- eslint-disable-next-line svelte/no-at-html-tags -->
        {@html selectedDoc.html}
      </article>
    </main>
  </div>
{/if}
