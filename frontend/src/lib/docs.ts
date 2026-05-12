import { marked } from 'marked';

type DocCategory = 'overview' | 'product' | 'engineering';

export type DocRecord = {
  id: string;
  title: string;
  category: DocCategory;
  path: string;
  summary: string;
  body: string;
  html: string;
};

const docModules = import.meta.glob('../../../docs/**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const categoryOrder: DocCategory[] = ['overview', 'product', 'engineering'];

function toTitleCase(value: string): string {
  return value
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function categoryFromPath(path: string): DocCategory {
  if (path.includes('/product/')) return 'product';
  if (path.includes('/engineering/')) return 'engineering';
  return 'overview';
}

function titleFromBody(path: string, body: string): string {
  const heading = body.match(/^#\s+(.+)$/m)?.[1]?.trim();
  if (heading) return heading;

  const fileName = path.split('/').pop()?.replace(/\.md$/, '') ?? 'document';
  return toTitleCase(fileName);
}

function summaryFromBody(body: string): string {
  const lines = body
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && !line.startsWith('- ') && !line.match(/^\d+\.\s/));

  return lines[0] ?? 'Documentation entry';
}

function normalizeLink(target: string): string {
  if (target.startsWith('http://') || target.startsWith('https://') || target.startsWith('#')) {
    return target;
  }

  const cleaned = target.replace(/^\.\//, '').replace(/^\//, '');
  return `#/docs/${cleaned.replace(/\.md$/, '')}`;
}

marked.use({
  renderer: {
    link({ href, title, tokens }) {
      const text = this.parser.parseInline(tokens);
      const safeHref = normalizeLink(href ?? '#');
      const titleAttr = title ? ` title="${title}"` : '';
      return `<a href="${safeHref}"${titleAttr}>${text}</a>`;
    },
  },
});

export const docs: DocRecord[] = Object.entries(docModules)
  .map(([filePath, body]) => {
    const normalizedPath = filePath.replace(/\\/g, '/').split('/docs/')[1];
    const pathWithoutExt = normalizedPath.replace(/\.md$/, '');

    return {
      id: pathWithoutExt,
      title: titleFromBody(normalizedPath, body),
      category: categoryFromPath(normalizedPath),
      path: normalizedPath,
      summary: summaryFromBody(body),
      body,
      html: marked.parse(body) as string,
    };
  })
  .sort((left, right) => {
    const categoryDifference = categoryOrder.indexOf(left.category) - categoryOrder.indexOf(right.category);
    if (categoryDifference !== 0) return categoryDifference;
    return left.path.localeCompare(right.path);
  });

export const docsById = new Map(docs.map((doc) => [doc.id, doc]));

export function categoryLabel(category: DocCategory): string {
  if (category === 'overview') return 'Overview';
  if (category === 'product') return 'Product';
  return 'Engineering';
}

