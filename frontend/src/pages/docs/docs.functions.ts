import type { DocRecord } from '../../lib/docs';

export type DocCategory = 'overview' | 'product' | 'engineering';

export type DocGroup = {
  category: DocCategory;
  label: string;
  items: DocRecord[];
};

export function selectedDocFromId(docs: DocRecord[], docsById: Map<string, DocRecord>, docId?: string): DocRecord | undefined {
  const normalized = docId?.replace(/\.md$/, '');
  if (normalized && docsById.has(normalized)) {
    return docsById.get(normalized);
  }

  return docs[0];
}

export function createDocGroups(docs: DocRecord[], categoryLabel: (category: DocCategory) => string): DocGroup[] {
  return (['overview', 'product', 'engineering'] as DocCategory[]).map((category) => ({
    category,
    label: categoryLabel(category),
    items: docs.filter((doc) => doc.category === category),
  }));
}
